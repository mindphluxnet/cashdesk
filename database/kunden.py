import sqlite3

import database.factory

def load_kunden(sqlite_file):

    conn = sqlite3.connect(sqlite_file)
    conn.row_factory = database.factory.dict_factory
    c = conn.cursor()

    c.execute("SELECT oid, * FROM kunden ORDER BY nachname, vorname ASC")
    kunden = c.fetchall()

    conn.close()

    return kunden

def save_kunde(sqlite_file, customer):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO kunden (vorname, nachname, strasse, hausnummer, plz, ort) VALUES (?, ?, ?, ?, ?, ?)", [ customer['vorname'], customer['nachname'], customer['strasse'], customer['hausnummer'], customer['plz'], customer['ort'] ])
    except Exception as e:
        pass

    conn.commit()
    conn.close()

    return c.lastrowid
