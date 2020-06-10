import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from horseracing.db import get_db

from horseracing.auth import user_login_required

bp = Blueprint('leaderboard', __name__, url_prefix='/leaderboard')

@bp.route('/', methods=('GET',))
@user_login_required
def leaderboard():
    if request.method == 'GET':
        db_conn, db_curs = get_db()
        db_curs.execute(
            'SELECT * FROM horseracing_user ORDER BY amount DESC'
        )
        u = db_curs.fetchall()

    return render_template('leaderboard/leaderboard.html', users=u)