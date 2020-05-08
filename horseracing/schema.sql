DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS admin;
DROP TABLE IF EXISTS horse;
DROP TABLE IF EXISTS race;
DROP TABLE IF EXISTS bet;

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  amount REAL NOT NULL DEFAULT 10.0
);

CREATE TABLE admin (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);

CREATE TABLE horse (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    number INTEGER NOT NULL,
    odds TEXT NOT NULL,
    race_id INTEGER NOT NULL,
    FOREIGN KEY (race_id) REFERENCES race (id)
);

CREATE TABLE race (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  number INTEGER NOT NULL,
  venue TEXT NOT NULL,
  distance TEXT NOT NULL,
  type TEXT NOT NULL,
  field TEXT NOT NULL
);

CREATE TABLE bet (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    horse_id INTEGER NOT NULL,
    race_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    each_way INTEGER NOT NULL,
    FOREIGN KEY (horse_id) REFERENCES horse (id),
    FOREIGN KEY (race_id) REFERENCES race (id),
    FOREIGN KEY (user_id) REFERENCES user (id)
);