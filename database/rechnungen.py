import sqlite3

import database.factory
import statics.konten
import database.wareneingang
import os
import timestring
from datetime import datetime
from locale import *

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

    c.execute("SELECT r.oid, r.*, k.oid, k.* FROM rechnungen r LEFT JOIN kunden k ON(k.oid = r.kunden_id) WHERE rechnungsnummer = ?", [ id ])
    rechnung = c.fetchone()

    conn.close()

    return rechnung

def load_barrechnung(sqlite_file, id):

    conn = sqlite3.connect(sqlite_file)
    conn.row_factory = database.factory.dict_factory
    c = conn.cursor()

    c.execute("SELECT oid, * FROM rechnungen WHERE rechnungsnummer = ?", [ id ])
    rechnung = c.fetchone()

    conn.close()

    return rechnung



def save_rechnung(sqlite_file, rechnung):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()


    try:
        rechnungsnummer = database.rechnungen.get_invoice_id_from_date(sqlite_file, rechnung['rechnungsdatum'])
        c.execute("INSERT INTO rechnungen (rechnungsnummer, barverkaufsnummer, kunden_id, rechnungsdatum, zahlungsart, zahlungsstatus, gedruckt, storniert, storno_rechnungsnummer) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", [ rechnungsnummer, 0, rechnung['kunden_id'], rechnung['rechnungsdatum'], rechnung['zahlungsart'], rechnung['zahlungsstatus'], 0, rechnung['storniert'], rechnung['storno_rechnungsnummer'] ] )
    except Exception as e:
        print(e.message)

    conn.commit()
    conn.close()

    return rechnungsnummer

def update_rechnung(sqlite_file, rechnung):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("UPDATE rechnungen SET kunden_id = ?, rechnungsdatum = ?, zahlungsart = ?, zahlungsstatus = ? WHERE rechnungsnummer = ?", [ rechnung['kunden_id'], rechnung['rechnungsdatum'], rechnung['zahlungsart'], rechnung['zahlungsstatus'], rechnung['rechnungsnummer'] ])

    conn.commit()
    conn.close()

    return rechnung['rechnungsnummer']


def save_position(sqlite_file, position):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    try:
        rabatt = atof(position['rabatt'])
    except Exception:
        rabatt = 0

    c.execute("INSERT INTO rechnungspositionen (rechnungs_id, artikel_id, anzahl, rabatt, storniert) VALUES (?, ?, ?, ?, ?)", [ position['rechnungs_id'], position['artikel_id'], position['anzahl'], rabatt, position['storniert'] ] )

    conn.commit()
    conn.close()

def update_position(sqlite_file, position):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("UPDATE rechnungspositionen SET artikel_id = ?, anzahl = ?, rabatt = ? WHERE oid = ?", [ position['artikel_id'], position['anzahl'], atof(position['rabatt']), position['positions_id'] ])

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

    c.execute("SELECT p.oid AS positions_id, p.*, a.oid AS artikel_id, a.* FROM rechnungspositionen p LEFT JOIN artikel a ON(a.oid = p.artikel_id) WHERE rechnungs_id = ? ORDER BY p.oid ASC", [ rechnungs_id ])
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

def get_invoice_id_from_date(sqlite_file, date):

    conn = sqlite3.connect(sqlite_file)
    conn.row_factory = database.factory.dict_factory
    c = conn.cursor()

    datum = timestring.Date(date).date
    datum = datetime.strftime(datum, '%Y%m%d')

    datum = datum + "00"

    tmp = int(datum)

    ar = 1

    while ar == 1:
        tmp = tmp + 1
        c.execute("SELECT COUNT(*) as c FROM rechnungen WHERE rechnungsnummer = ?", [ tmp ])
        count = c.fetchone()
        ar = count['c']

    return tmp

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

def get_next_cash_invoice_id(sqlite_file):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("SELECT barverkaufsnummer FROM rechnungen ORDER BY barverkaufsnummer DESC LIMIT 1")
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

    c.execute("UPDATE rechnungen SET zahlungsstatus = 1 WHERE rechnungsnummer = ?", [ buchung['rechnungsnummer'] ] )

    rechnung = database.rechnungen.load_rechnung(sqlite_file, buchung['rechnungsnummer'])

    #: Gesamtbetrag ermitteln

    positionen = database.rechnungen.load_positionen(sqlite_file, buchung['rechnungsnummer'])

    gesamtbetrag = 0

    for pos in positionen:
        rabattpreis = pos['vkpreis'] - (pos['vkpreis'] / 100 * pos['rabatt'])
        gesamtbetrag = gesamtbetrag + (pos['anzahl'] * rabattpreis)

    if(rechnung['storno_rechnungsnummer'] != 0 and rechnung['storno_rechnungsnummer'] != None):
        gesamtbetrag = -gesamtbetrag

    if(gesamtbetrag >= 0):
        einaus = 1
    else:
        einaus = 0

    c.execute("INSERT INTO buchungen (konto_id, eurkonto, ausgangsrechnungs_id, betrag, datum, einaus) VALUES (?, ?, ?, ?, ?, ?)", [ buchung['konto'], konto_einnahmen, buchung['rechnungsnummer'], gesamtbetrag, buchung['zahlungsdatum'], einaus ] )

    conn.commit()
    conn.close()

def get_buchung(sqlite_file, rechnungs_id):

    conn = sqlite3.connect(sqlite_file)
    conn.row_factory = database.factory.dict_factory
    c = conn.cursor()

    c.execute("SELECT * FROM buchungen WHERE ausgangsrechnungs_id = ?", [ rechnungs_id ])
    buchung = c.fetchone()

    conn.close()

    return buchung

def rechnung_gedruckt(sqlite_file, id):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("UPDATE rechnungen set gedruckt = 1 WHERE rechnungsnummer = ?", [ id ])

    conn.commit()
    conn.close()

def rechnung_storniert(sqlite_file, id):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("UPDATE rechnungen SET storniert = 1 WHERE rechnungsnummer = ?", [ id ])

    conn.commit()
    conn.close()

def rechnung_stornieren(sqlite_file, rechnung):

    neue_rechnungsnummer = 0

    neue_rechnungsnummer = get_next_invoice_id(sqlite_file)

    positionen = load_positionen(sqlite_file, rechnung['rechnungsnummer'])

    for pos in positionen:
        position = { 'rechnungs_id': neue_rechnungsnummer, 'artikel_id': pos['artikel_id'], 'anzahl': pos['anzahl'], 'rabatt': pos['rabatt'], 'storniert': 1 }
        save_position(sqlite_file, position)

    neue_rechnung = { 'rechnungsnummer': neue_rechnungsnummer, 'storniert': 0, 'kunden_id': rechnung['kunden_id'], 'rechnungsdatum': rechnung['rechnungsdatum'], 'zahlungsart': rechnung['zahlungsart'], 'zahlungsstatus': 1, 'gedruckt': 0, 'storno_rechnungsnummer': rechnung['rechnungsnummer'] }

    save_rechnung(sqlite_file, neue_rechnung)
    update_rechnung(sqlite_file, neue_rechnung)

    rechnung_storniert(sqlite_file, rechnung['rechnungsnummer'])

    org_buchung = get_buchung(sqlite_file, rechnung['rechnungsnummer'])

    buchung = { 'rechnungsnummer': neue_rechnungsnummer, 'zahlungsdatum': neue_rechnung['rechnungsdatum'], 'konto': org_buchung['konto_id'] }

    ausgangsrechnung_verbuchen(sqlite_file, buchung)

    return neue_rechnungsnummer

def delete_rechnung(sqlite_file, id):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("DELETE FROM rechnungspositionen WHERE rechnungs_id = ?", [ id ])
    c.execute("DELETE FROM rechnungen WHERE rechnungsnummer = ?", [ id ])

    conn.commit()
    conn.close()

def load_eingangsrechnungen(sqlite_file):

    conn = sqlite3.connect(sqlite_file)
    conn.row_factory = database.factory.dict_factory
    c = conn.cursor()

    c.execute("SELECT oid, * FROM eingangsrechnungen ORDER BY rechnungsdatum DESC")
    rechnungen = c.fetchall()

    conn.close()

    return rechnungen

def load_eingangsrechnung(sqlite_file, id):

    conn = sqlite3.connect(sqlite_file)
    conn.row_factory = database.factory.dict_factory
    c = conn.cursor()

    c.execute("SELECT oid, * FROM eingangsrechnungen WHERE oid = ?", [ id ])
    rechnung = c.fetchone()

    conn.close()

    return rechnung

def save_eingangsrechnung(sqlite_file, rechnung):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("INSERT INTO eingangsrechnungen (rechnungsnummer, rechnungsdatum, lieferant_id, eurkonto, rechnungsbetrag, bezahlt, ustsatz) VALUES (?, ?, ?, ?, ?, ?, ?)", [ rechnung['rechnungsnummer'], rechnung['rechnungsdatum'], rechnung['lieferant_id'], rechnung['eurkonto'], atof(rechnung['rechnungsbetrag']), 0, rechnung['ustsatz'] ])

    conn.commit()
    conn.close()

    return c.lastrowid

def update_eingangsrechnung(sqlite_file, rechnung):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("UPDATE eingangsrechnungen SET rechnungsnummer = ?, rechnungsdatum = ?, lieferant_id = ?, eurkonto = ?, rechnungsbetrag = ?, ustsatz = ? WHERE oid = ?", [ rechnung['rechnungsnummer'], rechnung['rechnungsdatum'], rechnung['lieferant_id'], rechnung['eurkonto'], atof(rechnung['rechnungsbetrag']), rechnung['ustsatz'], rechnung['rechnungs_id'] ])

    conn.commit()
    conn.close()

    return rechnung['rechnungs_id']

def delete_eingangsrechnung(sqlite_file, id):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("DELETE FROM eingangsrechnungen WHERE oid = ?", [ id ])

    positionen = database.wareneingang.load_wareneingang(sqlite_file, id)

    #: Wareneingang rueckgaengig machen
    for pos in positionen:
        c.execute("UPDATE artikel SET bestand = bestand - ? WHERE oid = ?", [ pos['anzahl'], pos['artikel_id']])
        c.execute("DELETE FROM wareneingang WHERE oid = ?", [ pos['rowid'] ])

    #: PDF loeschen wenn vorhanden

    try:
        os.remove('/dokumente/eingangsrechnungen/eingangsrechnung-' + str(id) + '.pdf')
    except OSError:
        pass

    conn.commit()
    conn.close()

def eingangsrechnung_bezahlt(sqlite_file, rechnung):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    rb = rechnung['rechnungsbetrag']
    rb = float(rb)
    rb = -rb

    c.execute("UPDATE eingangsrechnungen SET bezahlt = 1 WHERE oid = ?", [ rechnung['rechnungsnummer'] ])

    try:
        c.execute("INSERT INTO buchungen (konto_id, eurkonto, eingangsrechnungs_id, betrag, datum, einaus) VALUES (?, ?, ?, ?, ?, ?)", [ rechnung['konto'], rechnung['eurkonto'], rechnung['rechnungsnummer'], rb, rechnung['zahlungsdatum'], 0 ] )
    except Exception as e:
        print(e.message)

    conn.commit()
    conn.close()
