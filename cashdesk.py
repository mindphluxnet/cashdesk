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
import os.path
import imghdr
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
import database.konten
import database.lieferanten

import statics.konten

import raspi.raspi

sqlite_file = "cashdesk.sqlite"
upload_dir = "assets/"
debug = True
bind_host = '0.0.0.0'
bind_port = 5000
dbversion = 1

database.setup.setup_database(sqlite_file, dbversion)
settings = database.settings.load_settings()

if(raspi.raspi.is_raspi()):
    lcd = lcddriver.lcd()
    lcd.clear()
    if(settings['enable_lcd'] == '1'):
        try:
            lcd.display_string(settings['lcd_greeting_line1'], 1)
            lcd.display_string(settings['lcd_greeting_line2'], 2)
            lcd.display_string(settings['lcd_greeting_line3'], 3)
            lcd.display_string(settings['lcd_greeting_line4'], 4)
        except Exception as e:
            print(e.message)
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

    has_logo = False
    if(os.path.isfile('assets/firmenlogo.png')):
        has_logo = True

    return render_template('index.html', page_title = page_title, page_id = page_id, has_logo = has_logo)

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

@app.route('/kunden/bearbeiten/<string:id>')
def show_kunden_bearbeiten(id):

    page_title = "Kunden bearbeiten"
    page_id = "kundenbearbeiten"

    kunde = database.kunden.load_kunde(sqlite_file, id)

    return render_template('kunden-bearbeiten.html', kunde = kunde, page_title = page_title, page_id = page_id)

@app.route('/kunden/speichern', methods = ['POST'])
def kunde_speichern():

    database.kunden.save_kunde(sqlite_file, request.form)

    return redirect(url_for('show_kunden'))

@app.route('/kunden/aktualisieren', methods = ['POST'])
def kunde_aktualisieren():

    database.kunden.update_kunde(sqlite_file, request.form)

    return redirect(url_for('show_kunden'))

@app.route('/kunden/ajax/speichern', methods = ['POST'])
def kunde_ajax_speichern():

    new_id = database.kunden.save_kunde(sqlite_file, request.form)
    kunden = database.kunden.load_kunden(sqlite_file)

    result = []

    result.append(kunden)
    result.append(new_id)

    return json.dumps(result)

@app.route('/lieferanten')
def show_lieferanten():

    page_title = "Lieferanten"
    page_id = "lieferanten"

    lieferanten = database.lieferanten.load_lieferanten(sqlite_file)

    return render_template('lieferanten.html', lieferanten = lieferanten, page_title = page_title, page_id = page_id)

@app.route('/eingangsrechnungen')
def show_eingangsrechnungen():

    page_title = "Eingangsrechnungen"
    page_id = "eingangsrechnungen"

    rechnungen = database.rechnungen.load_eingangsrechnungen(sqlite_file)

    gesamtausgabe = 0

    for rechnung in rechnungen:
        lieferant = database.lieferanten.load_lieferant(sqlite_file, rechnung['lieferant_id'])
        rechnung['lieferant'] = lieferant['firmenname']
        gesamtausgabe = gesamtausgabe + rechnung['rechnungsbetrag']

    return render_template('eingangsrechnungen.html', rechnungen = rechnungen, gesamtausgabe = gesamtausgabe, page_title = page_title, page_id = page_id)

@app.route('/ausgangsrechnungen')
def show_ausgangsrechnungen():

    page_title = "Ausgangsrechnungen"
    page_id = "ausgangsrechnungen"

    rechnungen = database.rechnungen.load_rechnungen(sqlite_file)
    konten = database.konten.load_konten(sqlite_file)

    gesamtumsatz = 0
    gesamtgewinn = 0

    for rechnung in rechnungen:
        positionen = database.rechnungen.load_positionen(sqlite_file, rechnung['rechnungsnummer'])

        umsatz = 0
        rohgewinn = 0

        for pos in positionen:
            umsatz = umsatz + pos['anzahl'] * (pos['vkpreis'] - (pos['vkpreis'] / 100 * pos['rabatt']))
            rohgewinn = umsatz - (pos['ekpreis'] * pos['anzahl'])

        if(rechnung['storno_rechnungsnummer'] == 0 or rechnung['storno_rechnungsnummer'] == None):
            rechnung['umsatz'] = umsatz
            rechnung['rohgewinn'] = rohgewinn
        else:
            rechnung['umsatz'] = -umsatz
            rechnung['rohgewinn'] = -rohgewinn

        gesamtumsatz = gesamtumsatz + rechnung['umsatz']
        gesamtgewinn = gesamtgewinn + rechnung['rohgewinn']


    return render_template('ausgangsrechnungen.html', rechnungen = rechnungen, konten = konten, gesamtumsatz = gesamtumsatz, gesamtgewinn = gesamtgewinn, page_title = page_title, page_id = page_id)

@app.route('/ausgangsrechnungen/neu')
def show_ausgangsrechnungen_neu():

    page_title = "Neue Ausgangsrechnung"
    page_id = "ausgangsrechnungneu"

    kunden = database.kunden.load_kunden(sqlite_file)
    rechnungsnummer = database.rechnungen.get_next_invoice_id(sqlite_file)

    return render_template('ausgangsrechnung-neu.html', kunden = kunden, rechnungsnummer = rechnungsnummer, page_title = page_title, page_id = page_id)

@app.route('/ausgangsrechnungen/speichern/step1', methods = ['POST'])
def ausgangsrechnung_speichern_step1():

    rechnung_id = database.rechnungen.save_rechnung(sqlite_file, request.form)

    return redirect('/ausgangsrechnungen/neu/step2/' + str(rechnung_id))

@app.route('/ausgangsrechnungen/neu/step2/<string:id>')
def ausgangsrechnung_neu_step2(id):

    page_title = "Ausgangsrechnung bearbeiten"
    page_id = "ausgangsrechnungen"

    rechnung = database.rechnungen.load_rechnung(sqlite_file, id)
    kunden = database.kunden.load_kunden(sqlite_file)
    artikel = database.artikel.load_artikel(sqlite_file)
    positionen = database.rechnungen.load_positionen(sqlite_file, id)
    settings = database.settings.load_settings()

    for pos in positionen:
        pos['rabattpreis'] = pos['vkpreis'] - (pos['vkpreis'] / 100 * pos['rabatt'])


    gesamtpreis = 0

    for pos in positionen:
        gesamtpreis = gesamtpreis + (pos['rabattpreis'] * pos['anzahl'])

    rohgewinn = 0

    for pos in positionen:
        rohgewinn = gesamtpreis - (pos['ekpreis'] * pos['anzahl'])

    ust = (gesamtpreis / 100) * float(settings['ustsatz'])

    return render_template('ausgangsrechnung-neu-step2.html', einstellungen = settings, artikel = artikel, positionen = positionen, ust = ust, rohgewinn = rohgewinn, gesamtpreis = gesamtpreis, kunden = kunden, rechnung = rechnung, page_title = page_title, page_id = page_id)

@app.route('/ausgangsrechnungen/verbuchen', methods = ['POST'])
def ausgangsrechnung_verbuchen():

    database.rechnungen.ausgangsrechnung_verbuchen(sqlite_file, request.form)

    return redirect(url_for('show_ausgangsrechnungen'))

@app.route('/ausgangsrechnungen/speichern/step3', methods = ['POST'])
def ausgangsrechnung_speichern_step3():

    rechnung_id = database.rechnungen.update_rechnung(sqlite_file, request.form)

    return redirect('/ausgangsrechnungen/ausgeben/' + str(rechnung_id))

@app.route('/ausgangsrechnungen/ausgeben/<string:id>')
def ausgangsrechnung_ausgeben(id):

    page_title = "Ausgangsrechnung ausgeben"
    page_id = "ausgangsrechnungen"

    rechnung = database.rechnungen.load_rechnung(sqlite_file, id)
    positionen = database.rechnungen.load_positionen(sqlite_file, id)

    return render_template('ausgangsrechnung-ausgeben.html', page_title = page_title, page_id = page_id, rechnung = rechnung, positionen = positionen)

@app.route('/ausgangsrechnungen/pdfrenderer/<string:action>/<string:typ>/<string:id>')
def ausgangsrechnungen_pdfrenderer(action, typ, id):

    rechnung = database.rechnungen.load_rechnung(sqlite_file, id)
    kunde = database.kunden.load_kunde(sqlite_file, rechnung['kunden_id'])
    positionen = database.rechnungen.load_positionen(sqlite_file, id)
    stammdaten = database.settings.load_settings()

    #: Rechnung als gedruckt markieren

    database.rechnungen.rechnung_gedruckt(sqlite_file, id)

    if(typ == 'rechnung'):
        template = 'template-ausgangsrechnung'
        outfile = 'rechnung-'
        alte_rechnungs_id = 0
    elif(typ == 'gutschrift'):
        template = 'template-gutschrift'
        outfile = 'gutschrift-'
        alte_rechnungs_id = rechnung['storno_rechnungsnummer']

    gesamtsumme = 0

    for pos in positionen:
        if(typ == 'gutschrift'):
            pos['vkpreis'] = -pos['vkpreis']
        possumme = (pos['vkpreis'] - ((pos['vkpreis'] / 100) * pos['rabatt'])) * pos['anzahl']
        gesamtsumme = gesamtsumme + possumme

    mwst = (gesamtsumme / 100) * float(stammdaten['ustsatz'])

    bootstrap_css = ''

    f = file('assets/css/bootstrap.min.css', 'r')
    for line in f:
        bootstrap_css = bootstrap_css + line

    f.close()

    with open('assets/firmenlogo.png', 'rb') as logo:
        firmenlogo = base64.b64encode(logo.read())

    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template(template + '.html')
    out = template.render(bootstrap_css = bootstrap_css, firmenlogo = firmenlogo, rechnung = rechnung, positionen = positionen, stammdaten = stammdaten, kunde = kunde, gesamtsumme = gesamtsumme, mwst = mwst, alte_rechnungs_id = alte_rechnungs_id)
    pdf = pdfkit.from_string(out, False)

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    if(action == 'speichern'):
        response.headers['Content-Disposition'] = 'attachment; filename=' + outfile + id + '.pdf'

    if(action == 'drucken'):
        response.headers['Content-Disposition'] = 'inline; filename=' + outfile + id + '.pdf'

    return response

@app.route('/ausgangsrechnungen/position/speichern', methods = ['POST'])
def ausgangsrechnung_position_speichern():

    database.rechnungen.save_position(sqlite_file, request.form)

    return redirect('/ausgangsrechnungen/neu/step2/' + str(request.form['rechnungs_id']))

@app.route('/ausgangsrechnungen/position/loeschen/<string:id>')
def ausgangsrechnung_position_loeschen(id):

    rechnungs_id = database.rechnungen.delete_position(sqlite_file, id)

    return redirect('/ausgangsrechnungen/neu/step2/' + str(rechnungs_id))

@app.route('/ausgangsrechnungen/position/bearbeiten', methods = ['POST'])
def ausgangsrechnung_position_bearbeiten():

    database.rechnungen.update_position(sqlite_file, request.form)

    return redirect('/ausgangsrechnungen/neu/step2/' + str(request.form['rechnungs_id']))

@app.route('/positionen/ajax/position/<string:id>')
def positionen_ajax_position(id):

    position = database.rechnungen.load_position(sqlite_file, id)

    return json.dumps(position)

@app.route('/ausgangsrechnungen/stornieren/<string:id>')
def ausgangsrechnung_stornieren(id):

    page_title = "Rechnung stornieren"
    page_id = "ausgangsrechnungen"

    settings = database.settings.load_settings()
    rechnung = database.rechnungen.load_rechnung(sqlite_file, id)
    positionen = database.rechnungen.load_positionen(sqlite_file, id)
    kunden = database.kunden.load_kunden(sqlite_file)

    for pos in positionen:
        pos['vkpreis'] = -pos['vkpreis']
        pos['rabattpreis'] = pos['vkpreis'] - (pos['vkpreis'] / 100 * pos['rabatt'])

    gesamtpreis = 0

    for pos in positionen:
        gesamtpreis = gesamtpreis + (pos['rabattpreis'] * pos['anzahl'])

    rohgewinn = 0

    for pos in positionen:
        rohgewinn = gesamtpreis - (-pos['ekpreis'] * pos['anzahl'])

    ust = (gesamtpreis / 100) * float(settings['ustsatz'])

    return render_template('ausgangsrechnung-stornieren.html', page_title = page_title, page_id = page_id, rechnung = rechnung, positionen = positionen, kunden = kunden, einstellungen = settings, ust = ust, gesamtpreis = gesamtpreis, rohgewinn = rohgewinn)

@app.route('/ausgangsrechnungen/stornieren/speichern', methods = ['POST'])
def ausgangsrechnung_stornieren_speichern():

    neue_rechnungsnummer = database.rechnungen.rechnung_stornieren(sqlite_file, request.form)

    return redirect('/ausgangsrechnungen/stornieren/ausgeben/' + str(neue_rechnungsnummer))

@app.route('/ausgangsrechnungen/stornieren/ausgeben/<string:id>')
def ausgangsrechnung_stornieren_ausgeben(id):

    page_title = "Gutschrift ausgeben"
    page_id = "ausgangsrechnungen"

    rechnung = database.rechnungen.load_rechnung(sqlite_file, id)

    return render_template('gutschrift-ausgeben.html', page_title = page_title, page_id = page_id, rechnung = rechnung)


@app.route('/ausgangsrechnungen/loeschen/<string:id>')
def ausgangsrechnung_loeschen(id):

    database.rechnungen.delete_rechnung(sqlite_file, id)

    return redirect(url_for('show_ausgangsrechnungen'))

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

    has_logo = False
    if(os.path.isfile('assets/firmenlogo.png') and imghdr.what('assets/firmenlogo.png') == 'png'):
        has_logo = True

    return render_template('einstellungen.html', page_title = page_title, page_id = page_id, einstellungen = einstellungen, is_raspi = is_raspi, has_logo = has_logo)

@app.route('/einstellungen/speichern', methods = ['POST'])
def einstellungen_speichern():

    uploaded_file = request.files['logobild']
    if(uploaded_file):
        uploaded_file.save('assets/firmenlogo.png')

    database.settings.save_settings(request.form)

    return redirect(url_for('show_einstellungen'))

@app.route('/konten', methods = ['GET'])
def show_konten():

    show_delete = False
    if(request.args.get('show_delete') == 'True'):
        show_delete = True

    page_title = "Kontoverwaltung"
    page_id = "konten"

    konten = database.konten.load_konten(sqlite_file)

    return render_template('konten.html', page_title = page_title, page_id = page_id, konten = konten, show_delete = show_delete)

@app.route('/konten/neu')
def show_konten_neu():

    page_title = "Neues Konto anlegen"
    page_id = "konten"

    return render_template('konten-neu.html', page_title = page_title, page_id = page_id)

@app.route('/konten/bearbeiten/<string:id>')
def show_konten_bearbeiten(id):

    page_title = "Konto bearbeiten"
    page_id = "konten"

    konto = database.konten.load_konto(sqlite_file, id)

    return render_template('konten-bearbeiten.html', konto = konto, page_title = page_title, page_id = page_id)

@app.route('/konten/speichern', methods = ['POST'])
def konten_speichern():

    database.konten.save_konto(sqlite_file, request.form)

    return redirect(url_for('show_konten'))

@app.route('/konten/aktualisieren', methods = ['POST'])
def konten_aktualisieren():

    database.konten.update_konto(sqlite_file, request.form)

    return redirect(url_for('show_konten'))

@app.route('/konten/loeschen/<string:id>')
def konten_loeschen(id):

    database.konten.delete_konto(sqlite_file, id)

    return redirect(url_for('show_konten'))

if __name__ == '__main__':
	app.run(debug = debug, host = bind_host, port = bind_port)
