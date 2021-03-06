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
import database.warengruppen
import database.korrespondenz
import database.privatentnahmen
import database.barverkauf

import statics.konten

import raspi.raspi

import backup.dbx

sqlite_file = os.path.dirname(os.path.realpath(__file__)) + os.sep + "cashdesk.sqlite"
upload_dir = os.path.dirname(os.path.realpath(__file__)) + os.sep + "assets/"
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

    settings = database.settings.load_settings()

    no_backup = False
    if(settings['dropbox_api_key'] == "" or settings['dropbox_api_key'] == None):
        no_backup = True

    no_accounts = False
    konten = database.konten.load_konten(sqlite_file)
    if(len(konten) == 0):
        no_accounts = True

    no_backup_password = False
    if(settings['backup_passwort'] == '' or settings['backup_passwort'] == None):
        no_backup_password = True

    no_backup_freq = False
    if(settings['backupfrequenz'] == '0' or settings['backupfrequenz'] == None):
        no_backup_freq = True

    return render_template('index.html', page_title = page_title, page_id = page_id, has_logo = has_logo, no_backup = no_backup, no_accounts = no_accounts, no_backup_password = no_backup_password, no_backup_freq = no_backup_freq)

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
@app.route('/artikel/<string:id>')
def show_artikel(id = None):

    selwgr = id

    if(selwgr != None):
        artikel = database.artikel.load_artikel_by_wgr(sqlite_file, selwgr)
    else:
        first_wgr = database.warengruppen.get_first_wgr(sqlite_file)
        artikel = database.artikel.load_artikel_by_wgr(sqlite_file, first_wgr)
        selwgr = first_wgr

    warengruppen = database.warengruppen.load_warengruppen(sqlite_file)
    selwgr = database.warengruppen.load_warengruppe(sqlite_file, selwgr)

    for art in artikel:
        if(database.artikel.artikel_is_bundle(sqlite_file, art['rowid'])):
            art['bundle'] = True
        else:
            art['bundle'] = False

    page_title = "Artikelverwaltung"
    page_id = "artikel"

    return render_template('artikel.html', artikel = artikel, warengruppen = warengruppen, selwgr = selwgr, page_title = page_title, page_id = page_id)

@app.route('/artikel/info/<string:id>')
def show_artikel_info(id):

    page_title = "Artikelinformation"
    page_id = "artikel"

    artikel = database.artikel.load_single_artikel(sqlite_file, id)
    wareneingang = database.wareneingang.load_wareneingang_by_artikel(sqlite_file, id)
    settings = database.settings.load_settings()
    wgr = database.warengruppen.get_wgr_by_artikel(sqlite_file, id)

    median_ekpreis = 0
    warenwert_lager = 0

    for we in wareneingang:
        median_ekpreis += we['ekpreis']
        warenwert_lager += (we['ekpreis'] * we['anzahl'])

    if(len(wareneingang) > 0):
        median_ekpreis = median_ekpreis / len(wareneingang)

    ust = (median_ekpreis * (float(settings['ustsatz'])+100.0) /100.0) - median_ekpreis

    median_revenue = artikel['vkpreis'] - median_ekpreis - ust
    median_revenue_percent = (median_revenue / artikel['vkpreis']) * 100

    return render_template('artikel-info.html', artikel = artikel, wareneingang = wareneingang, median_ekpreis = median_ekpreis, median_revenue = median_revenue, median_revenue_percent = median_revenue_percent, ust = ust, wgr = wgr, warenwert_lager = warenwert_lager, page_title = page_title, page_id = page_id)

@app.route('/artikel/neu/<string:id>')
def show_artikel_neu(id):

    page_title = "Neuen Artikel anlegen"
    page_id = "artikelneu"

    selwgr = id

    warengruppen = database.warengruppen.load_warengruppen(sqlite_file)
    selwgr = database.warengruppen.load_warengruppe(sqlite_file, selwgr)

    return render_template('artikel-neu.html', warengruppen = warengruppen, selwgr = selwgr, page_title = page_title, page_id = page_id)

@app.route('/artikel/speichern', methods = ['POST'])
def artikel_speichern():

    database.artikel.save_artikel(sqlite_file, request.form)

    return redirect('/artikel/' + request.form['warengruppe'])

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
    warengruppen = database.warengruppen.load_warengruppen(sqlite_file)
    alle_artikel = database.artikel.load_artikel(sqlite_file)

    for art in alle_artikel:
        if(database.artikel.artikel_is_bundle(sqlite_file, art['rowid'])):
            art['bundle'] = True
        else:
            art['bundle'] = False

    bundle_artikel = database.artikel.load_bundle(sqlite_file, id)

    return render_template('artikel-bearbeiten.html', warengruppen = warengruppen, bundle_artikel = bundle_artikel, alle_artikel = alle_artikel, page_title = page_title, page_id = page_id, artikel = artikel)

@app.route('/artikel/aktualisieren', methods = ['POST'])
def artikel_aktualisieren():

    database.artikel.update_artikel(sqlite_file, request.form)

    return redirect('/artikel/' + request.form['warengruppe'])

@app.route('/artikel/archivieren/<string:id>')
def artikel_archivieren(id):

        wgr = database.artikel.archive_artikel(sqlite_file, id)

        return redirect('/artikel/' + str(wgr[0]))

@app.route('/artikel/wiederherstellen/<string:id>')
def artikel_wiederherstellen(id):

        wgr = database.artikel.restore_artikel(sqlite_file, id)

        return redirect('/artikel/' + str(wgr[0]))

@app.route('/artikel/ajax/preis/<string:id>')
def artikel_ajax_preis(id):

    artikel = database.artikel.load_single_artikel(sqlite_file, id)
    return str(artikel['vkpreis'])

@app.route('/artikel/bundle/speichern', methods = ['POST'])
def artikel_bundle_speichern():

    database.artikel.save_bundle(sqlite_file, request.form)

    return redirect('/artikel/bearbeiten/' + str(request.form['bundle_artikel_id']))

@app.route('/artikel/bundle/bearbeiten', methods = ['POST'])
def artikel_bundle_bearbeiten():

    database.artikel.update_bundle(sqlite_file, request.form)

    return redirect('/artikel/bearbeiten/' + str(request.form['bundle_artikel_id']))

@app.route('/artikel/bundle/loeschen/<string:id>')
def artikel_bundle_loeschen(id):

    id = database.artikel.delete_bundle(sqlite_file, id)

    return redirect('/artikel/bearbeiten/' + str(id))

@app.route('/artikel/bundle/auspacken/<string:id>')
def artikel_bundle_auspacken(id):

    id = database.artikel.unbundle(sqlite_file, id)

    return redirect('/artikel/' + str(id))

@app.route('/artikel/ajax/bundle/<string:id>')
def artikel_ajax_bundle(id):

    bundle = database.artikel.load_bundle_position(sqlite_file, id)

    return json.dumps(bundle)

@app.route('/warengruppen')
def show_warengruppen():

    page_title = "Warengruppen"
    page_id = "warengruppen"

    warengruppen = database.warengruppen.load_warengruppen(sqlite_file)

    return render_template('warengruppen.html', warengruppen = warengruppen, page_title = page_title, page_id = page_id)

@app.route('/warengruppen/neu')
def show_warengruppen_neu():

    page_title = "Neue Warengruppe anlegen"
    page_id = "warengruppen"

    return render_template('warengruppen-neu.html', page_title = page_title, page_id = page_id)

@app.route('/warengruppen/bearbeiten/<string:id>')
def show_warengruppen_bearbeiten(id):

    page_title = "Warengruppe bearbeiten"
    page_id = "warengruppen"

    warengruppe = database.warengruppen.load_warengruppe(sqlite_file, id)

    return render_template('warengruppen-bearbeiten.html', warengruppe = warengruppe, page_title = page_title, page_id = page_id)

@app.route('/warengruppen/speichern', methods = ['POST'])
def warengruppen_speichern():

    database.warengruppen.save_warengruppe(sqlite_file, request.form)

    return redirect(url_for('show_warengruppen'))

@app.route('/warengruppen/aktualisieren', methods = ['POST'])
def warengruppen_aktualisieren():

    database.warengruppen.update_warengruppe(sqlite_file, request.form)

    return redirect(url_for('show_warengruppen'))

@app.route('/warengruppen/loeschen/<string:id>')
def warengruppen_loeschen(id):

    database.warengruppen.delete_warengruppe(sqlite_file, id)

    return redirect(url_for('show_warengruppen'))

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

@app.route('/kunden/archivieren/<string:id>')
def kunden_archivieren(id):

    database.kunden.archive_kunde(sqlite_file, id)

    return redirect(url_for('show_kunden'))

@app.route('/kunden/wiederherstellen/<string:id>')
def kunden_wiederherstellen(id):

    database.kunden.restore_kunde(sqlite_file, id)

    return redirect(url_for('show_kunden'))

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

@app.route('/lieferanten/archivieren/<string:id>')
def archive_lieferant(id):

    database.lieferanten.archive_lieferant(sqlite_file, id)

    return redirect(url_for('show_lieferanten'))

@app.route('/lieferanten/wiederherstellen/<string:id>')
def restore_lieferant(id):

    database.lieferanten.restore_lieferant(sqlite_file, id)

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

@app.route('/eingangsrechnungen/pdfupload', methods = ['POST'])
def eingangsrechnungen_pdfupload():

    #: FIXME: sollte natuerlich auch fuer andere Dateien funktionieren
    uploaded_file = request.files['pdfdatei']
    if(uploaded_file):
        uploaded_file.save('dokumente/eingangsrechnungen/eingangsrechnung-' + str(request.form['id']) + '.pdf')

    return redirect(url_for('show_eingangsrechnungen'))

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
    settings = database.settings.load_settings()

    gesamtumsatz = 0
    gesamtgewinn = 0

    for rechnung in rechnungen:
        positionen = database.rechnungen.load_positionen(sqlite_file, rechnung['rechnungsnummer'])

        umsatz = 0
        rohgewinn = 0

        for pos in positionen:
            if(settings['ekpreis_berechnung'] == '1'):
                pos['ekpreis'] = database.wareneingang.load_last_ekpreis(sqlite_file, pos['artikel_id'])
            else:
                pos['ekpreis'] = database.wareneingang.load_median_ekpreis(sqlite_file, pos['artikel_id'])
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
    artikel = database.artikel.load_artikel(sqlite_file, True)
    positionen = database.rechnungen.load_positionen(sqlite_file, id)
    settings = database.settings.load_settings()

    for pos in positionen:
        pos['rabattpreis'] = pos['vkpreis'] - (pos['vkpreis'] / 100 * pos['rabatt'])


    gesamtpreis = 0

    for pos in positionen:
        gesamtpreis = gesamtpreis + (pos['rabattpreis'] * pos['anzahl'])

    rohgewinn = 0

    for pos in positionen:
        if(settings['ekpreis_berechnung'] == '1'):
            pos['ekpreis'] = database.wareneingang.load_last_ekpreis(sqlite_file, pos['artikel_id'])
        else:
            pos['ekpreis'] = database.wareneingang.load_median_ekpreis(sqlite_file, pos['artikel_id'])

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

    if(typ == 'gutschrift' and rechnung['kunden_id'] == -1):
        typ = 'bargutschrift'

    if(rechnung['kunden_id'] == -1 and typ == 'rechnung'):
        typ = 'barrechnung'

    if(typ == 'rechnung'):
        template = 'template-ausgangsrechnung'
        outfile = 'rechnung-'
        alte_rechnungs_id = 0
    elif(typ == 'gutschrift'):
        template = 'template-gutschrift'
        outfile = 'gutschrift-'
        alte_rechnungs_id = rechnung['storno_rechnungsnummer']
    elif(typ == 'barrechnung'):
        template = 'template-barverkaufsrechnung'
        outfile = 'barrechnung-'
        alte_rechnungs_id = 0
    elif(typ == 'bargutschrift'):
        template = 'template-bargutschrift'
        outfile = 'bargutschrift-'
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
        pos['ekpreis'] = database.wareneingang.load_median_ekpreis(sqlite_file, pos['artikel_id'])
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

    konten = database.konten.load_konten(sqlite_file, True)
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
            re = database.rechnungen.load_barrechnung(sqlite_file, buchung['ausgangsrechnungs_id'])
            if(buchung['einaus'] == 1):
                if(buchung['barverkaufsnummer'] == 0):
                    buchung['empfaenger'] = stammdaten['firmenname']
                    buchung['verwendungszweck'] = "Zahlung Ausgangsrechnung Nr. " + str(re['rechnungsnummer']) + " durch Kunde"
                else:
                    buchung['empfaenger'] = "Barkunde"
                    buchung['verwendungszweck'] = "Erloes aus Barverkaufsrechnung Nr. " + str(re['barverkaufsnummer'])
            else:
                if(re['kunden_id'] == -1):
                    buchung['empfaenger'] = "Bar-Erstattung an Kunde"
                else:
                    buchung['empfaenger'] = re['nachname'] + ', ' + re['vorname']
                if(buchung['barverkaufsnummer'] == 0):
                    buchung['verwendungszweck'] = "Erstattung Gutschrift " + str(re['rechnungsnummer']) + " an Kunde"
                else:
                    buchung['verwendungszweck'] = "Erstattung aus Barverkaufsrechnung Nr. " + str(re['barverkaufsnummer'])

        #: Eingangsrechnungen
        if(buchung['eingangsrechnungs_id'] != 0 and buchung['eingangsrechnungs_id'] != None):
            re = database.rechnungen.load_eingangsrechnung(sqlite_file, buchung['eingangsrechnungs_id'])
            li = database.lieferanten.load_lieferant(sqlite_file, re['lieferant_id'])
            buchung['empfaenger'] = li['firmenname']
            buchung['verwendungszweck'] = "Zahlung Eingangsrechnung Nr. " + str(re['rechnungsnummer'])
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

    page_title = "Kontoverwaltung"
    page_id = "konten"

    konten = database.konten.load_konten(sqlite_file)

    return render_template('konten.html', page_title = page_title, page_id = page_id, konten = konten)

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

@app.route('/konten/archivieren/<string:id>')
def konten_archivieren(id):

    database.konten.archive_konto(sqlite_file, id)

    return redirect(url_for('show_konten'))

@app.route('/konten/wiederherstellen/<string:id>')
def konten_wiederherstellen(id):

    database.konten.restore_konto(sqlite_file, id)

    return redirect(url_for('show_konten'))

@app.route('/briefe')
def show_briefe():

    page_id = "korrespondenz"
    page_title = "Briefe"

    briefe = database.korrespondenz.load_briefe(sqlite_file)

    for brief in briefe:
        if(brief['empfaenger_typ'] == 1):
            empfaenger = database.kunden.load_kunde(sqlite_file, brief['empfaenger_id'])
            brief['empfaenger'] = empfaenger
        else:
            empfaenger = database.lieferanten.load_lieferant(sqlite_file, brief['empfaenger_id'])
            brief['empfaenger'] = empfaenger

    return render_template('briefe.html', briefe = briefe, page_title = page_title, page_id = page_id)

@app.route('/briefe/neu')
def show_briefe_neu():

    page_id = "korrespondenz"
    page_title = "Neuen Brief schreiben"

    return render_template('briefe-neu.html', page_title = page_title, page_id = page_id)

@app.route('/briefe/bearbeiten/<string:id>')
def show_briefe_bearbeiten(id):

    page_id = "korrespondenz"
    page_title = "Brief bearbeiten"

    brief = database.korrespondenz.load_brief(sqlite_file, id)

    return render_template('briefe-bearbeiten.html', brief = brief, page_title = page_title, page_id = page_id)


@app.route('/briefe/speichern', methods = ['POST'])
def briefe_speichern():

    id = database.korrespondenz.save_brief(sqlite_file, request.form)

    return redirect('/briefe/ausgeben/' + str(id))

@app.route('/briefe/aktualisieren', methods = ['POST'])
def briefe_aktualisieren():

    database.korrespondenz.update_brief(sqlite_file, request.form)

    return redirect(url_for('show_briefe'))

@app.route('/briefe/archivieren/<string:id>')
def briefe_archivieren(id):

    database.korrespondenz.archive_brief(sqlite_file, id)

    return redirect(url_for('show_briefe'))

@app.route('/briefe/wiederherstellen/<string:id>')
def briefe_wiederherstellen(id):

    database.korrespondenz.restore_brief(sqlite_file, id)

    return redirect(url_for('show_briefe'))

@app.route('/briefe/ausgeben/<string:id>')
def show_briefe_ausgeben(id):

    page_id = "korrespondenz"
    page_title = "Brief ausgeben"

    brief = database.korrespondenz.load_brief(sqlite_file, id)

    return render_template('briefe-ausgeben.html', brief = brief, page_id = page_id, page_title = page_title)

@app.route('/briefe/ajax/empfaenger/<string:typ>')
def briefe_ajax_empfaenger(typ):

    if(typ == '1'):
        empfaenger = database.kunden.load_kunden(sqlite_file)
    else:
        empfaenger = database.lieferanten.load_lieferanten(sqlite_file)

    return json.dumps(empfaenger)

@app.route('/briefe/pdfrenderer/<string:action>/<string:id>')
def briefe_pdfrenderer(action, id):

    brief = database.korrespondenz.load_brief(sqlite_file, id)
    if(brief['empfaenger_typ'] == '1'):
        empfaenger = database.kunden.load_kunde(sqlite_file, brief['empfaenger_id'])
    else:
        empfaenger = database.lieferanten.load_lieferant(sqlite_file, brief['empfaenger_id'])

    brief['inhalt'] = brief['inhalt'].replace('\n', '<br />\n')

    stammdaten = database.settings.load_settings()

    bootstrap_css = ''

    f = file('assets/css/bootstrap.min.css', 'r')
    for line in f:
        bootstrap_css = bootstrap_css + line

    f.close()

    with open('assets/firmenlogo.png', 'rb') as logo:
        firmenlogo = base64.b64encode(logo.read())

    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('template-brief.html')
    out = template.render(bootstrap_css = bootstrap_css, firmenlogo = firmenlogo, brief = brief, empfaenger = empfaenger, stammdaten = stammdaten)
    pdf = pdfkit.from_string(out, False)

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    if(action == 'speichern'):
        response.headers['Content-Disposition'] = 'attachment; filename=brief-' + id + '.pdf'

    if(action == 'drucken'):
        response.headers['Content-Disposition'] = 'inline; filename=brief-' + id + '.pdf'

    return response

@app.route('/privatentnahmen')
def show_privatentnahmen():

    page_id = "privatentnahmen"
    page_title = "Privatentnahmen und Werbegeschenke"

    privatentnahmen = database.privatentnahmen.load_privatentnahmen(sqlite_file)
    artikelstamm = database.artikel.load_artikel(sqlite_file, False)

    gesamtwert = 0

    for pe in privatentnahmen:
        artikel = database.artikel.load_single_artikel(sqlite_file, pe['artikel_id'])
        pe['artikelbezeichnung'] = artikel['artikelbezeichnung']
        median_ekpreis = database.wareneingang.load_median_ekpreis(sqlite_file, pe['artikel_id'])
        pe['warenwert'] = median_ekpreis * pe['anzahl']
        gesamtwert = gesamtwert + (median_ekpreis * pe['anzahl'])

    return render_template('privatentnahmen.html', privatentnahmen = privatentnahmen, artikel = artikelstamm, gesamtwert = gesamtwert, page_id = page_id, page_title = page_title)

@app.route('/privatentnahmen/speichern', methods = ['POST'])
def privatentnahmen_speichern():

    database.privatentnahmen.save_privatentnahmen(sqlite_file, request.form)

    return redirect(url_for('show_privatentnahmen'))

@app.route('/barverkauf')
def show_barverkauf():

    page_id = "barverkauf"
    page_title = "Barverkauf"

    artikel = database.artikel.load_artikel(sqlite_file, True)

    ts = time.time()

    return render_template('barverkauf.html', ts = ts, gesamtsumme = 0, artikel = artikel, page_id = page_id, page_title = page_title)

@app.route('/barverkauf/starten')
def barverkauf_starten():

    bon_id = database.barverkauf.start_barverkauf(sqlite_file)

    result = { 'bon_id': bon_id }

    return json.dumps(result)

@app.route('/barverkauf/ajax/artikel', methods = ['POST'])
def barverkauf_ajax_artikel():

    artikel = database.artikel.load_artikel_by_ean(sqlite_file, request.form['ean'])

    return json.dumps(artikel)

@app.route('/barverkauf/position/neu', methods = ['POST'])
def barverkauf_position_neu():

    page_id = "barverkauf"
    page_title = "Barverkauf"

    bon_id = request.form['bon_id']

    gesamtrabatt = 0
    gesamtsumme = 0

    database.barverkauf.save_position(sqlite_file, request.form)

    positionen = database.barverkauf.load_positionen(sqlite_file, bon_id)

    for pos in positionen:
        art = database.artikel.load_single_artikel(sqlite_file, pos['artikel_id'])
        pos['vkpreis'] = art['vkpreis']
        pos['artikelbezeichnung'] = art['artikelbezeichnung']
        gesamtsumme += (pos['vkpreis'] * pos['anzahl'])
        if(pos['anzahl'] >= art['bestand']):
            pos['bestandswarnung'] = True
        else:
            pos['bestandswarnung'] = False

    artikel = database.artikel.load_artikel(sqlite_file)

    ts = time.time()

    return render_template('barverkauf.html', ts = ts, artikel = artikel, positionen = positionen, gesamtrabatt = gesamtrabatt, gesamtsumme = gesamtsumme, bon_id = bon_id, page_id = page_id, page_title = page_title)

@app.route('/barverkauf/position/aendern', methods = ['POST'])
def barverkauf_position_aendern():

    page_id = "barverkauf"
    page_title = "Barverkauf"

    bon_id = request.form['pa_bon_id']

    gesamtrabatt = 0
    gesamtsumme = 0

    database.barverkauf.update_position(sqlite_file, request.form)

    positionen = database.barverkauf.load_positionen(sqlite_file, bon_id)

    for pos in positionen:
        art = database.artikel.load_single_artikel(sqlite_file, pos['artikel_id'])
        pos['vkpreis'] = art['vkpreis']
        pos['artikelbezeichnung'] = art['artikelbezeichnung']
        gesamtsumme += (pos['vkpreis'] * pos['anzahl'])
        if(pos['anzahl'] >= art['bestand']):
            pos['bestandswarnung'] = True
        else:
            pos['bestandswarnung'] = False

    artikel = database.artikel.load_artikel(sqlite_file)

    ts = time.time()

    return render_template('barverkauf.html', ts = ts, artikel = artikel, positionen = positionen, gesamtrabatt = gesamtrabatt, gesamtsumme = gesamtsumme, bon_id = bon_id, page_id = page_id, page_title = page_title)

@app.route('/barverkauf/position/loeschen', methods = ['POST'])
def barverkauf_position_loeschen():

    page_id = "barverkauf"
    page_title = "Barverkauf"

    bon_id = request.form['lo_bon_id']

    gesamtrabatt = 0
    gesamtsumme = 0

    database.barverkauf.delete_position(sqlite_file, request.form)

    positionen = database.barverkauf.load_positionen(sqlite_file, bon_id)

    for pos in positionen:
        art = database.artikel.load_single_artikel(sqlite_file, pos['artikel_id'])
        pos['vkpreis'] = art['vkpreis']
        pos['artikelbezeichnung'] = art['artikelbezeichnung']
        gesamtsumme += (pos['vkpreis'] * pos['anzahl'])
        if(pos['anzahl'] >= art['bestand']):
            pos['bestandswarnung'] = True
        else:
            pos['bestandswarnung'] = False

    artikel = database.artikel.load_artikel(sqlite_file)

    ts = time.time()

    return render_template('barverkauf.html', artikel = artikel, ts = ts, positionen = positionen, gesamtrabatt = gesamtrabatt, gesamtsumme = gesamtsumme, bon_id = bon_id, page_id = page_id, page_title = page_title)

@app.route('/barverkauf/abbrechen/<string:id>')
def barverkauf_abbrechen(id):

    database.barverkauf.barverkauf_abbrechen(sqlite_file, id)

    return redirect(url_for('show_barverkauf'))

@app.route('/barverkauf/ajax/abschliessen', methods = ['POST'])
def barverkauf_ajax_abschliessen():

    result = database.barverkauf.barverkauf_abschliessen(sqlite_file, request.form)

    return json.dumps(result)

@app.route('/barverkauf/pdfrenderer/<string:id>')
def barverkauf_pdfrenderer(id):

    rechnung = database.rechnungen.load_barrechnung(sqlite_file, id)
    positionen = database.rechnungen.load_positionen(sqlite_file, id)
    stammdaten = database.settings.load_settings()

    gesamtsumme = 0

    for pos in positionen:
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
    template = env.get_template('template-barverkaufsrechnung.html')
    out = template.render(bootstrap_css = bootstrap_css, firmenlogo = firmenlogo, rechnung = rechnung, positionen = positionen, stammdaten = stammdaten, gesamtsumme = gesamtsumme, mwst = mwst)
    pdf = pdfkit.from_string(out, False)

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=barverkaufsrechnung' + id + '.pdf'

    return response

if __name__ == '__main__':
	app.run(debug = debug, host = bind_host, port = bind_port)
