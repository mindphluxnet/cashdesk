import sqlite3

import database.factory

def load_buchungen(sqlite_file, konto_id):

    conn = sqlite3.connect(sqlite_file)
    conn.row_factory = database.factory.dict_factory
    c = conn.cursor()

    c.execute("SELECT oid, * FROM buchungen WHERE konto_id = ? ORDER BY datum ASC", [ konto_id ])
    buchungen = c.fetchall()

    conn.close()

    return buchungen
