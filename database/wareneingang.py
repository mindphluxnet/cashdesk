import sqlite3

import database.factory

def load_wareneingang(sqlite_file, rechnung_id):

    conn = sqlite3.connect(sqlite_file)
    conn.row_factory = database.factory.dict_factory
    c = conn.cursor()

    c.execute("SELECT w.oid AS weid, w.*, a.oid, a.artikelbezeichnung FROM wareneingang w LEFT JOIN artikel a ON(a.oid = w.artikel_id) WHERE w.rechnung_id = ? ORDER BY w.oid ASC", [ rechnung_id ])

    wareneingang = c.fetchall()

    conn.close()

    return wareneingang

def save_position(sqlite_file, position):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("INSERT INTO wareneingang (rechnung_id, artikel_id, anzahl) VALUES (?, ?, ?)", [ position['rechnungs_id'], position['artikel_id'], position['anzahl'] ])

    conn.commit()
    conn.close()

def load_position(sqlite_file, id):

    conn = sqlite3.connect(sqlite_file)
    conn.row_factory = database.factory.dict_factory
    c = conn.cursor()

    c.execute("SELECT oid, artikel_id, anzahl FROM wareneingang WHERE oid = ?", [ id ])
    position = c.fetchone()

    conn.close()

    return position

def delete_position(sqlite_file, id):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("SELECT rechnung_id FROM wareneingang WHERE oid = ?", [ id ])
    rechnung_id = c.fetchone()

    c.execute("DELETE FROM wareneingang WHERE oid = ?", [ id ])

    conn.commit()
    conn.close()

    return rechnung_id[0]

def update_position(sqlite_file, position):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("UPDATE wareneingang SET anzahl = ?, artikel_id = ? WHERE oid = ?", [ position['anzahl'], position['artikel_id'], position['positions_id'] ])

    conn.commit()
    conn.close()

def wareneingang_verbuchen(sqlite_file, id):

    conn = sqlite3.connect(sqlite_file)
    conn.row_factory = database.factory.dict_factory
    c = conn.cursor()

    c.execute("SELECT oid, * FROM wareneingang WHERE rechnung_id = ?", [ id ])
    positionen = c.fetchall()

    for pos in positionen:
        c.execute("UPDATE artikel SET bestand = bestand + ? WHERE oid = ?", [ pos['anzahl'], pos['artikel_id'] ])
        c.execute("UPDATE wareneingang SET verbucht = 1 WHERE oid = ?", [ pos['rowid'] ])

    conn.commit()
    conn.close()
