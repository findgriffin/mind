CREATE TABLE stuff(
    id      INTEGER NOT NULL PRIMARY KEY CHECK (id > 0),
    body    TEXT NOT NULL,
    state   INTEGER NOT NULL CHECK (state BETWEEN -1 AND 2)
);
CREATE TABLE log(
    sn INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL CHECK (sn > 0),
    stuff INTEGER NOT NULL,
    prev_state INTEGER NOT NULL,
    FOREIGN KEY(stuff) REFERENCES stuff(id)
);
CREATE TABLE tags(
                     stuff   INTEGER NOT NULL CHECK (stuff > 0),
                     tag     TEXT NOT NULL,
                     PRIMARY KEY (stuff, tag),
                     FOREIGN KEY(stuff) REFERENCES stuff(id)
);
/* Must do this for every session */
PRAGMA foreign_keys = ON;

/* Example add operation */
BEGIN TRANSACTION;
INSERT INTO stuff   (id, body, state)   VALUES (1, 'INIT', 0);;
INSERT INTO log     (stuff, prev_state) VALUES (1, -1);
INSERT INTO tags    (stuff, tag)        VALUES (1, 'init');
COMMIT;
SELECT * FROM log;

/*
Fails foreign key constraint
 INSERT INTO tags    (stuff, tag)        VALUES (5, 'init');
 DELETE FROM stuff WHERE id = 1;

 DELETE FROM tags WHERE stuff=1; < This succeeds.

Fails check constraint:
 INSERT INTO stuff   (id, body, state) VALUES (5, 'test', -2);
 */
