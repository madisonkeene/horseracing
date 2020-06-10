import click
import psycopg2
import psycopg2.extras
from flask import current_app, g
from flask.cli import with_appcontext

from horseracing.data_loading import loadRaceInfo, loadAdminConfig

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)

def get_db():
    if 'db' not in g:
        g.db_conn = psycopg2.connect("dbname=horseracing_dev")
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

    loadRaceInfo("config/racenight.json", db_conn, db_curs)
    loadAdminConfig("config/config.example.json", db_conn, db_curs)


@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')