import functools
import psycopg2
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
    db_conn, db_curs = get_db()

    if request.method == 'POST':
        if 'modify_race_state' in request.form.keys():
            db_curs.execute(
                'SELECT * FROM race WHERE number = %s', (request.form['race_number'],)
            )
            r = db_curs.fetchone()
            return modify_race_state(r['id'], get_race_state(request.form['race_state']), db_conn, db_curs)
        elif 'modify_user_state' in request.form.keys():
            modify_user_state(request.form['usernames'], request.form['user_actions'], db_conn, db_curs)
        else:
            return render_template('admin/failure.html', message="Something went wrong!")


    db_curs.execute(
        'SELECT * FROM race ORDER BY number'
    )
    r = db_curs.fetchall()

    db_curs.execute(
        'SELECT * FROM horseracing_user ORDER BY id'
    )
    u = db_curs.fetchall()
    return render_template('admin/admin.html', races=r, users=u)

def get_race_state(form_state):
    if form_state == "Start":
        return RaceState.OPEN
    elif form_state == "Close":
        return RaceState.CLOSED
    elif form_state == "Not yet started":
        return RaceState.NOT_YET_OPEN

def get_race_state_string(state):
    if state == RaceState.OPEN:
        return "Start"
    elif state == RaceState.CLOSED:
        return "Close"
    elif state == RaceState.NOT_YET_OPEN:
        return "Not yet started"

def modify_race_state(race_id, state, db_conn, db_curs):
    state = state.value
    try:
        db_curs.execute(
            'UPDATE race SET open = %s WHERE id = %s', (state, race_id)
        )
        db_conn.commit()
    except psycopg2.Error as e:
        return render_template('admin/failure.html', message="Failed to modify race")
    return render_template('admin/success.html', message="Race modified: %s" % get_race_state_string(state))

def modify_user_state(username, action, db_conn, db_curs):
    if action == 'Delete':
        return user_delete(db_conn, db_curs, username)
    elif action == 'Reset amount':
        return user_reset_amount(db_conn, db_curs, username)
    else:
        return render_template('admin/failure.html', message="Something went wrong!")


def user_delete(db_conn, db_curs, username):
    try:
        db_curs.execute(
            'DELETE FROM horseracing_user WHERE username = %s', (username,)
        )
        db_conn.commit()
    except psycopg2.Error as e:
        return render_template('admin/failure.html', message="Failed to modify user: %s" % e)
    return render_template('admin/success.html', message="User deleted: %s" % username)


def user_reset_amount(db_conn, db_curs, username):
    try:
        db_curs.execute(
            'UPDATE horseracing_user SET amount = %s WHERE username = %s', (10.0, username)
        )
        db_conn.commit()
    except psycopg2.Error as e:
        return render_template('admin/failure.html', message="Failed to modify user: %s" % e)
    return render_template('admin/success.html', message="User amount reset: %s" % username)

@bp.route('/addresults/<race_number>', methods=('GET','POST'))
@admin_login_required
def add_results(race_number):
    db_conn, db_curs = get_db()

    db_curs.execute(
        'SELECT * FROM race WHERE number = %s', (str(race_number),)
    )
    r = db_curs.fetchone()

    db_curs.execute(
        'SELECT * FROM horse WHERE race_id = %s ORDER BY number ASC', (r['id'],)
    )
    h = db_curs.fetchall()

    if request.method == 'POST':
        horse_numbers = {1: request.form['horse1'].split(" - ")[0],
                   2: request.form['horse2'].split(" - ")[0],
                   3: request.form['horse3'].split(" - ")[0]}

        if len(horse_numbers.values()) > len(set(horse_numbers.values())):
            return render_template('admin/failure.html', message="Failed to add results: horses not unique")

        # Register results into db.
        try:
            for place, hnum in horse_numbers.items():
                db_curs.execute(
                    'SELECT * FROM horse WHERE number = %s AND race_id = %s', (hnum, r['id'])
                )
                hse = db_curs.fetchone()
                db_curs.execute(
                    'INSERT INTO result (horse_id, race_id, place) VALUES (%s, %s, %s)',
                    (hse['id'], r['id'], str(place))
                )
            db_conn.commit()
        except psycopg2.Error as e:
            return render_template('admin/failure.html', message="Failed to add results: %s" % e)

        err = calculate_and_store_bets(r['id'])
        if err is not None:
            return err

        return render_template('admin/success.html', message="Results added")

    return render_template('admin/add_results.html', race_number=r['number'] , horses=h)

def calculate_and_store_bets(race_id):
    db_conn, db_curs = get_db()

    db_curs.execute(
        'SELECT * FROM bet WHERE race_id = %s', (race_id,)
    )
    bets = db_curs.fetchall()

    # Get the results
    db_curs.execute(
        'SELECT result.place, result.horse_id, horse.name AS horsename, horse.odds AS horseodds FROM result INNER JOIN horse ON horse.id = result.horse_id WHERE result.race_id = %s', (race_id,)
    )
    results = db_curs.fetchall()

    to_store = {}

    for bet in bets:
        # if the bets horse_id in results
        result = get_result_for_horse(bet['horse_id'], results)
        if result:
            # calculate bet + store
            # total_stake = resolveStake(bet['amount'], bet['each_way'])
            calc = resolveBetValue(result['place'],bet['amount'],result['horseodds'],bet['each_way'])
            to_store[bet['id']] = (calc, bet['horseracing_user_id'])

    try:
        for id, val in to_store.items():
            db_curs.execute(
                'UPDATE bet SET amount_won = %s WHERE id = %s', (val[0], id)
            )
            db_curs.execute(
                'SELECT horseracing_user.amount FROM horseracing_user WHERE id = %s', (val[1],)
            )
            wallet = db_curs.fetchone()

            new_wallet = wallet['amount'] + val[0]

            db_curs.execute(
                'UPDATE horseracing_user SET amount = %s WHERE id = %s', (new_wallet, val[1])
            )

        db_conn.commit()
    except psycopg2.Error as e:
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
        db_conn, db_curs = get_db()
        error = None
        db_curs.execute(
            'SELECT * FROM horseracing_admin WHERE username = %s', (username,)
        )
        admin = db_curs.fetchone()
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
        db_conn, db_curs = get_db()
        db_curs.execute(
            'SELECT * FROM horseracing_admin WHERE id = %s', (admin_id,)
        )
        g.admin = db_curs.fetchone()