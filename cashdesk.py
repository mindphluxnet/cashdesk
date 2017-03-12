#: cashdesk
#: ein minimales fakturierungsprogramm
#: Copyright 2017, Richard Kaemmerer <richard@richardkaemmerer.de>

from flask import Flask, render_template, send_from_directory
import sqlite3
import dateutil.parser
from path import Path
import time

#: eigene importe

import database.setup

sqlite_file = "cashdesk.sqlite"

database.setup.setup_database(sqlite_file)
