from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
import functools
import psycopg2

from horseracing.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/', methods=('GET',))
def auth_index():
    return render_template('auth/auth.html')

@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        db_conn, db_curs = get_db()
        error = None

        # Check if user already exists and if so, redirect to login page.
        if not username:
            error = 'Username is required.'

        db_curs.execute('SELECT id FROM horseracing_user WHERE username = %s', (username,))
        exists = db_curs.fetchone()
        if exists is not None:
            error = 'User {} is already registered. Please log in.'.format(username)

        if error is not None:
            flash(error)
            return redirect(url_for('auth.login'))

        # Register user and then log them in.
        try:
            db_curs.execute('INSERT INTO horseracing_user (username) VALUES (%s)',((username,)))
            db_conn.commit()
            error = login_user(username, db_curs)
            if error is None:
                return redirect(url_for('index'))
        except psycopg2.Error as e:
            db_conn.rollback()
            error = 'Something went wrong when doing database transactions: %s', e

        flash(error)

    return render_template('auth/register.html')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        db_conn, db_curs = get_db()
        error = login_user(username, db_curs)

        if error is None:
            return redirect(url_for('index'))
        flash(error)

    return render_template('auth/login.html')

def login_user(username, db_curs):
    db_curs.execute('SELECT id FROM horseracing_user WHERE username = %s', (username,))
    user = db_curs.fetchone()

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
        db_conn, db_curs = get_db()
        db_curs.execute('SELECT * FROM horseracing_user WHERE id = %s', (user_id,))
        g.user = db_curs.fetchone()