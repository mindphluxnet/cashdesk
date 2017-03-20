import sqlite3

import database.factory

def load_wareneingang(sqlite_file, rechnung_id):

    conn = sqlite3.connect(sqlite_file)
    conn.row_factory = database.factory.dict_factory
    c = conn.cursor()

    c.execute("SELECT oid, * FROM wareneingang WHERE rechnung_id = ? ORDER BY oid DESC", [ rechnung_id ])
    wareneingang = c.fetchall()

    conn.close()

    return wareneingang
