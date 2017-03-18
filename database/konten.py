import sqlite3

import database.factory

def load_konten(sqlite_file):

    conn = sqlite3.connect(sqlite_file)
    conn.row_factory = database.factory.dict_factory
    c = conn.cursor()

    c.execute("SELECT oid, * FROM konten ORDER BY bezeichnung ASC")
    konten = c.fetchall()

    conn.close()

    return konten
