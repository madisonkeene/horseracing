import functools

from flask import (
    Blueprint, flash, g, jsonify, redirect, render_template, request, session, url_for, abort
)

from urllib.parse import unquote

from horseracing.db import get_db

from horseracing.auth import user_login_required

from horseracing.math import previewCalc

bp = Blueprint('bet', __name__, url_prefix='/bet')

@bp.route('/', methods=('GET', 'POST'))
@user_login_required
def bet():
    db = get_db()
    horse_id = request.args.get('id', None)

    h = db.execute(
        'SELECT * FROM horse WHERE id = ?', (horse_id,)
    ).fetchone()

    if request.method == 'POST':
        error = None
        amount = request.form['amount']
        eachway = 0
        if 'eachway' in request.form.keys() and request.form['eachway'] == 'on':
            eachway = 1
        if not amount:
            error = 'Amount is required.'

        if error is None:
            db.execute(
                'INSERT INTO bet (horse_id, race_id, user_id, amount, each_way) VALUES (?, ?, ?, ?, ?)',
                (horse_id, h['race_id'], g.user['id'], amount, eachway)
            )
            amount = g.user['amount'] - float(amount)
            db.execute(
                'UPDATE user SET amount = ? WHERE id = ?', (amount, g.user['id'])
            )
            db.commit()

            return redirect(url_for('race.race', race_id=h['race_id']))

        flash(error)

    return render_template('bet/bet.html', horse=h)

@bp.route('/delete/<bet_id>', methods=('GET', 'POST'))
@user_login_required
def delete_bet(bet_id):
    db = get_db()

    bet = db.execute(
        'SELECT * FROM bet WHERE id = ?', (bet_id,)
    ).fetchone()
    race_id = bet['race_id']

    if bet['user_id'] != g.user['id']:
        abort(403)

    db.execute(
        'DELETE FROM bet WHERE id = ?', (bet['id'],)
    )
    db.commit()

    return redirect(url_for('race.race', race_id=race_id))

@bp.route('/previewCalc', methods=('GET', 'POST'))
@user_login_required
def calculate_preview():
    stake = request.args.get('stake', 0, type=float)
    odds = request.args.get('odds', 0, type=str)

    odds = unquote(odds)

    result = previewCalc(stake, odds)

    return result