import sqlite3

def setup_database(sqlite_file):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    try:
        c.execute("CREATE TABLE artikel (artikelnummer TEXT(50), artikelbezeichnung TEXT, bestand INT(5), vkpreis REAL, ean TEXT(13), warengruppe INT)")
    except Exception as e:
        pass

    try:
        c.execute("CREATE TABLE warengruppen (bezeichnung TEXT(50))")
    except Exception as e:
        pass

    try:
        c.execute("CREATE TABLE kunden (anrede TEXT, titel TEXT, vorname TEXT, nachname TEXT, strasse TEXT, hausnummer TEXT, plz INT(5), ort TEXT, telefonnummer TEXT, mobilnummer TEXT, telefaxnummer TEXT, email TEXT)")
    except Exception as e:
        pass

    try:
        c.execute("CREATE TABLE rechnungen (rechnungsnummer INT, kunden_id INT, rechnungsdatum TEXT, zahlungsart INT(1), zahlungsstatus INT(1), gedruckt INT(1), storniert INT(1), storno_rechnungsnummer INT, UNIQUE(rechnungsnummer) ON CONFLICT REPLACE)")
    except Exception as e:
        pass

    try:
        c.execute("CREATE TABLE rechnungspositionen (rechnungs_id INT, artikel_id INT, anzahl INT, rabatt REAL, storniert INT(1))")
    except Exception as e:
        pass

    try:
        c.execute("CREATE TABLE eingangsrechnungen (rechnungsnummer TEXT, rechnungsdatum TEXT, lieferant_id INT, eurkonto INT, rechnungsbetrag REAL, bezahlt INT(1), ustsatz REAL, UNIQUE(rechnungsnummer))")
    except Exception as e:
        pass

    try:
        c.execute("CREATE TABLE wareneingang (rechnung_id INT, artikel_id INT, anzahl INT, ekpreis REAL, verbucht INT(1))")
    except Exception as e:
        pass

    try:
        c.execute("CREATE TABLE lieferanten (firmenname TEXT, strasse TEXT, hausnummer TEXT, plz INT(5), ort TEXT, telefonnummer TEXT, telefaxnummer TEXT, email TEXT)")
    except Exception as e:
        pass

    try:
        c.execute("CREATE TABLE buchungen (konto_id INT, gegenkonto_id INT, eurkonto INT, ausgangsrechnungs_id INT, eingangsrechnungs_id INT, betrag REAL, datum TEXT, einaus INT)")
    except Exception as e:
        pass

    try:
        c.execute("CREATE TABLE konten (bezeichnung TEXT(50), iban TEXT(34), bic TEXT(11), bankname TEXT(50), is_kasse INT(1))")
    except Exception as e:
        pass

    try:
        c.execute("CREATE TABLE kassenlog (event TEXT, datum TEXT, betrag REAL, artikel_id INT, anzahl INT)")
    except Exception as e:
        pass

    try:
        c.execute("CREATE TABLE bundles (bundle_artikel_id INT, artikel_id INT, anzahl INT)")
    except Exception as e:
        pass

    conn.commit()
    conn.close()

def upgrade_database(sqlite_file, dbversion):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("PRAGMA user_version")
    uv = c.fetchone()

    print(uv)

    if(uv < dbversion):
        #: upgrade database
        pass

    conn.close()
