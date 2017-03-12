import sqlite3

def load_kunden(sqlite_file):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("SELECT oid, * FROM kunden ORDER BY nachname, vorname ASC")
    kunden = c.fetchall()

    return kunden
