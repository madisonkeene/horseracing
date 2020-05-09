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
    closed = False
    db = get_db()
    if request.method == 'GET':
        r = db.execute(
            'SELECT * FROM race WHERE number = ?', (str(race_id),)
        ).fetchone()

        h = db.execute(
            'SELECT horse.id, horse.name, horse.number, horse.odds, horse.race_id, result.place FROM horse LEFT JOIN result ON result.horse_id = horse.id WHERE horse.race_id = ? ORDER BY result.place is null, result.place, horse.number ASC', (str(r['id']),)
        ).fetchall()

        b = db.execute(
            'SELECT bet.id, bet.amount, bet.each_way, bet.user_id, bet.amount_won, horse.name AS horsename, user.username FROM bet INNER JOIN user ON user.id = bet.user_id INNER JOIN horse ON horse.id = bet.horse_id WHERE bet.race_id = ? ORDER BY bet.created DESC', (str(race_id),)
        ).fetchall()

        if r['open'] == RaceState.CLOSED.value:
            closed = True

        return render_template('race/race.html', race=r, horses=h, bets=b, race_state=RaceState, race_finished=closed)
