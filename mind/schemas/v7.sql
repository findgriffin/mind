CREATE TABLE log(sn INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                 hash TEXT NOT NULL,
                 stuff EPOCH NOT NULL,
                 stamp EPOCH NOT NULL,
                 old_state PHASE NOT NULL CHECK (old_state BETWEEN 1 AND 4),
                 new_state PHASE NOT NULL CHECK (new_state BETWEEN 1 AND 4));
CREATE TABLE stuffs(id EPOCH NOT NULL,
                    body TEXT NOT NULL,
                    state PHASE NOT NULL CHECK (state BETWEEN 1 AND 4),
                    PRIMARY KEY (id));
CREATE TABLE tags(id EPOCH NOT NULL, tag TEXT NOT NULL);