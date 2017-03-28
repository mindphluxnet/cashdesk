# Cashdesk

Eine extrem schlanke Faktura in Python, hauptsächlich für den Einsatz auf einem
Raspberry Pi (3) konzipiert.

# Geplante Features

- Komplette Faktura mit Ein- und Ausgangsrechnungen, Artikel- und Kundenverwaltung, Kassenbuch
- alle Daten in einer SQLite-Datenbank für einfachen Austausch
- Bedienung vollständig im Browser (Bootstrap, jQuery)
- Ausgabe/Druck von Rechnungen als PDF mit eigenem Layout aus HTML-Template

# Abhängigkeiten installieren

```
sudo apt-get install wkhtmltopdf
```

# Installation

```
git clone https://github.com/mindphluxnet/cashdesk
cd cashdesk
sudo pip install -r requirements.txt
```

# Programmstart

```
./cashdesk.py
```

Sobald das Programm läuft, kann die Oberfläche im Browser unter der URL

```
http://localhost:5000
```

geöffnet werden.

# Fremder Code

- UUID-Generator in Javascript von Jeff Ward (http://jcward.com/UUID.js)
- Font Awesome by Dave Gandy - http://fontawesome.io
- Bootstrap - http://getbootstrap.com
- jQuery - http://jquery.com
