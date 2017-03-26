import sqlite3

import database.factory

def load_briefe(sqlite_file):

    conn = sqlite3.connect(sqlite_file)
    conn.row_factory = database.factory.dict_factory
    c = conn.cursor()

    c.execute("SELECT oid, * FROM briefe ORDER BY datum DESC")
    briefe = c.fetchall()

    conn.close()

    return briefe

def save_brief(sqlite_file, brief):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("INSERT INTO briefe (empfaenger_typ, empfaenger_id, datum, betreff, zuhaenden, inhalt) VALUES (?, ?, ?, ?, ?, ?)", [ brief['empfaenger_typ'], brief['empfaenger_id'], brief['datum'], brief['betreff'], brief['zuhaenden'], brief['inhalt'] ])

    conn.commit()
    conn.close()

    return c.lastrowid

def load_brief(sqlite_file, id):

    conn = sqlite3.connect(sqlite_file)
    conn.row_factory = database.factory.dict_factory
    c = conn.cursor()

    c.execute("SELECT oid, * FROM briefe WHERE oid = ?", [ id ])
    brief = c.fetchone()

    conn.close()

    return brief
