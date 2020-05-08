import json

from werkzeug.security import generate_password_hash

def loadAdminConfig(filepath, db):
    with open(filepath) as json_file:
        data = json.load(json_file)
        username = data['adminInfo']['username']
        password = data['adminInfo']['password']

        db.execute(
            'INSERT INTO admin (username, password) VALUES (?, ?)',
            (username, generate_password_hash(password))
        )
        db.commit()

def loadRaceInfo(filepath, db):
    with open(filepath) as json_file:
        data = json.load(json_file)

        for race in data["races"]:
            db.execute(
                'INSERT INTO race (name, number, venue, distance, type, field) VALUES (?, ?, ?, ?, ?, ?)',
                (race["name"], race["number"], race["venue"], race["distance"], race["type"], race["field"])
            )
            race_key = db.execute('SELECT last_insert_rowid()').lastrowid
            db.commit()

            for horse in race["horses"]:
                db.execute(
                    'INSERT INTO horse (name, number, odds, race_id) VALUES (?, ?, ?, ?)',
                    (horse["name"], horse["number"], horse["odds"], race_key)
                )
                db.commit()