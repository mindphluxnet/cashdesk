#: from http://stackoverflow.com/questions/811548/sqlite-and-python-return-a-dictionary-using-fetchone
def dict_factory(cursor, row):
    d = {}
    for idx,col in enumerate(cursor.description):
        d[col[0]] = row[idx]

    return d
