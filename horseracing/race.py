from enum import Enum
from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for

from horseracing.db import get_db
from horseracing.auth import user_login_required

# Define enum for race state
class RaceState(Enum):
    NOT_YET_OPEN = 0  # Default
    OPEN = 1
    CLOSED = 2

bp = Blueprint('race', __name__, url_prefix='/race')

@bp.route('/<int:race_id>', methods=('GET',))
@user_login_required
def race(race_id):
    db = get_db()
    if request.method == 'GET':
        r = db.execute(
            'SELECT * FROM race WHERE number = ?', (str(race_id),)
        ).fetchone()

        h = db.execute(
            'SELECT * FROM horse WHERE race_id = ? ORDER BY number ASC', (str(race_id),)
        ).fetchall()
        return render_template('race/race.html', race=r, horses=h, race_state=RaceState)
