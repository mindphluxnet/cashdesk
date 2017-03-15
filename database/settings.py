import sqlite3

import database.factory

def save_settings(sqlite_file, settings):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("UPDATE einstellungen SET firmenname = ?, inhaber = ?, strasse = ?, hausnummer = ?, plz = ?, ort = ?, ustid = ?, kleinunternehmer = ?, ustsatz = ?, enable_lcd = ?, lcd_greeting_line1 = ?, lcd_greeting_line2 = ?, lcd_goodbye_line1 = ?, lcd_goodbye_line2 = ? WHERE oid = 1", [ settings['firmenname'], settings['inhaber'], settings['strasse'], settings['hausnummer'], settings['plz'], settings['ort'], settings['ustid'], settings['kleinunternehmer'], settings['ustsatz'], settings['enable_lcd'], settings['lcd_greeting_line1'], settings['lcd_greeting_line2'], settings['lcd_goodbye_line1'], settings['lcd_goodbye_line2'] ])

    conn.commit()
    conn.close()

def load_settings(sqlite_file):

    conn = sqlite3.connect(sqlite_file)
    conn.row_factory = database.factory.dict_factory
    c = conn.cursor()

    c.execute("SELECT * FROM einstellungen WHERE oid = 1")
    einstellungen = c.fetchone()

    return einstellungen
