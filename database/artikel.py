import sqlite3

import database.factory

def load_single_artikel(sqlite_file, id):

    conn = sqlite3.connect(sqlite_file)
    conn.row_factory = database.factory.dict_factory
    c = conn.cursor()

    c.execute("SELECT oid, * FROM artikel WHERE oid = ?", id)
    artikel = c.fetchone()

    conn.close()

    return artikel

def load_artikel(sqlite_file):

    conn = sqlite3.connect(sqlite_file)
    conn.row_factory = database.factory.dict_factory
    c = conn.cursor()

    c.execute("SELECT oid, * FROM artikel ORDER BY artikelnummer ASC")
    artikel = c.fetchall()

    conn.close()
    return artikel

def save_artikel(sqlite_file, artikel):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("INSERT INTO artikel (artikelnummer, artikelbezeichnung, ekpreis, vkpreis, bestand, ean) VALUES (?, ?, ?, ?, ?, ?)", [ artikel['artikelnummer'], artikel['artikelbezeichnung'], artikel['ekpreis'], artikel['vkpreis'], artikel['bestand'], artikel['ean'] ])

    conn.commit()
    conn.close()

def update_artikel(sqlite_file, artikel):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("UPDATE artikel SET artikelnummer = ?, artikelbezeichnung = ?, ekpreis = ?, vkpreis = ?, bestand = ?, ean = ? WHERE oid = ?", [ artikel['artikelnummer'], artikel['artikelbezeichnung'], artikel['ekpreis'], artikel['vkpreis'], artikel['bestand'], artikel['ean'], artikel['id'] ])

    conn.commit()
    conn.close()

def delete_artikel(sqlite_file, id):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("DELETE FROM artikel WHERE oid = ?", id)

    conn.commit()
    conn.close()
