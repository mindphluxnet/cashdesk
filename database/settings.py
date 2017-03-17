import sqlite3
import pickle

import database.factory

def save_settings(settings):

    with open('settings.pickle', 'wb') as settingsfile:
        pickle.dump(settings, settingsfile, protocol=pickle.HIGHEST_PROTOCOL)

def load_settings():

    einstellungen = []

    try:
        with open('settings.pickle', 'rb') as settingsfile:
            einstellungen = pickle.load(settingsfile)
            #: fix integers

    except Exception:
        pass

    return einstellungen
