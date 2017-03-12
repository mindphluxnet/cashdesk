import sqlite3

def setup_database(sqlite_file):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    try:
        c.execute("CREATE TABLE artikel (artikelnummer TEXT(50) PRIMARY KEY, artikelbezeichnung TEXT, netto_ek REAL, vk_preis REAL, steuertyp INT, UNIQUE artikelnummer)")
    except Exception as e:
        pass

    try:
        c.execute("CREATE TABLE kunden (kundennummer INT, vorname TEXT, nachname TEXT, strasse TEXT, hausnummer TEXT, plz INT(5), ort TEXT, UNIQUE kundennummer)")
    except Exception as e:
        pass

    try:
        c.execute("CREATE TABLE rechnungen (rechnungsnummer INT, kundennummer INT, rechnungsdatum TEXT)")
    except Exception as e:
        pass

    conn.commit()
    conn.close()
