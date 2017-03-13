import sqlite3

import database.factory

def load_rechnungen(sqlite_file):

    conn = sqlite3.connect(sqlite_file)
    conn.row_factory = database.factory.dict_factory
    c = conn.cursor()

    c.execute("SELECT r.oid, r.*, k.oid, k.* FROM rechnungen r LEFT JOIN kunden k ON(k.oid = r.kunden_id) ORDER BY rechnungsnummer ASC")
    rechnungen = c.fetchall()

    conn.close()

    return rechnungen

def load_rechnung(sqlite_file, id):

    conn = sqlite3.connect(sqlite_file)
    conn.row_factory = database.factory.dict_factory
    c = conn.cursor()

    c.execute("SELECT r.oid, r.*, k.oid, k.* FROM rechnungen r LEFT JOIN kunden k ON(k.oid = r.kunden_id) WHERE r.oid = ?", id)
    rechnung = c.fetchone()

    conn.close()

    return rechnung

def save_rechnung_step1(sqlite_file, rechnung):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("INSERT INTO rechnungen (rechnungsnummer, kunden_id, rechnungsdatum) VALUES (?, ?, ?)", [ rechnung['rechnungsnummer'], rechnung['kunden_id'], rechnung['rechnungsdatum'] ] )

    conn.commit()
    conn.close()

    return c.lastrowid

def get_next_invoice_id(sqlite_file):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("SELECT rechnungsnummer FROM rechnungen ORDER BY rechnungsnummer DESC LIMIT 1")
    last_id = c.fetchone()

    if(last_id == None):
        next_id = 1
    else:
        next_id = int(last_id[0]) + 1

    conn.close()

    return next_id
