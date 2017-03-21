import sqlite3

import database.factory

def load_konten(sqlite_file):

    conn = sqlite3.connect(sqlite_file)
    conn.row_factory = database.factory.dict_factory
    c = conn.cursor()

    c.execute("SELECT oid, * FROM konten ORDER BY -is_kasse, bezeichnung ASC")
    konten = c.fetchall()

    conn.close()

    return konten

def load_konto(sqlite_file, id):

    conn = sqlite3.connect(sqlite_file)
    conn.row_factory = database.factory.dict_factory
    c = conn.cursor()

    c.execute("SELECT oid, * FROM konten WHERE oid = ?", [ id ])
    konto = c.fetchone()

    conn.close()

    return konto

def save_konto(sqlite_file, konto):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("INSERT INTO konten (bezeichnung, iban, bic, bankname, is_kasse) VALUES(?, ?, ?, ?, ?)", [ konto['bezeichnung'], konto['iban'], konto['bic'], konto['bankname'], konto['is_kasse'] ])

    conn.commit()
    conn.close()

def update_konto(sqlite_file, konto):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("UPDATE konten SET bezeichnung = ?, iban = ?, bic = ?, bankname = ?, is_kasse = ? WHERE oid = ?", [ konto['bezeichnung'], konto['iban'], konto['bic'], konto['bankname'], konto['is_kasse'], konto['id'] ] )

    conn.commit()
    conn.close()

def delete_konto(sqlite_file, id):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("DELETE FROM konten WHERE oid = ?", id)
    c.execute("DELETE FROM buchungen WHERE konto_id = ?", id)

    conn.commit()
    conn.close()
