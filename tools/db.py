import sqlite3


def startdb(dbfile: str = "./sqlite2.db") -> sqlite3.Connection:
    conn = sqlite3.connect(dbfile, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute("PRAGMA optimize;")
    conn.commit()
    cursor.close()
    return conn
