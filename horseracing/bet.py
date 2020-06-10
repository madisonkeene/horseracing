import functools

from flask import (
    Blueprint, flash, g, jsonify, redirect, render_template, request, session, url_for, abort
)

from urllib.parse import unquote

from horseracing.db import get_db
from horseracing.math import resolveStake
from horseracing.auth import user_login_required
from horseracing.race import RaceState

from horseracing.math import previewCalc

bp = Blueprint('bet', __name__, url_prefix='/bet')

@bp.route('/', methods=('GET', 'POST'))
@user_login_required
def bet():
    db_conn, db_curs = get_db()
    horse_id = request.args.get('id', None)
    error = None
    db_curs.execute(
        'SELECT * FROM horse WHERE id = %s', (horse_id,)
    )
    h = db_curs.fetchone()

    db_curs.execute(
        'SELECT * FROM race WHERE id = %s', (h['race_id'],)
    )
    r = db_curs.fetchone()

    if r['open'] != RaceState.OPEN.value:
        error ="Race is closed"
        flash(error)
    elif g.user['amount'] <= 0:
        error = "You don't have the money to place this bet"
        flash(error)

    if request.method == 'POST' and error is None:
        amount = request.form['amount']
        eachway = 0
        if 'eachway' in request.form.keys() and request.form['eachway'] == 'on':
            eachway = 1
        if not amount:
            error = 'Amount is required.'

        new_wallet = g.user['amount'] - resolveStake(float(amount), eachway)
        if new_wallet < 0:
            error = "You don't have enough money for this bet"

        if error is None:
            db_curs.execute(
                'INSERT INTO bet (horse_id, race_id, horseracing_user_id, amount, each_way) VALUES (%s, %s, %s, %s, %s)',
                (horse_id, h['race_id'], g.user['id'], amount, eachway)
            )

            db_curs.execute(
                'UPDATE horseracing_user SET amount = %s WHERE id = %s', (new_wallet, g.user['id'])
            )
            db_conn.commit()

            return redirect(url_for('race.race', race_id=h['race_id']))

        flash(error)

    return render_template('bet/bet.html', horse=h)

@bp.route('/delete/<bet_id>', methods=('GET', 'POST'))
@user_login_required
def delete_bet(bet_id):
    db_conn, db_curs = get_db()

    db_curs.execute(
        'SELECT * FROM bet WHERE id = %s', (bet_id,)
    )
    bet = db_curs.fetchone()
    race_id = bet['race_id']

    if bet['horseracing_user_id'] != g.user['id']:
        abort(403)

    amount = g.user['amount'] + resolveStake(float(bet['amount']), bet['each_way'])

    db_curs.execute(
        'DELETE FROM bet WHERE id = %s', (bet['id'],)
    )
    db_curs.execute(
        'UPDATE horseracing_user SET amount = %s WHERE id = %s', (amount, g.user['id'])
    )
    db_conn.commit()

    return redirect(url_for('race.race', race_id=race_id))

@bp.route('/previewCalc', methods=('GET', 'POST'))
@user_login_required
def calculate_preview():
    stake = request.args.get('stake', 0, type=float)
    odds = request.args.get('odds', 0, type=str)

    odds = unquote(odds)

    result = previewCalc(stake, odds)

    return result