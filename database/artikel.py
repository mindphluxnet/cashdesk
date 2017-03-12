import sqlite3

def load_single_artikel(sqlite_file, id):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("SELECT * FROM artikel WHERE id = ?", id)
    artikel = c.fetchone()

    conn.close()

    return artikel

def load_artikel(sqlite_file):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("SELECT oid, * FROM artikel ORDER BY artikelnummer ASC")
    artikel = c.fetchall()

    conn.close()
    return artikel

def save_artikel(sqlite_file, artikel):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("INSERT INTO artikel (artikelnummer, artikelbezeichnung, ekpreis, vkpreis, bestand) VALUES (?, ?, ?, ?, ?)", [ artikel['artikelnummer'], artikel['artikelbezeichnung'], artikel['ekpreis'], artikel['vkpreis'], artikel['bestand'] ])

    conn.commit()
    conn.close()
