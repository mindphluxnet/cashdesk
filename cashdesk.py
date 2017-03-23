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
import database.wareneingang
import database.buchungen

import statics.konten

import raspi.raspi

import backup.dbx

sqlite_file = "cashdesk.sqlite"
upload_dir = "assets/"
debug = True
bind_host = '0.0.0.0'
bind_port = 5000
dbversion = 1

app = Flask(__name__, static_url_path = '')

database.setup.setup_database(sqlite_file)
settings = database.settings.load_settings()

try:
    os.makedirs('dokumente/eingangsrechnungen')
except OSError as Exception:
    pass

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

if(debug == False):
    webbrowser.open(('http://' + bind_host + ':' + str(bind_port)))

@app.route('/assets/<path:path>')
def serve_asset(path):
        return send_from_directory('assets', path)

@app.route('/pdfviewer/<string:id>')
def pdfviewer(id):

    return send_from_directory('dokumente/eingangsrechnungen', 'eingangsrechnung-' + str(id) + '.pdf')

@app.route('/')
def show_index():

    page_title = "Startseite"
    page_id = "index"

    has_logo = False
    if(os.path.isfile('assets/firmenlogo.png')):
        has_logo = True

    return render_template('index.html', page_title = page_title, page_id = page_id, has_logo = has_logo)

@app.route('/backups')
def backups():

    page_title = "Backups"
    page_id = "backups"

    backups = backup.dbx.list_backups()

    backupfiles = []

    for b in backups.entries:
        out = [ b.name, b.client_modified ]
        backupfiles.append(out)

    #: Liste umdrehen (neueste zuerst)
    backups = backupfiles[::-1]

    del backups[25:]

    return render_template('backups.html', backups = backups, page_title = page_title, page_id = page_id)

@app.route('/prune_backups')
def prune_backups():

    backup.dbx.prune_backups()

    return redirect(url_for('backups'))

@app.route('/manual_backup')
def manual_backup():

    settings = database.settings.load_settings()

    backup.dbx.run_backup(sqlite_file, dbversion)

    return redirect(url_for('backups'))

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

@app.route('/artikel/kopieren/<string:id>')
def artikel_kopieren(id):

    page_title = "Artikel bearbeiten"
    page_id = "artikelbearbeiten"


    neue_id = database.artikel.copy_artikel(sqlite_file, id)
    artikel = database.artikel.load_single_artikel(sqlite_file, neue_id)

    return redirect('/artikel/bearbeiten/' + str(neue_id))

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

@app.route('/lieferanten/neu')
def show_lieferanten_neu():

    page_title = "Lieferanten anlegen"
    page_id = "lieferanten"

    return render_template('lieferanten-neu.html', page_title = page_title, page_id = page_id)

@app.route('/lieferanten/speichern', methods = ['POST'])
def save_lieferanten():

    database.lieferanten.save_lieferant(sqlite_file, request.form)

    return redirect(url_for('show_lieferanten'))

@app.route('/lieferanten/bearbeiten/<string:id>')
def edit_lieferanten(id):

    page_title = "Lieferanten bearbeiten"
    page_id = "lieferanten"

    lieferant = database.lieferanten.load_lieferant(sqlite_file, id)

    return render_template('lieferanten-bearbeiten.html', lieferant = lieferant, page_title = page_title, page_id = page_id)

@app.route('/lieferanten/aktualisieren', methods = ['POST'])
def update_lieferanten():

    database.lieferanten.update_lieferant(sqlite_file, request.form)

    return redirect(url_for('show_lieferanten'))

@app.route('/lieferanten/loeschen/<string:id>')
def delete_lieferant(id):

    database.lieferanten.delete_lieferant(sqlite_file, id)

    return redirect(url_for('show_lieferanten'))

@app.route('/lieferanten/ajax/speichern', methods = ['POST'])
def lieferanten_ajax_speichern():

    new_id = database.lieferanten.save_lieferant(sqlite_file, request.form)
    lieferanten = database.lieferanten.load_lieferanten(sqlite_file)

    result = []

    result.append(lieferanten)
    result.append(new_id)

    return json.dumps(result)

@app.route('/eingangsrechnungen')
def show_eingangsrechnungen():

    page_title = "Eingangsrechnungen"
    page_id = "eingangsrechnungen"

    rechnungen = database.rechnungen.load_eingangsrechnungen(sqlite_file)
    konten = database.konten.load_konten(sqlite_file)

    gesamtausgabe = 0

    for rechnung in rechnungen:
        lieferant = database.lieferanten.load_lieferant(sqlite_file, rechnung['lieferant_id'])
        rechnung['lieferant'] = lieferant['firmenname']
        gesamtausgabe = gesamtausgabe + rechnung['rechnungsbetrag']
        if(os.path.isfile('dokumente/eingangsrechnungen/eingangsrechnung-' + str(rechnung['rowid']) + '.pdf')):
            rechnung['pdf'] = True;

    return render_template('eingangsrechnungen.html', rechnungen = rechnungen, konten = konten, gesamtausgabe = gesamtausgabe, page_title = page_title, page_id = page_id)

@app.route('/eingangsrechnungen/neu')
def show_eingangsrechnungen_neu():

    page_title = "Neue Eingangsrechnung"
    page_id = "eingangsrechnungen"

    lieferanten = database.lieferanten.load_lieferanten(sqlite_file)
    eurkonten = statics.konten.get_eurkonten()
    artikel = database.artikel.load_artikel(sqlite_file)

    return render_template('eingangsrechnung-neu.html', lieferanten = lieferanten, eurkonten = eurkonten, artikel = artikel, page_title = page_title, page_id = page_id)

@app.route('/eingangsrechnungen/speichern/step1', methods = ['POST'])
def eingangsrechnung_speichern_step1():

    rechnung_id = database.rechnungen.save_eingangsrechnung(sqlite_file, request.form)

    return redirect('/eingangsrechnungen/neu/step2/' + str(rechnung_id))

@app.route('/eingangsrechnungen/neu/step2/<string:id>')
def show_eingangsrechnungen_neu_step2(id):

    page_title = "Eingangsrechnung bearbeiten"
    page_id = "eingangsrechnungen"

    rechnung = database.rechnungen.load_eingangsrechnung(sqlite_file, id)
    lieferanten = database.lieferanten.load_lieferanten(sqlite_file)
    eurkonten = statics.konten.get_eurkonten()
    artikel = database.artikel.load_artikel(sqlite_file)
    wareneingang = database.wareneingang.load_wareneingang(sqlite_file, id)
    einstellungen = database.settings.load_settings()

    return render_template('eingangsrechnung-neu-step2.html', rechnung = rechnung, lieferanten = lieferanten, eurkonten = eurkonten, artikel = artikel, wareneingang = wareneingang, einstellungen = einstellungen, page_title = page_title, page_id = page_id)

@app.route('/eingangsrechnungen/position/speichern', methods = ['POST'])
def eingangsrechnungen_position_speichern():

    rechnung_id = request.form['rechnungs_id']

    database.wareneingang.save_position(sqlite_file, request.form)

    return redirect('/eingangsrechnungen/neu/step2/' + str(rechnung_id))

@app.route('/eingangsrechnungen/position/bearbeiten', methods = ['POST'])
def eingangsrechnungen_position_bearbeiten():

    rechnung_id = request.form['rechnungs_id']

    database.wareneingang.update_position(sqlite_file, request.form)

    return redirect('/eingangsrechnungen/neu/step2/' + str(rechnung_id))

@app.route('/wareneingang/ajax/position/<string:id>')
def wareneingang_ajax_position(id):

    position = database.wareneingang.load_position(sqlite_file, id)

    return json.dumps(position)

@app.route('/eingangsrechnungen/position/loeschen/<string:id>')
def eingangsrechnungen_position_loeschen(id):

    rechnung_id = database.wareneingang.delete_position(sqlite_file, id)

    return redirect('/eingangsrechnungen/neu/step2/' + str(rechnung_id))

@app.route('/eingangsrechnungen/verbuchen', methods = ['POST'])
def eingangsrechnungen_verbuchen():

    page_title = "Eingangsrechnung verbuchen"
    page_id = "eingangsrechnungen"

    id = database.rechnungen.update_eingangsrechnung(sqlite_file, request.form)
    database.wareneingang.wareneingang_verbuchen(sqlite_file, id)

    #: FIXME: sollte natuerlich auch fuer andere Dateien funktionieren
    uploaded_file = request.files['pdf']
    if(uploaded_file):
        uploaded_file.save('dokumente/eingangsrechnungen/eingangsrechnung-' + str(id) + '.pdf')

    return redirect(url_for('show_eingangsrechnungen'))

@app.route('/eingangsrechnungen/loeschen/<string:id>')
def eingangsrechnungen_loeschen(id):

    database.rechnungen.delete_eingangsrechnung(sqlite_file, id)

    return redirect(url_for('show_eingangsrechnungen'))

@app.route('/eingangsrechnungen/bezahlt', methods = ['POST'])
def eingangsrechnungen_bezahlt():

    database.rechnungen.eingangsrechnung_bezahlt(sqlite_file, request.form)

    return redirect(url_for('show_eingangsrechnungen'))

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

@app.route('/buchungskonten/umbuchung', methods = ['POST'])
def buchungskonten_umbuchung():

    database.buchungen.umbuchung(sqlite_file, request.form)

    return redirect(url_for('show_buchungskonten'))

@app.route('/buchungskonten/privateinlage', methods = ['POST'])
def buchungskonten_privateinlage():

    database.buchungen.privateinlage(sqlite_file, request.form)

    return redirect(url_for('show_buchungskonten'))

@app.route('/buchungskonten/privatentnahme', methods = ['POST'])
def buchungskonten_privatentnahme():

    database.buchungen.privatentnahme(sqlite_file, request.form)

    return redirect(url_for('show_buchungskonten'))

@app.route('/buchungskonten')
@app.route('/buchungskonten/<usekonto>')
def show_buchungskonten(usekonto = 0):

    page_title = "Buchungskonten"
    page_id = "buchungskonten"

    konten = database.konten.load_konten(sqlite_file)
    stammdaten = database.settings.load_settings()

    if(usekonto == 0):
        usekonto = konten[0]['rowid']

    buchungen = database.buchungen.load_buchungen(sqlite_file, usekonto)

    saldo = 0

    #: Buchungen aufbereiten
    for buchung in buchungen:

        #: Umbuchungen zwischen Geschaeftskonten
        if(buchung['gegenkonto_id'] != 0 and buchung['gegenkonto_id'] != None):
            buchung['umbuchung'] = True
            gk = database.konten.load_konto(sqlite_file, buchung['gegenkonto_id'])
            dk = database.konten.load_konto(sqlite_file, usekonto)
            buchung['empfaenger'] = dk['bezeichnung']
            if(buchung['einaus'] == 1):
                buchung['verwendungszweck'] = "Umbuchung von " + gk['bezeichnung']
            else:
                buchung['verwendungszweck'] = "Umbuchung auf " + gk['bezeichnung']
        else:
            buchung['umbuchung'] = False

        #: Privateinlagen
        if((buchung['gegenkonto_id'] == 0 or buchung['gegenkonto_id'] == None) and (buchung['ausgangsrechnungs_id'] == 0 or buchung['ausgangsrechnungs_id'] == None) and (buchung['eingangsrechnungs_id'] == 0 or buchung['eingangsrechnungs_id'] == None) and buchung['einaus'] == 1):
            dk = database.konten.load_konto(sqlite_file, usekonto)
            buchung['empfaenger'] = dk['bezeichnung']
            buchung['verwendungszweck'] = "Privateinlage"

        #: Privatentnahmen
        if((buchung['gegenkonto_id'] == 0 or buchung['gegenkonto_id'] == None) and (buchung['ausgangsrechnungs_id'] == 0 or buchung['ausgangsrechnungs_id'] == None) and (buchung['eingangsrechnungs_id'] == 0 or buchung['eingangsrechnungs_id'] == None) and buchung['einaus'] == 0):
            dk = database.konten.load_konto(sqlite_file, usekonto)
            buchung['empfaenger'] = stammdaten['inhaber']
            buchung['verwendungszweck'] = "Privatentnahme"

        #: Ausgangsrechnungen
        if(buchung['ausgangsrechnungs_id'] != 0 and buchung['ausgangsrechnungs_id'] != None):
            re = database.rechnungen.load_rechnung(sqlite_file, buchung['ausgangsrechnungs_id'])
            if(buchung['einaus'] == 1):
                buchung['empfaenger'] = stammdaten['firmenname']
                buchung['verwendungszweck'] = "Zahlung Ausgangsrechnung Nr. " + re['rechnungsnummer'] + " durch Kunde"
            else:
                buchung['empfaenger'] = re['nachname'] + ', ' + re['vorname']
                buchung['verwendungszweck'] = "Erstattung Gutschrift " + re['rechnungsnummer'] + " an Kunde"

        #: Eingangsrechnungen
        if(buchung['eingangsrechnungs_id'] != 0 and buchung['eingangsrechnungs_id'] != None):
            re = database.rechnungen.load_eingangsrechnung(sqlite_file, buchung['eingangsrechnungs_id'])
            li = database.lieferanten.load_lieferant(sqlite_file, re['lieferant_id'])
            buchung['empfaenger'] = li['firmenname']
            buchung['verwendungszweck'] = "Zahlung Eingangsrechnung Nr. " + re['rechnungsnummer']
            if(os.path.isfile('/dokumente/eingangsrechnung/eingangsrechnung-' + str(buchung['eingangsrechnungs_id']) + '.pdf')):
                buchung['pdf'] = True

        #: Saldo

        saldo = saldo + buchung['betrag']
        buchung['saldo'] = saldo

    return render_template('buchungskonten.html', konten = konten, buchungen = buchungen, usekonto = int(usekonto), saldo = saldo, page_title = page_title, page_id = page_id)

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
