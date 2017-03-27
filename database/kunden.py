import sqlite3

import database.factory

def load_kunden(sqlite_file, archiviert = False):

    conn = sqlite3.connect(sqlite_file)
    conn.row_factory = database.factory.dict_factory
    c = conn.cursor()

    if(not archiviert):
        c.execute("SELECT oid, * FROM kunden ORDER BY nachname, vorname ASC")
    else:
        c.execute("SELECT oid, * FROM kunden WHERE archiviert = 0 ORDER BY nachname, vorname ASC")
    kunden = c.fetchall()

    conn.close()

    return kunden

def save_kunde(sqlite_file, customer):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("INSERT INTO kunden (anrede, titel, vorname, nachname, strasse, hausnummer, plz, ort, telefonnummer, telefaxnummer, mobilnummer, email, archiviert) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", [ customer['anrede'], customer['titel'], customer['vorname'], customer['nachname'], customer['strasse'], customer['hausnummer'], customer['plz'], customer['ort'], customer['telefonnummer'], customer['telefaxnummer'], customer['mobilnummer'], customer['email'], 0 ])

    conn.commit()
    conn.close()

    return c.lastrowid

def update_kunde(sqlite_file, customer):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("UPDATE kunden SET anrede = ?, titel = ?, vorname = ?, nachname = ?, strasse = ?, hausnummer = ?, plz = ?, ort = ?, telefonnummer = ?, telefaxnummer = ?, mobilnummer = ?, email = ? WHERE oid = ?", [ customer['anrede'], customer['titel'], customer['vorname'], customer['nachname'], customer['strasse'], customer['hausnummer'], customer['plz'], customer['ort'], customer['telefonnummer'], customer['telefaxnummer'], customer['mobilnummer'], customer['email'], customer['id'] ] )

    conn.commit()
    conn.close()

def load_kunde(sqlite_file, id):

    conn = sqlite3.connect(sqlite_file)
    conn.row_factory = database.factory.dict_factory
    c = conn.cursor()

    c.execute("SELECT oid, * FROM kunden WHERE oid = ?", [ id ] )
    kunde = c.fetchone()

    conn.close()

    return kunde

def archive_kunde(sqlite_file, id):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("UPDATE kunden SET archiviert = 1 WHERE oid = ?", [ id ])

    conn.commit()
    conn.close()

def restore_kunde(sqlite_file, id):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("UPDATE kunden SET archiviert = 0 WHERE oid = ?", [ id ])

    conn.commit()
    conn.close()
