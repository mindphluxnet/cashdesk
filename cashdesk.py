#!/usr/bin/env python

#: cashdesk
#: ein minimales fakturierungsprogramm
#: Copyright 2017, Richard Kaemmerer <richard@richardkaemmerer.de>

from flask import Flask, render_template, send_from_directory, request, redirect, url_for, send_file, make_response
import sqlite3
import dateutil.parser
import time
import json
import webbrowser
import pdfkit
from jinja2 import Environment, FileSystemLoader
import base64
try:
    import lcddriver
except Exception:
    pass

#: eigene importe

import database.setup
import database.settings
import database.artikel
import database.rechnungen
import database.kunden

import raspi.raspi

sqlite_file = "cashdesk.sqlite"
debug = True
bind_host = '0.0.0.0'
bind_port = 5000
dbversion = 1

database.setup.setup_database(sqlite_file, dbversion)
settings = database.settings.load_settings()

if(raspi.raspi.is_raspi() and settings['enable_lcd'] == '1'):
    lcd = lcddriver.lcd()
    lcd.clear()
    try:
        lcd.display_string(settings['lcd_welcome_line1'], 1)
        lcd.display_string(settings['lcd_welcome_line2'], 2)
        lcd.display_string(settings['lcd_welcome_line3'], 3)
        lcd.display_string(settings['lcd_welcome_line4'], 4)
    except Exception:
	pass

app = Flask(__name__, static_url_path = '')

if(debug == False):
    webbrowser.open('http://localhost:5000')

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

@app.route('/artikel/ajax/preis/<string:id>')
def artikel_ajax_preis(id):

    artikel = database.artikel.load_single_artikel(sqlite_file, id)
    return str(artikel['vkpreis'])


@app.route('/kunden')
def show_kunden():

    page_title = "Kundenverwaltung"
    page_id = "kunden"

    kunden = database.kunden.load_kunden(sqlite_file)

    return render_template('kunden.html', kunden = kunden, page_title = page_title, page_id = page_id)

@app.route('/kunden/neu')
def show_kunden_neu():

    page_title = "Neuer Kunde"
    page_id = "kundenneu"

    return render_template('kunden-neu.html', page_title = page_title, page_id = page_id)

@app.route('/kunden/speichern', methods = ['POST'])
def kunde_speichern():

    database.kunden.save_kunde(sqlite_file, request.form)

    return redirect(url_for('show_kunden'))

@app.route('/kunden/ajax/speichern', methods = ['POST'])
def kunde_ajax_speichern():

    new_id = database.kunden.save_kunde(sqlite_file, request.form)
    kunden = database.kunden.load_kunden(sqlite_file)

    result = []

    result.append(kunden)
    result.append(new_id)

    return json.dumps(result)

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

    for rechnung in rechnungen:
        positionen = database.rechnungen.load_positionen(sqlite_file, rechnung['rechnungs_id'])

        umsatz = 0
        rohgewinn = 0

        for pos in positionen:
            umsatz = umsatz + ((pos['vkpreis'] - ((pos['vkpreis'] / 100) * pos['rabatt']) * pos['anzahl']))
            rohgewinn = umsatz - (pos['ekpreis'] * pos['anzahl'])

        rechnung['umsatz'] = umsatz
        rechnung['rohgewinn'] = rohgewinn

    return render_template('ausgangsrechnungen.html', rechnungen = rechnungen, page_title = page_title, page_id = page_id)

@app.route('/ausgangsrechnungen/neu')
def show_ausgangsrechnungen_neu():

    page_title = "Neue Ausgangsrechnung (Schritt 1)"
    page_id = "ausgangsrechnungneu"

    kunden = database.kunden.load_kunden(sqlite_file)
    rechnungsnummer = database.rechnungen.get_next_invoice_id(sqlite_file)

    return render_template('ausgangsrechnung-neu.html', kunden = kunden, rechnungsnummer = rechnungsnummer, page_title = page_title, page_id = page_id)

@app.route('/ausgangsrechnungen/neu/step2/<string:id>')
def ausgangsrechnung_neu_step2(id):

    page_title = "Neue Ausgangsrechnung (Schritt 2)"
    page_id = "ausgangsrechnungen"

    rechnung = database.rechnungen.load_rechnung(sqlite_file, id)
    kunden = database.kunden.load_kunden(sqlite_file)
    artikel = database.artikel.load_artikel(sqlite_file)
    positionen = database.rechnungen.load_positionen(sqlite_file, id)

    for pos in positionen:
        pos['rabattpreis'] = pos['vkpreis'] - (pos['vkpreis'] / 100 * pos['rabatt'])


    gesamtpreis = 0

    for pos in positionen:
        gesamtpreis = gesamtpreis + (pos['rabattpreis'] * pos['anzahl'])

    rohgewinn = 0

    for pos in positionen:
        rohgewinn = gesamtpreis - (pos['ekpreis'] * pos['anzahl'])

    ust = gesamtpreis - (gesamtpreis / 1.19)



    return render_template('ausgangsrechnung-neu-step2.html', artikel = artikel, positionen = positionen, ust = ust, rohgewinn = rohgewinn, gesamtpreis = gesamtpreis, kunden = kunden, rechnung = rechnung, page_title = page_title, page_id = page_id)

@app.route('/ausgangsrechnungen/speichern/step1', methods = ['POST'])
def ausgangsrechnung_speichern_step1():

    rechnung_id = database.rechnungen.save_rechnung_step1(sqlite_file, request.form)

    return redirect('/ausgangsrechnungen/neu/step2/' + str(rechnung_id))

@app.route('/ausgangsrechnungen/speichern/step3', methods = ['POST'])
def ausgangsrechnung_speichern_step3():

    rechnung_id = database.rechnungen.save_rechnung_step1(sqlite_file, request.form)

    return redirect('/ausgangsrechnungen/ausgeben/' + str(rechnung_id))

@app.route('/ausgangsrechnungen/ausgeben/<string:id>')
def ausgangsrechnung_ausgeben(id):

    page_title = "Ausgangsrechnung ausgeben"
    page_id = "ausgangsrechnungen"

    rechnung = database.rechnungen.load_rechnung(sqlite_file, id)
    positionen = database.rechnungen.load_positionen(sqlite_file, id)

    return render_template('ausgangsrechnung-ausgeben.html', page_title = page_title, page_id = page_id, rechnung = rechnung, positionen = positionen)

@app.route('/ausgangsrechnungen/pdfrenderer/<string:action>/<string:id>')
def ausgangsrechnungen_pdfrenderer(action, id):

    rechnung = database.rechnungen.load_rechnung(sqlite_file, id)
    kunde = database.kunden.load_kunde(sqlite_file, rechnung['kunden_id'])
    positionen = database.rechnungen.load_positionen(sqlite_file, id)
    stammdaten = database.settings.load_settings()

    gesamtsumme = 0
    for pos in positionen:
        possumme = (pos['vkpreis'] - ((pos['vkpreis'] / 100) * pos['rabatt'])) * pos['anzahl']
        gesamtsumme = gesamtsumme + possumme

    bootstrap_css = ''

    f = file('assets/css/bootstrap.min.css', 'r')
    for line in f:
        bootstrap_css = bootstrap_css + line

    f.close()

    with open('assets/firmenlogo.png', 'rb') as logo:
        firmenlogo = base64.b64encode(logo.read())

    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('template-ausgangsrechnung.html')
    out = template.render(bootstrap_css = bootstrap_css, firmenlogo = firmenlogo, bind_host = bind_host, bind_port = bind_port, rechnung = rechnung, positionen = positionen, stammdaten = stammdaten, kunde = kunde, gesamtsumme = gesamtsumme)
    pdf = pdfkit.from_string(out, False)

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    if(action == 'speichern'):
        response.headers['Content-Disposition'] = 'attachment; filename=rechnung-' + id + '.pdf'

    if(action == 'drucken'):
        response.headers['Content-Disposition'] = 'inline; filename=rechnung-' + id + '.pdf'

    return response

@app.route('/ausgangsrechnungen/position/speichern', methods = ['POST'])
def ausgangsrechnung_position_speichern():

    database.rechnungen.save_position(sqlite_file, request.form)

    return redirect('/ausgangsrechnungen/neu/step2/' + str(request.form['rechnungs_id']))

@app.route('/ausgangsrechnungen/position/loeschen/<string:id>')
def ausgangsrechnung_position_loeschen(id):

    rechnungs_id = database.rechnungen.delete_position(sqlite_file, id)

    return redirect('/ausgangsrechnungen/neu/step2/' + str(rechnungs_id))

@app.route('/positionen/ajax/position/<string:id>')
def positionen_ajax_position(id):

    position = database.rechnungen.load_position(sqlite_file, id)

    return json.dumps(position)

@app.route('/kassenbuch')
def show_kassenbuch():

    page_title = "Kassenbuch"
    page_id = "kassenbuch"

    return render_template('kassenbuch.html', page_title = page_title, page_id = page_id)

@app.route('/einstellungen')
def show_einstellungen():

    page_title = "Einstellungen"
    page_id = "einstellungen"

    einstellungen = database.settings.load_settings()
    is_raspi = raspi.raspi.is_raspi()

    return render_template('einstellungen.html', page_title = page_title, page_id = page_id, einstellungen = einstellungen, is_raspi = is_raspi)

@app.route('/einstellungen/speichern', methods = ['POST'])
def einstellungen_speichern():

    database.settings.save_settings(request.form)

    return redirect(url_for('show_einstellungen'))

if __name__ == '__main__':
	app.run(debug = debug, host = bind_host, port = bind_port)
