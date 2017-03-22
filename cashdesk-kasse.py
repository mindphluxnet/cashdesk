#!/usr/bin/env python

#: cashdesk-kasse
#: ein minimales kassenprogramm fuer cashdesk
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
bind_port = 5050
dbversion = 1

app = Flask(__name__, static_url_path = '', template_folder = 'templates-kasse')

database.setup.setup_database(sqlite_file)
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

if(debug == False):
    webbrowser.open(('http://' + bind_host + ':' + str(bind_port)))

@app.route('/assets/<path:path>')
def serve_asset(path):
        return send_from_directory('assets', path)

@app.route('/')
def show_index():

    artikel = database.artikel.load_artikel(sqlite_file)

    return render_template('index.html', artikel = artikel)

@app.route('/ajax/artikel/byean', methods = ['POST'])
def ajax_artikel_byean():

    artikel = database.artikel.load_artikel_by_ean(sqlite_file, request.form['ean'])

    return json.dumps(artikel)

@app.route('/ajax/artikel/byid', methods = ['POST'])
def ajax_artikel_byid():

    artikel = database.artikel.load_single_artikel(sqlite_file, request.form['id'])

    return json.dumps(artikel)

if __name__ == '__main__':
	app.run(debug = debug, host = bind_host, port = bind_port)
