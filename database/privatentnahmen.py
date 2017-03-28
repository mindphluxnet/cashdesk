import sqlite3

import database.factory

def load_privatentnahmen(sqlite_file):

    conn = sqlite3.connect(sqlite_file)
    conn.row_factory = database.factory.dict_factory
    c = conn.cursor()

    c.execute("SELECT oid, * FROM privatentnahmen ORDER BY datum DESC")
    privatentnahmen = c.fetchall()

    conn.close()

    return privatentnahmen

def save_privatentnahmen(sqlite_file, pe):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    eurkonto = 0

    if(pe['typ'] == '0'):
        eurkonto = 108 #: Sonstige Sach-, Nutzungs- und Leistungsentnahmen
    else:
        eurkonto = 164 #: Geschenke

    c.execute("INSERT INTO privatentnahmen (datum, artikel_id, anzahl, typ, eurkonto) VALUES(?, ?, ?, ?, ?)", [ pe['datum'], pe['artikel_id'], pe['anzahl'], pe['typ'], eurkonto ] )

    conn.commit()
    conn.close()
