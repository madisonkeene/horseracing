import json

from werkzeug.security import generate_password_hash

def loadAdminConfig(username, password, db_conn, db_curs):
    db_curs.execute(
        'INSERT INTO horseracing_admin (username, password) VALUES (%s, %s)',
        (username, generate_password_hash(password))
    )
    db_conn.commit()

def loadRaceInfo(filepath, db_conn, db_curs):
    with open(filepath) as json_file:
        data = json.load(json_file)

        for race in data["races"]:
            db_curs.execute(
                'INSERT INTO race (name, number, venue, distance, type, field) VALUES (%s, %s, %s, %s, %s, %s)',
                (race["name"], race["number"], race["venue"], race["distance"], race["type"], race["field"])
            )
            db_conn.commit()

            db_curs.execute('SELECT id FROM race WHERE number = %s', (race["number"],))
            race_key = db_curs.fetchone()['id']

            for horse in race["horses"]:
                db_curs.execute(
                    'INSERT INTO horse (name, number, odds, race_id) VALUES (%s, %s, %s, %s)',
                    (horse["name"], horse["number"], horse["odds"], race_key)
                )
                db_conn.commit()