import sqlite3

import database.factory

def load_briefe(sqlite_file):

    conn = sqlite3.connect(sqlite_file)
    conn.row_factory = database.factory.dict_factory
    c = conn.cursor()

    c.execute("SELECT oid, * FROM briefe ORDER BY datum DESC")
    briefe = c.fetchall()

    conn.close()

    return briefe
