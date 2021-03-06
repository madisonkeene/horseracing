import click
import os
import psycopg2
import psycopg2.extras
import urllib.parse
from flask import current_app, g
from flask.cli import with_appcontext

from horseracing.data_loading import loadRaceInfo, loadAdminConfig


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)

def get_db():
    uri = os.environ['DATABASE_URL']
    if 'db' not in g:
        url = urllib.parse.urlparse(uri)
        conn_string = "dbname=%s user=%s password=%s host=%s " % (url.path[1:], url.username, url.password, url.hostname)

        g.db_conn = psycopg2.connect(conn_string, sslmode='require')
        g.db_curs = g.db_conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    return g.db_conn, g.db_curs


def close_db(e=None):
    db = g.pop('db_conn', None)

    if db is not None:
        db.close()


def init_db():
    db_conn, db_curs = get_db()

    with current_app.open_resource('schema.sql') as f:
        db_curs.execute(f.read().decode('utf8'))
        db_conn.commit()

    loadRaceInfo(os.environ['HR_RACE_CONFIG_FILENAME'], db_conn, db_curs)
    loadAdminConfig(os.environ['HR_ADMIN_USER'], os.environ['HR_ADMIN_PWD'], db_conn, db_curs)


@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')