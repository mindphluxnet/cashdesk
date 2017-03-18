import sqlite3

def setup_database(sqlite_file, dbversion):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    try:
        c.execute("CREATE TABLE dbversion (version INT)")
    except Exception as e:
        pass

    c.execute("INSERT OR IGNORE INTO dbversion (version) VALUES (?)", [ dbversion ])

    try:
        c.execute("CREATE TABLE artikel (artikelnummer TEXT(50), artikelbezeichnung TEXT, bestand INT(5), ekpreis REAL, vkpreis REAL)")
    except Exception as e:
        pass

    try:
        c.execute("CREATE TABLE kunden (vorname TEXT, nachname TEXT, strasse TEXT, hausnummer TEXT, plz INT(5), ort TEXT)")
    except Exception as e:
        pass

    try:
        c.execute("CREATE TABLE rechnungen (rechnungsnummer INT, kunden_id INT, rechnungsdatum TEXT, zahlungsart INT(1), zahlungsstatus INT(1), gedruckt INT(1), storniert INT(1), UNIQUE(rechnungsnummer) ON CONFLICT REPLACE)")
    except Exception as e:
        pass

    try:
        c.execute("CREATE TABLE rechnungspositionen (rechnungs_id INT, artikel_id INT, anzahl INT, rabatt REAL)")
    except Exception as e:
        pass

    try:
        c.execute("CREATE TABLE buchungen (konto_id INT, gegenkonto_id INT, eurkonto INT, rechnungs_id INT, betrag REAL, datum TEXT, einaus INT, UNIQUE(rechnungs_id) ON CONFLICT REPLACE)")
    except Exception as e:
        pass

    try:
        c.execute("CREATE TABLE konten (bezeichnung TEXT(50), iban TEXT(22), bic TEXT(8), is_kasse INT(1))")
    except Exception as e:
        pass

    conn.commit()
    conn.close()
