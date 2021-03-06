import dropbox
import database.settings
import datetime
import pyminizip
import os

def compress_backup(filename, password, dbversion):

    with file("dbver", 'w') as f:
        f.write(str(dbversion))

    pyminizip.compress_multiple( [ filename, 'dbver'], 'tmp.zip', password, 9)

    os.remove('dbver')

def run_backup(filename, dbversion):

    prune_backups()

    settings = database.settings.load_settings()

    apikey = settings['dropbox_api_key']

    dbx = dropbox.Dropbox(apikey)

    compress_backup(filename, settings['backup_passwort'], dbversion)

    fname = 'backup-' + '{:%Y-%m-%d-%H:%M:%S}'.format(datetime.datetime.now())
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

def prune_backups():

    settings = database.settings.load_settings()

    backups = list_backups()

    apikey = settings['dropbox_api_key']
    max_backups = int(settings['max_backups'])

    dbx = dropbox.Dropbox(apikey)

    backups = backups.entries[::-1]

    for idx, b in enumerate(backups):
        if(idx >= max_backups):
            dbx.files_delete('/cashdesk-backups/' + b.name)
