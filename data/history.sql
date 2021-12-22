DROP TABLE IF EXISTS history;
DROP TABLE IF EXISTS history_index;
CREATE TABLE history_index(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name TEXT NOT NULL,
    UNIQUE(file_name)
);
CREATE TABLE history(
    open_time INTEGER NOT NULL,
    pair TEXT NOT NULL,
    close_time INTEGER NOT NULL,
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    file_id INTEGER NOT NULL,
    PRIMARY KEY (open_time, pair)
    FOREIGN KEY(file_id) REFERENCES history_index(id)
);
