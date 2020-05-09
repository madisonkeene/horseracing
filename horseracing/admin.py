import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from horseracing.db import get_db

bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.admin is None:
            return redirect(url_for('admin.login'))

        return view(**kwargs)

    return wrapped_view

@bp.route('/', methods=('GET',))
@admin_login_required
def admin_index():
    return render_template('admin/admin.html')

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