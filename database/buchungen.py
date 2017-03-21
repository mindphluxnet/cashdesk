import sqlite3

import database.factory

def load_buchungen(sqlite_file, konto_id):

    conn = sqlite3.connect(sqlite_file)
    conn.row_factory = database.factory.dict_factory
    c = conn.cursor()

    c.execute("SELECT oid, * FROM buchungen WHERE konto_id = ? ORDER BY datum DESC", [ konto_id ])
    buchungen = c.fetchall()

    conn.close()

    return buchungen

def umbuchung(sqlite_file, umbuchung):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    print(umbuchung)

    if(umbuchung['betrag'] >= 0):
        einaus = 0
        einaus_gk = 1
    else:
        einaus = 1
        einaus_gk = 0

    betrag_gk = float(umbuchung['betrag'])
    betrag_gk = -betrag_gk

    c.execute("INSERT INTO buchungen (konto_id, gegenkonto_id, betrag, datum, einaus) VALUES (?, ?, ?, ?, ?)", [ umbuchung['quellkonto'], umbuchung['zielkonto'], betrag_gk, umbuchung['datum'], einaus ] )
    c.execute("INSERT INTO buchungen (konto_id, gegenkonto_id, betrag, datum, einaus) VALUES( ?, ?, ?, ?, ?)", [ umbuchung['zielkonto'], umbuchung['quellkonto'], umbuchung['betrag'], umbuchung['datum'], einaus_gk ])

    conn.commit()
    conn.close()
