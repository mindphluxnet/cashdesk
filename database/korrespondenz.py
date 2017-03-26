import sqlite3

import database.factory

def load_briefe(sqlite_file):

    conn = sqlite3.connect(sqlite_file)
    conn.row_factory = database.factory.dict_factory
    c = conn.cursor()

    c.execute("SELECT oid, * FROM briefe ORDER BY datum ASC")
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

def update_brief(sqlite_file, brief):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("UPDATE briefe SET empfaenger_typ = ?, empfaenger_id = ?, datum = ?, betreff = ?, zuhaenden = ?, inhalt = ? WHERE oid = ?", [ brief['empfaenger_typ'], brief['empfaenger_id'], brief['datum'], brief['betreff'], brief['zuhaenden'], brief['inhalt'], brief['id'] ])

    conn.commit()
    conn.close()

def delete_brief(sqlite_file, id):

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("DELETE FROM briefe WHERE oid = ?", [ id ])

    conn.commit()
    conn.close()

def load_brief(sqlite_file, id):

    conn = sqlite3.connect(sqlite_file)
    conn.row_factory = database.factory.dict_factory
    c = conn.cursor()

    c.execute("SELECT oid, * FROM briefe WHERE oid = ?", [ id ])
    brief = c.fetchone()

    conn.close()

    return brief
