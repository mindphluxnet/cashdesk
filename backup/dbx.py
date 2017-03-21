import dropbox
import database.settings
import datetime
import pyminizip
import os

def compress_backup(filename, password):

    pyminizip.compress(filename, 'tmp.zip', password, 9)

def run_backup(filename):

    settings = database.settings.load_settings()

    apikey = settings['dropbox_api_key']

    dbx = dropbox.Dropbox(apikey)

    compress_backup(filename, settings['backup_passwort'])

    fname = filename + '-' + '{:%Y-%m-%d-%H:%M:%S}'.format(datetime.datetime.now())
    fname = fname + '.zip'

    with open('tmp.zip', 'rb') as f:
        dbx.files_upload(f.read(), '/cashdesk-backups/' + fname)

    os.remove('tmp.zip')

def list_backups():

    settings = database.settings.load_settings()

    apikey = settings['dropbox_api_key']

    dbx = dropbox.Dropbox(apikey)

    try:
        backups = dbx.files_list_folder('/cashdesk-backups')
    except Exception:
        pass

    return backups
