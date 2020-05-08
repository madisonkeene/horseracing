import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from horseracing.db import get_db

from horseracing.auth import user_login_required

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
            # TODO(madisonfl): Update the redirect
            return redirect(url_for('leaderboard'))

        flash(error)

    return render_template('bet/bet.html', horse=h)