import sqlite3

import database.factory

def load_lieferanten(sqlite_file):

    conn = sqlite3.connect(sqlite_file)
    conn.row_factory = database.factory.dict_factory
    c = conn.cursor()

    c.execute("SELECT oid, * FROM lieferanten ORDER BY firmenname DESC")
    lieferanten = c.fetchall()

    conn.close()

    return lieferanten

def load_lieferant(sqlite_file, id):

    conn = sqlite3.connect(sqlite_file)
    conn.row_factory = database.factory.dict_factory
    c = conn.cursor()

    c.execute("SELECT oid, * FROM lieferanten WHERE oid = ?", id)
    lieferant = c.fetchone()

    conn.close()

    return lieferant

def save_lieferant(sqlite_file, lieferant):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("INSERT INTO lieferanten (firmenname, strasse, hausnummer, plz, ort, telefonnummer, telefaxnummer, email) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", [ lieferant['firmenname'], lieferant['strasse'], lieferant['hausnummer'], lieferant['plz'], lieferant['ort'], lieferant['telefonnummer'], lieferant['telefaxnummer'], lieferant['email'] ])

    conn.commit()
    conn.close()

def delete_lieferant(sqlite_file, id):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("DELETE FROM lieferanten WHERE oid = ?", id)

    conn.commit()
    conn.close()
