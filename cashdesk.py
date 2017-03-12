#!/usr/bin/env python

#: cashdesk
#: ein minimales fakturierungsprogramm
#: Copyright 2017, Richard Kaemmerer <richard@richardkaemmerer.de>

from flask import Flask, render_template, send_from_directory, request, redirect, url_for
import sqlite3
import dateutil.parser
from path import Path
import time

#: eigene importe

import database.setup
import database.settings
import database.artikel
import database.rechnungen
import database.kunden

sqlite_file = "cashdesk.sqlite"
debug = True
bind_host = '0.0.0.0'
bind_port = 5000
dbversion = 1

database.setup.setup_database(sqlite_file, dbversion)

app = Flask(__name__, static_url_path = '')

@app.route('/assets/<path:path>')
def serve_asset(path):
        return send_from_directory('assets', path)

@app.route('/')
def show_index():

    page_title = "Startseite"
    page_id = "index"

    return render_template('index.html', page_title = page_title, page_id = page_id)

@app.route('/artikel')
def show_artikel():

    page_title = "Artikelverwaltung"
    page_id = "artikel"

    artikel = database.artikel.load_artikel(sqlite_file)

    return render_template('artikel.html', artikel = artikel, page_title = page_title, page_id = page_id)

@app.route('/artikel/neu')
def show_artikel_neu():

    page_title = "Neuen Artikel anlegen"
    page_id = "artikelneu"

    return render_template('artikel-neu.html', page_title = page_title, page_id = page_id)

@app.route('/artikel/speichern', methods = ['POST'])
def artikel_speichern():

    database.artikel.save_artikel(sqlite_file, request.form)

    return redirect(url_for('show_artikel'))

@app.route('/artikel/bearbeiten/<string:id>')
def show_artikel_bearbeiten(id):

    page_title = "Artikel bearbeiten"
    page_id = "artikelbearbeiten"

    artikel = database.artikel.load_single_artikel(sqlite_file, id)

    return render_template('artikel-bearbeiten.html', page_title = page_title, page_id = page_id, artikel = artikel)

@app.route('/artikel/aktualisieren', methods = ['POST'])
def artikel_aktualisieren():

    database.artikel.update_artikel(sqlite_file, request.form)

    return redirect(url_for('show_artikel'))

@app.route('/artikel/loeschen/<string:id>')
def artikel_loeschen(id):

        database.artikel.delete_artikel(sqlite_file, id)

        return redirect(url_for('show_artikel'))

@app.route('/kunden')
def show_kunden():

    page_title = "Kundenverwaltung"
    page_id = "kunden"

    return render_template('kunden.html', page_title = page_title, page_id = page_id)

@app.route('/eingangsrechnungen')
def show_eingangsrechnungen():

    page_title = "Eingangsrechnungen"
    page_id = "eingangsrechnungen"

    return render_template('eingangsrechnungen.html', page_title = page_title, page_id = page_id)

@app.route('/ausgangsrechnungen')
def show_ausgangsrechnungen():

    page_title = "Ausgangsrechnungen"
    page_id = "ausgangsrechnungen"

    rechnungen = database.rechnungen.load_rechnungen(sqlite_file)

    return render_template('ausgangsrechnungen.html', rechnungen = rechnungen, page_title = page_title, page_id = page_id)

@app.route('/ausgangsrechnungen/neu')
def show_ausgangsrechnungen_neu():

    page_title = "Neue Ausgangsrechnung"
    page_id = "ausgangsrechnungneu"

    kunden = database.kunden.load_kunden(sqlite_file)    
    rechnungs_id = database.rechnungen.get_next_invoice_id(sqlite_file)

    return render_template('ausgangsrechnung-neu.html', kunden = kunden, rechnungs_id = rechnungs_id, page_title = page_title, page_id = page_id)

@app.route('/kassenbuch')
def show_kassenbuch():

    page_title = "Kassenbuch"
    page_id = "kassenbuch"

    return render_template('kassenbuch.html', page_title = page_title, page_id = page_id)

@app.route('/einstellungen')
def show_einstellungen():

    page_title = "Einstellungen"
    page_id = "einstellungen"

    einstellungen = database.settings.load_settings(sqlite_file)

    return render_template('einstellungen.html', page_title = page_title, page_id = page_id, einstellungen = einstellungen)

@app.route('/einstellungen/speichern', methods = ['POST'])
def einstellungen_speichern():

    database.settings.save_settings(sqlite_file, request.form)

    return redirect(url_for('show_einstellungen'))

if __name__ == '__main__':
	app.run(debug = debug, host = bind_host, port = bind_port)
