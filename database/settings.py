import sqlite3

def save_settings(sqlite_file, settings):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()


    conn.commit()
    conn.close()
