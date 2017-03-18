import sqlite3

import database.factory

def load_konten(sqlite_file):

    conn = sqlite3.connect(sqlite_file)
    conn.row_factory = database.factory.dict_factory
    c = conn.cursor()

    c.execute("SELECT oid, * FROM konten ORDER BY bezeichnung ASC")
    konten = c.fetchall()

    conn.close()

    return konten

def save_konto(sqlite_file, konto):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("INSERT INTO konten (bezeichnung, iban, bic, bankname, is_kasse) VALUES(?, ?, ?, ?, ?)", [ konto['bezeichnung'], konto['iban'], konto['bic'], konto['bankname'], konto['is_kasse'] ])

    conn.commit()
    conn.close()
