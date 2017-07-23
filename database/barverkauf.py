import sqlite3
import datetime

import database.factory
import database.rechnungen
import database.konten
import database.artikel

def start_barverkauf(sqlite_file):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    now = datetime.datetime.now()

    rechnungsnummer = database.rechnungen.get_invoice_id_from_date(sqlite_file, now.strftime("%Y-%m-%d"))
    barverkaufsnummer = database.rechnungen.get_next_cash_invoice_id(sqlite_file)

    c.execute("INSERT INTO barverkauf (datum, uhrzeit, rechnungsnummer, barverkaufsnummer, gesamtrabatt, verbucht) VALUES (?, ?, ?, ?, ?, ?)", [ now.strftime("%Y-%m-%d"), now.strftime("%H:%I:%S"), rechnungsnummer, barverkaufsnummer, 0, 0 ] )

    conn.commit()
    conn.close()

    return c.lastrowid

def save_position(sqlite_file, pos):

    conn = sqlite3.connect(sqlite_file)
    conn.row_factory = database.factory.dict_factory
    c = conn.cursor()

    now = datetime.datetime.now()

    c.execute("SELECT oid, COUNT(*) as rowcount FROM barverkauf_positionen WHERE artikel_id = ? AND bon_id = ?", [ pos['pos_artikel_id'], pos['bon_id'] ])
    count = c.fetchone()

    if(count['rowcount'] == 0):
        c.execute("INSERT INTO barverkauf_positionen (datum, uhrzeit, bon_id, artikel_id, anzahl, rabatt, verbucht) VALUES (?, ?, ?, ?, ?, ?, ?)", [ now.strftime("%Y-%m-%d"), now.strftime("%H:%I:%S"), pos['bon_id'], pos['pos_artikel_id'], pos['pos_anzahl'], 0, 0 ])
    else:
        c.execute("UPDATE barverkauf_positionen SET datum = ?, uhrzeit = ?, anzahl = anzahl + ? WHERE oid = ?", [ now.strftime("%Y-%m-%d"), now.strftime("%H:%I:%S"), pos['pos_anzahl'], count['rowid'] ])

    conn.commit()
    conn.close()

def update_position(sqlite_file, pos):

    conn = sqlite3.connect(sqlite_file)
    conn.row_factory = database.factory.dict_factory
    c = conn.cursor()

    now = datetime.datetime.now()

    c.execute("UPDATE barverkauf_positionen SET datum = ?, uhrzeit = ?, anzahl = ? WHERE oid = ?", [ now.strftime("%Y-%m-%d"), now.strftime("%H:%I:%S"), pos['pa_anzahl'], pos['pa_pos_id'] ])

    conn.commit()
    conn.close()

def load_positionen(sqlite_file, bon_id):

    conn = sqlite3.connect(sqlite_file)
    conn.row_factory = database.factory.dict_factory
    c = conn.cursor()

    c.execute("SELECT oid, * FROM barverkauf_positionen WHERE bon_id = ? ORDER BY oid ASC", [ bon_id ])
    positionen = c.fetchall()

    conn.close()

    return positionen

def delete_position(sqlite_file, pos):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("DELETE FROM barverkauf_positionen WHERE oid = ?", [ pos['lo_pos_id'] ])

    conn.commit()
    conn.close()

def barverkauf_abbrechen(sqlite_file, bon_id):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("DELETE FROM barverkauf_positionen WHERE bon_id = ?", [ bon_id ])
    c.execute("DELETE FROM barverkauf WHERE oid = ?", [ bon_id ])

    conn.commit()
    conn.close()

def barverkauf_abschliessen(sqlite_file, post):

    print(post)

    conn = sqlite3.connect(sqlite_file)
    conn.row_factory = database.factory.dict_factory
    c = conn.cursor()

    kasse = database.konten.get_kasse(sqlite_file)

    c.execute("SELECT oid, * FROM barverkauf WHERE oid = ?", [ post['bon_id'] ])
    barverkauf = c.fetchone()

    c.execute("SELECT oid, * FROM barverkauf_positionen WHERE bon_id = ?", [ post['bon_id'] ])
    positionen = c.fetchall()

    c.execute("INSERT INTO rechnungen (rechnungsnummer, barverkaufsnummer, kunden_id, rechnungsdatum, zahlungsart, zahlungsstatus, gedruckt, storniert, storno_rechnungsnummer) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", [ barverkauf['rechnungsnummer'], barverkauf['barverkaufsnummer'], -1, barverkauf['datum'], post['zahlungsart'], 1, 1, 0, 0 ] )

    rechnungs_id = c.lastrowid

    gesamtbetrag = 0

    for pos in positionen:
        c.execute("INSERT INTO rechnungspositionen(rechnungs_id, artikel_id, anzahl, rabatt, storniert) VALUES (?, ?, ?, ?, ?)", [ barverkauf['rechnungsnummer'], pos['artikel_id'], pos['anzahl'], 0, 0 ])
        c.execute("UPDATE barverkauf_positionen SET verbucht = 1 WHERE oid = ?", [ pos['rowid'] ] )
        art = database.artikel.load_single_artikel(sqlite_file, pos['artikel_id'])
        gesamtbetrag += (art['vkpreis'] * pos['anzahl'])

    c.execute("UPDATE barverkauf SET verbucht = 1 WHERE oid = ?", [ post['bon_id'] ])

    c.execute("INSERT INTO buchungen (konto_id, gegenkonto_id, barverkaufsnummer, eurkonto, ausgangsrechnungs_id, eingangsrechnungs_id, betrag, datum, einaus) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)", [ kasse, 0, 111, barverkauf['barverkaufsnummer'], barverkauf['rechnungsnummer'], 0, gesamtbetrag, barverkauf['datum'], 1 ])

    conn.commit()
    conn.close()

    return { 'rechnungs_id': barverkauf['rechnungsnummer'] }
