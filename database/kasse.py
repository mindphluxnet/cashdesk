import sqlite3
import json

import database.factory

def buchung(sqlite_file, buchung):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    result = False

    try:
        c.execute("INSERT INTO kassenlog (event, datum, betrag, artikel_id, anzahl) VALUES(?, ?, ?, ?, ?)", [ buchung['event'], buchung['datum'], buchung['betrag'], buchung['artikel_id'], buchung['anzahl'] ])
        result = True
    except Exception:
        pass

    conn.commit()
    conn.close()

    result = { 'result': result }

    return result
