import sqlite3

import database.factory
import statics.konten

def load_rechnungen(sqlite_file):

    conn = sqlite3.connect(sqlite_file)
    conn.row_factory = database.factory.dict_factory
    c = conn.cursor()

    c.execute("SELECT r.oid AS rechnungs_id, r.*, k.oid AS kunden_id, k.* FROM rechnungen r LEFT JOIN kunden k ON(k.oid = r.kunden_id) ORDER BY rechnungsnummer DESC")
    rechnungen = c.fetchall()

    conn.close()

    return rechnungen

def load_rechnung(sqlite_file, id):

    conn = sqlite3.connect(sqlite_file)
    conn.row_factory = database.factory.dict_factory
    c = conn.cursor()

    c.execute("SELECT r.oid, r.*, k.oid, k.* FROM rechnungen r LEFT JOIN kunden k ON(k.oid = r.kunden_id) WHERE rechnungsnummer = ?", id)
    rechnung = c.fetchone()

    conn.close()

    return rechnung

def save_rechnung_step1(sqlite_file, rechnung):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("INSERT INTO rechnungen (rechnungsnummer, kunden_id, rechnungsdatum, zahlungsart, zahlungsstatus, gedruckt, storniert, storno_rechnungsnummer) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", [ rechnung['rechnungsnummer'], rechnung['kunden_id'], rechnung['rechnungsdatum'], rechnung['zahlungsart'], rechnung['zahlungsstatus'], 0, rechnung['storniert'], rechnung['storno_rechnungsnummer'] ] )

    conn.commit()
    conn.close()

    return rechnung['rechnungsnummer']

def save_rechnung_step2(sqlite_file, rechnung):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("INSERT INTO rechnungen (rechnungsnummer, kunden_id, rechnungsdatum, zahlungsart, zahlungsstatus) VALUES (?, ?, ?, ?, ?)", [ rechnung['rechnungsnummer'], rechnung['kunden_id'], rechnung['rechnungsdatum'], rechnung['zahlungsart'], rechnung['zahlungsstatus'] ] )

    conn.commit()
    conn.close()

    return rechnung['rechnungsnummer']


def save_position(sqlite_file, position):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("INSERT INTO rechnungspositionen (rechnungs_id, artikel_id, anzahl, rabatt, storniert) VALUES (?, ?, ?, ?, ?)", [ position['rechnungs_id'], position['artikel_id'], position['anzahl'], position['rabatt'], position['storniert'] ] )

    conn.commit()
    conn.close()

def update_position(sqlite_file, position):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("UPDATE rechnungspositionen SET artikel_id = ?, anzahl = ?, rabatt = ? WHERE oid = ?", [ position['artikel_id'], position['anzahl'], position['rabatt'], position['positions_id'] ])

    conn.commit()
    conn.close()

def delete_position(sqlite_file, position):

    conn = sqlite3.connect(sqlite_file)
    conn.row_factory = database.factory.dict_factory
    c = conn.cursor()

    c.execute("SELECT rechnungs_id FROM rechnungspositionen WHERE oid = ?", position)
    rechnungs_id = c.fetchone()

    c.execute("DELETE FROM rechnungspositionen WHERE oid = ?", position)

    conn.commit()
    conn.close()

    return rechnungs_id['rechnungs_id']

def load_positionen(sqlite_file, rechnungs_id):

    conn = sqlite3.connect(sqlite_file)
    conn.row_factory = database.factory.dict_factory
    c = conn.cursor()

    c.execute("SELECT p.oid AS positions_id, p.*, a.oid AS artikel_id, a.* FROM rechnungspositionen p LEFT JOIN artikel a ON(a.oid = p.artikel_id) WHERE rechnungs_id = ?", [ rechnungs_id ])
    positionen = c.fetchall()

    conn.close()

    return positionen

def load_position(sqlite_file, positions_id):

    conn = sqlite3.connect(sqlite_file)
    conn.row_factory = database.factory.dict_factory
    c = conn.cursor()

    c.execute("SELECT oid, * FROM rechnungspositionen WHERE oid = ?", positions_id)
    position = c.fetchone()

    conn.close()

    return position

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

def ausgangsrechnung_verbuchen(sqlite_file, buchung):

    konto_einnahmen = 111

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("UPDATE rechnungen SET zahlungsstatus = 1 WHERE rechnungsnummer = ?", buchung['rechnungsnummer'])

    rechnung = database.rechnungen.load_rechnung(sqlite_file, buchung['rechnungsnummer'])

    #: Gesamtbetrag ermitteln

    positionen = database.rechnungen.load_positionen(sqlite_file, buchung['rechnungsnummer'])

    gesamtbetrag = 0

    for pos in positionen:
        rabattpreis = pos['vkpreis'] - (pos['vkpreis'] / 100 * pos['rabatt'])
        gesamtbetrag = gesamtbetrag + (pos['anzahl'] * rabattpreis)

    if(gesamtbetrag >= 0):
        einaus = 1
    else:
        einaus = 0

    c.execute("INSERT INTO buchungen (konto_id, eurkonto, rechnungs_id, betrag, datum, einaus) VALUES (?, ?, ?, ?, ?, ?)", [ buchung['konto'], konto_einnahmen, buchung['rechnungsnummer'], gesamtbetrag, buchung['zahlungsdatum'], einaus ] )

    conn.commit()
    conn.close()

def rechnung_gedruckt(sqlite_file, id):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("UPDATE rechnungen set gedruckt = 1 WHERE rechnungsnummer = ?", id)

    conn.commit()
    conn.close()

def rechnung_stornieren(sqlite_file, rechnung):

    neue_rechnungsnummer = 0

    try:

        neue_rechnungsnummer = get_next_invoice_id(sqlite_file)

        positionen = load_positionen(sqlite_file, rechnung['rechnungsnummer'])

        for pos in positionen:
            position = { 'rechnungs_id': neue_rechnungsnummer, 'artikel_id': pos['artikel_id'], 'anzahl': pos['anzahl'], 'rabatt': pos['rabatt'], 'storniert': 1 }
            save_position(sqlite_file, position)

        neue_rechnung = { 'rechnungsnummer': neue_rechnungsnummer, 'storniert': 1, 'kunden_id': rechnung['kunden_id'], 'rechnungsdatum': rechnung['rechnungsdatum'], 'zahlungsart': rechnung['zahlungsart'], 'zahlungsstatus': 1, 'gedruckt': 0, 'storno_rechnungsnummer': rechnung['rechnungsnummer'] }

        save_rechnung_step1(sqlite_file, neue_rechnung)
    except Exception as e:
        print(e.message)

    return neue_rechnungsnummer
