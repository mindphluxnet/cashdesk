import sqlite3

def load_artikel(sqlite_file, id):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("SELECT * FROM artikel WHERE id = ?", id)
    artikel = c.fetchone()

    conn.close()

    return artikel
