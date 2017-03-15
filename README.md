# Cashdesk

Eine extrem schlanke Faktura in Python, hauptsächlich für den Einsatz auf einem 
Raspberry Pi (3) konzipiert. 

# Geplante Features

- Komplette Faktura mit Ein- und Ausgangsrechnungen, Artikel- und Kundenverwaltung, Kassenbuch
- alle Daten in einer SQLite-Datenbank für einfachen Austausch
- Kassenmodul mit Ansteuerung von LCD-Display und Bondrucker
- Bedienung vollständig im Browser (Bootstrap, jQuery)
- Ausgabe/Druck von Rechnungen als PDF mit eigenem Layout aus HTML-Template

# Installation

```
sudo pip install -r requirements.txt
git clone https://github.com/mindphluxnet/cashdesk
cd cashdesk
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

Hinweis: diese Software befindet sich im frühen Entwicklungsstadium. Sie ist
aktuell nicht besonders funktionsfähig.


