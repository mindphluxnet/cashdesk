import sqlite3

import database.factory

def load_warengruppen(sqlite_file):

    conn = sqlite3.connect(sqlite_file)
    conn.row_factory = database.factory.dict_factory
    c = conn.cursor()

    c.execute("SELECT oid, bezeichnung FROM warengruppen ORDER BY bezeichnung ASC")
    warengruppen = c.fetchall()

    conn.close()

    return warengruppen

def load_warengruppe(sqlite_file,id ):

    conn = sqlite3.connect(sqlite_file)
    conn.row_factory = database.factory.dict_factory
    c = conn.cursor()

    c.execute("SELECT oid, bezeichnung FROM warengruppen WHERE oid = ?", [ id ])
    warengruppe = c.fetchone()

    conn.close()

    return warengruppe

def save_warengruppe(sqlite_file, wgr):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("INSERT INTO warengruppen (bezeichnung) VALUES (?)", [ wgr['bezeichnung'] ])

    conn.commit()
    conn.close()

def update_warengruppe(sqlite_file, wgr):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("UPDATE warengruppen SET bezeichnung = ? WHERE oid = ?", [ wgr['bezeichnung'], wgr['id'] ])

    conn.commit()
    conn.close()

def delete_warengruppe(sqlite_file, id):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("DELETE FROM warengruppen WHERE oid = ?", [ id ])

    conn.commit()
    conn.close()

def get_first_wgr(sqlite_file):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("SELECT oid FROM warengruppen ORDER BY oid ASC LIMIT 1")
    wgr = c.fetchone()

    conn.close()

    return wgr[0]

def get_wgr_by_artikel(sqlite_file, id):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("SELECT warengruppe FROM artikel WHERE oid = ?", [ id ])
    wgr = c.fetchone()

    conn.close()

    return wgr[0]
