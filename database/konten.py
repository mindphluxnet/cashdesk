import sqlite3

import database.factory

def load_konten(sqlite_file, archiviert = False):

    conn = sqlite3.connect(sqlite_file)
    conn.row_factory = database.factory.dict_factory
    c = conn.cursor()

    if(not archiviert):
        c.execute("SELECT oid, * FROM konten ORDER BY -is_kasse, bezeichnung ASC")
    else:
        try:
            c.execute("SELECT oid, * FROM konten WHERE archiviert = 0 ORDER BY -is_kasse, bezeichnung ASC")
        except Exception as e:
            print(e.message)
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

    c.execute("INSERT INTO konten (bezeichnung, iban, bic, bankname, is_kasse, archiviert) VALUES(?, ?, ?, ?, ?, ?)", [ konto['bezeichnung'], konto['iban'], konto['bic'], konto['bankname'], konto['is_kasse'], 0 ])

    conn.commit()
    conn.close()

def update_konto(sqlite_file, konto):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("UPDATE konten SET bezeichnung = ?, iban = ?, bic = ?, bankname = ?, is_kasse = ? WHERE oid = ?", [ konto['bezeichnung'], konto['iban'], konto['bic'], konto['bankname'], konto['is_kasse'], konto['id'] ] )

    conn.commit()
    conn.close()

def archive_konto(sqlite_file, id):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("UPDATE konten SET archiviert = 1 WHERE oid = ?", id)

    conn.commit()
    conn.close()

def restore_konto(sqlite_file, id):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("UPDATE konten SET archiviert = 0 WHERE oid = ?", id)

    conn.commit()
    conn.close()
