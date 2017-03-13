import sqlite3

def setup_database(sqlite_file, dbversion):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    try:
        c.execute("CREATE TABLE dbversion (version INT)")
        c.execute("INSERT INTO dbversion (version) VALUES (?)", dbversion)
    except Exception as e:
        pass

    try:
        c.execute("CREATE TABLE artikel (artikelnummer TEXT(50), artikelbezeichnung TEXT, bestand INT(5), ekpreis REAL, vkpreis REAL)")
    except Exception as e:
        pass

    try:
        c.execute("CREATE TABLE kunden (vorname TEXT, nachname TEXT, strasse TEXT, hausnummer TEXT, plz INT(5), ort TEXT)")
    except Exception as e:
        pass

    try:
        c.execute("CREATE TABLE rechnungen (rechnungsnummer INT, kunden_id INT, rechnungsdatum TEXT, gedruckt INT(1), storniert INT(1))")
    except Exception as e:
        pass

    try:
        c.execute("CREATE TABLE rechnungspositionen (rechnungs_id INT, artikel_id INT, anzahl INT, rabatt REAL)")
    except Exception as e:
        pass

    try:
        c.execute("CREATE TABLE einstellungen (firmenname TEXT, inhaber TEXT, strasse TEXT, hausnummer TEXT, plz INT(5), ort TEXT, ustid TEXT, kleinunternehmer INT(1))")
        c.execute("INSERT INTO einstellungen (firmenname, inhaber, strasse, hausnummer, plz, ort, ustid, kleinunternehmer) VALUES ('', '', '', '', '', '', '', '')")
    except Exception as e:
        pass

    conn.commit()
    conn.close()
