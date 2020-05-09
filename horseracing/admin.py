import functools
import sqlite3
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash

from horseracing.db import get_db
from horseracing.race import RaceState
from horseracing.math import resolveBetValue, resolveStake

bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.admin is None:
            return redirect(url_for('admin.login'))

        return view(**kwargs)

    return wrapped_view

@bp.route('/', methods=('GET','POST'))
@admin_login_required
def admin_index():
    db = get_db()

    if request.method == 'POST':
        if 'modify_race_state' in request.form.keys():
            r = db.execute(
                'SELECT * FROM race WHERE number = ?', (request.form['race_number'],)
            ).fetchone()
            return modify_race_state(r['id'], get_race_state(request.form['race_state']), db)
        elif 'modify_user_state' in request.form.keys():
            modify_user_state(request.form['usernames'], request.form['user_actions'], db)
        else:
            return render_template('admin/failure.html', message="Something went wrong!")


    r = db.execute(
        'SELECT * FROM race'
    ).fetchall()

    u = db.execute(
        'SELECT * FROM user'
    ).fetchall()
    return render_template('admin/admin.html', races=r, users=u)

def get_race_state(form_state):
    if form_state == "Start":
        return RaceState.OPEN
    elif form_state == "Closed":
        return RaceState.CLOSED
    elif request.form['race_state'] == "Not yet started":
        return RaceState.NOT_YET_OPEN

def modify_race_state(race_id, state, db):
    state = state.value
    try:
        db.execute(
            'UPDATE race SET open = ? WHERE id = ?', (state, race_id)
        )
        db.commit()
    except sqlite3.Error as e:
        return render_template('admin/failure.html', message="Failed to modify race: %s" % e)
    return render_template('admin/success.html', message="Race modified: %d" % state)

def modify_user_state(username, action, db):
    if action == 'Delete':
        return user_delete(db, username)
    elif action == 'Reset amount':
        return user_reset_amount(db, username)
    else:
        return render_template('admin/failure.html', message="Something went wrong!")


def user_delete(db, username):
    try:
        db.execute(
            'DELETE FROM user WHERE username = ?', (username,)
        )
        db.commit()
    except sqlite3.Error as e:
        return render_template('admin/failure.html', message="Failed to modify user: %s" % e)
    return render_template('admin/success.html', message="User deleted: %s" % username)


def user_reset_amount(db, username):
    try:
        db.execute(
            'UPDATE user SET amount = ? WHERE username = ?', (10.0, username)
        )
        db.commit()
    except sqlite3.Error as e:
        return render_template('admin/failure.html', message="Failed to modify user: %s" % e)
    return render_template('admin/success.html', message="User amount reset: %s" % username)

@bp.route('/addresults/<race_number>', methods=('GET','POST'))
@admin_login_required
def add_results(race_number):
    db = get_db()

    r = db.execute(
        'SELECT * FROM race WHERE number = ?', (str(race_number),)
    ).fetchone()

    h = db.execute(
        'SELECT * FROM horse WHERE race_id = ? ORDER BY number ASC', (r['id'],)
    ).fetchall()

    if request.method == 'POST':
        horse_numbers = {1: request.form['horse1'].split(" - ")[0],
                   2: request.form['horse2'].split(" - ")[0],
                   3: request.form['horse3'].split(" - ")[0]}

        if len(horse_numbers.values()) > len(set(horse_numbers.values())):
            return render_template('admin/failure.html', message="Failed to add results: horses not unique")

        # Register results into db.
        try:
            for place, hnum in horse_numbers.items():
                hse = db.execute(
                    'SELECT * FROM horse WHERE number = ?', (hnum,)
                ).fetchone()
                db.execute(
                    'INSERT INTO result (horse_id, race_id, place) VALUES (?, ?, ?)',
                    (hse['id'], r['id'], str(place))
                )
            db.commit()
        except sqlite3.Error as e:
            return render_template('admin/failure.html', message="Failed to add results: %s" % e)

        err = calculate_bets(r['id'])
        if err is not None:
            return err

        return render_template('admin/success.html', message="Results added")

    return render_template('admin/add_results.html', race_number=r['number'] , horses=h)

def calculate_bets(race_id):
    db = get_db()

    bets = db.execute(
        'SELECT * FROM bet WHERE race_id = ?', (race_id,)
    ).fetchall()

    # Get the results
    results = db.execute(
        'SELECT result.place, result.horse_id, horse.name AS horsename, horse.odds AS horseodds FROM result INNER JOIN horse ON horse.id = result.horse_id WHERE result.race_id = ?', (race_id,)
    ).fetchall()

    to_store = {}

    for bet in bets:
        # if the bets horse_id in results
        result = get_result_for_horse(bet['horse_id'], results)
        if result:
            # calculate bet + store
            total_stake = resolveStake(bet['amount'], bet['each_way'])
            calc = resolveBetValue(result['place'],total_stake,result['horseodds'],bet['each_way'])
            to_store[bet['id']] = calc

    try:
        for id, val in to_store.items():
            db.execute(
                'UPDATE bet SET amount_won = ? WHERE id = ?', (val, id)
            )
        db.commit()
    except sqlite3.Error as e:
        return render_template('admin/failure.html', message="Failed to update bets: %s" % e)


def get_result_for_horse(id, results):
    for result in results:
        if result['horse_id'] == id:
            return result
    return None

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        admin = db.execute(
            'SELECT * FROM admin WHERE username = ?', (username,)
        ).fetchone()

        if admin is None:
            error = 'Incorrect username.'
        elif not check_password_hash(admin['password'], password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['admin_id'] = admin['id']
            return redirect(url_for('admin.admin_index'))

        flash(error)

    return render_template('admin/login.html')

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@bp.before_app_request
def load_logged_in_admin():
    admin_id = session.get('admin_id')

    if admin_id is None:
        g.admin = None
    else:
        g.admin = get_db().execute(
            'SELECT * FROM admin WHERE id = ?', (admin_id,)
        ).fetchone()