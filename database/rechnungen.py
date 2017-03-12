import sqlite3

def load_rechnungen(sqlite_file):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("SELECT r.oid, r.*, k.oid, k.* FROM rechnungen r LEFT JOIN kunden k ON(k.oid = r.kunden_id) ORDER BY rechnungsnummer ASC")
    rechnungen = c.fetchall()

    return rechnungen
