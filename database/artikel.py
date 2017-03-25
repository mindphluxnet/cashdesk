import sqlite3

import database.factory
import database.wareneingang

def load_single_artikel(sqlite_file, id):

    conn = sqlite3.connect(sqlite_file)
    conn.row_factory = database.factory.dict_factory
    c = conn.cursor()

    c.execute("SELECT oid, * FROM artikel WHERE oid = ?", [ id ])
    artikel = c.fetchone()

    conn.close()

    return artikel

def load_artikel_by_ean(sqlite_file, ean):

    conn = sqlite3.connect(sqlite_file)
    conn.row_factory = database.factory.dict_factory
    c = conn.cursor()

    c.execute("SELECT oid, * FROM artikel WHERE ean = ?", [ ean ])
    artikel = c.fetchone()

    conn.close()

    return artikel

def load_artikel_by_wgr(sqlite_file, id):

    conn = sqlite3.connect(sqlite_file)
    conn.row_factory = database.factory.dict_factory
    c = conn.cursor()

    c.execute("SELECT oid, * FROM artikel WHERE warengruppe = ?", [ id ])
    artikel = c.fetchall()

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

    c.execute("INSERT INTO artikel (artikelnummer, artikelbezeichnung, vkpreis, bestand, ean, warengruppe) VALUES (?, ?, ?, ?, ?, ?)", [ artikel['artikelnummer'], artikel['artikelbezeichnung'], artikel['vkpreis'], artikel['bestand'], artikel['ean'], artikel['warengruppe'] ])

    conn.commit()
    conn.close()

def update_artikel(sqlite_file, artikel):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("UPDATE artikel SET artikelnummer = ?, artikelbezeichnung = ?, vkpreis = ?, bestand = ?, ean = ?, warengruppe = ? WHERE oid = ?", [ artikel['artikelnummer'], artikel['artikelbezeichnung'], artikel['vkpreis'], artikel['bestand'], artikel['ean'], artikel['warengruppe'], artikel['id'] ])

    conn.commit()
    conn.close()

def copy_artikel(sqlite_file, id):

    conn = sqlite3.connect(sqlite_file)
    conn.row_factory = database.factory.dict_factory
    c = conn.cursor()

    c.execute("SELECT * FROM artikel WHERE oid = ?", [ id ])
    artikel = c.fetchone()

    c.execute("INSERT INTO artikel (artikelnummer, artikelbezeichnung, vkpreis, bestand, ean, warengruppe) VALUES (?, ?, ?, ?, ?, ?)", [ artikel['artikelnummer'], artikel['artikelbezeichnung'], artikel['vkpreis'], 0, artikel['ean'], artikel['warengruppe'] ])

    conn.commit()
    conn.close()

    return c.lastrowid

def delete_artikel(sqlite_file, id):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("SELECT warengruppe FROM artikel WHERE oid = ?", [ id ])
    wgr = c.fetchone()

    c.execute("DELETE FROM artikel WHERE oid = ?", [ id ])

    conn.commit()
    conn.close()

    return wgr

def artikel_is_bundle(sqlite_file, id):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM bundles WHERE bundle_artikel_id = ?", [ id ])
    count = c.fetchone()

    conn.close()

    if(count[0] > 0):
        return True
    else:
        return False

def save_bundle(sqlite_file, pos):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("INSERT INTO bundles (bundle_artikel_id, artikel_id, anzahl) VALUES (?, ?, ?)", [ pos['bundle_artikel_id'], pos['artikel_id'], pos['anzahl'] ])

    conn.commit()
    conn.close()

def load_bundle(sqlite_file, id):

    conn = sqlite3.connect(sqlite_file)
    conn.row_factory = database.factory.dict_factory
    c = conn.cursor()

    c.execute("SELECT b.oid, b.*, a.artikelbezeichnung FROM bundles AS b LEFT JOIN artikel as a ON(a.oid = b.artikel_id) WHERE b.bundle_artikel_id = ?", [ id ])
    bundle = c.fetchall()

    conn.close()

    return bundle

def load_bundle_position(sqlite_file, id):

    conn = sqlite3.connect(sqlite_file)
    conn.row_factory = database.factory.dict_factory
    c = conn.cursor()

    c.execute("SELECT oid, * FROM bundles WHERE oid = ?", [ id ])
    bundle = c.fetchone()

    conn.close()

    return bundle

def update_bundle(sqlite_file, bundle):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("UPDATE bundles SET artikel_id = ?, anzahl = ? WHERE oid = ?", [ bundle['artikel_id'], bundle['anzahl'], bundle['positions_id'] ])

    conn.commit()
    conn.close()


def delete_bundle(sqlite_file, id):

    conn = sqlite3.connect(sqlite_file)
    conn.row_factory = database.factory.dict_factory
    c = conn.cursor()

    c.execute("SELECT bundle_artikel_id FROM bundles WHERE oid = ?", [ id ])
    tmp = c.fetchone()

    c.execute("DELETE FROM bundles WHERE oid = ?", [ id ])

    conn.commit()
    conn.close()

    return tmp['bundle_artikel_id']

def unbundle(sqlite_file, id):

    conn = sqlite3.connect(sqlite_file)
    conn.row_factory = database.factory.dict_factory
    c = conn.cursor()

    c.execute("SELECT oid, * FROM bundles WHERE bundle_artikel_id = ?", [ id ])
    bundle_contents = c.fetchall()

    c.execute("SELECT warengruppe FROM artikel WHERE oid = ?", [ id ])
    wgr = c.fetchone()

    for bc in bundle_contents:
        pos = { 'rechnungs_id': -1, 'ekpreis': 0, 'anzahl': bc['anzahl'], 'artikel_id': bc['artikel_id'], 'verbucht': 1 }
        database.wareneingang.save_position(sqlite_file, pos)
        c.execute("UPDATE artikel SET bestand = bestand + ? WHERE oid = ?", [ bc['anzahl'], bc['artikel_id'] ])
        c.execute("UPDATE artikel SET bestand = bestand - 1 WHERE oid = ?", [ bc['bundle_artikel_id'] ])

    conn.commit()
    conn.close()

    return wgr['warengruppe']
