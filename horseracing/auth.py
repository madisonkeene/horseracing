from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
import functools
import sqlite3

from horseracing.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/', methods=('GET',))
def auth_index():
    return render_template('auth/auth.html')

@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        db = get_db()
        error = None

        # Check if user already exists and if so, redirect to login page.
        if not username:
            error = 'Username is required.'
        elif db.execute(
            'SELECT id FROM user WHERE username = ?', (username,)
        ).fetchone() is not None:
            error = 'User {} is already registered. Please log in.'.format(username)
            flash(error)
            return redirect(url_for('auth.login'))

        # Register user and then log them in.
        try:
            db.execute(
                'INSERT INTO user (username) VALUES (?)',
                ((username,))
            )
            db.commit()
            error = login_user(username, db)
            if error is None:
                return redirect(url_for('index'))
        except sqlite3.Error as e:
            error = 'Something went wrong: %s' % e

        flash(error)

    return render_template('auth/register.html')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        db = get_db()
        error = login_user(username, db)

        if error is None:
            return redirect(url_for('index'))
        flash(error)

    return render_template('auth/login.html')

def login_user(username, db):
    user = db.execute(
        'SELECT * FROM user WHERE username = ?', (username,)
    ).fetchone()

    if user is None:
        return 'Incorrect username.'

    session.clear()
    session['user_id'] = user['id']
    return None

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

def user_login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth_index'))

        return view(**kwargs)

    return wrapped_view

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()