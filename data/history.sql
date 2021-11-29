DROP VIEW IF EXISTS history;
CREATE TABLE history(
    open_time INTEGER NOT NULL,
    pair TEXT NOT NULL,
    close_time INTEGER NOT NULL,
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    PRIMARY KEY (open_time, pair)
);
