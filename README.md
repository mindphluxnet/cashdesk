# Cashdesk

Eine extrem schlanke Faktura in Python, hauptsächlich für den Einsatz auf einem
Raspberry Pi (3) konzipiert. Die Software richtet sich speziell an Kleinunternehmer nach §19 Abs. 1 UStG.

# Features

- vollständige Faktura mit Vollwarenwirtschaft, Ein- und Ausgangsrechnungen, Kunden- und Lieferantenstamm
- Barverkauf mit Unterstützung von Barcode-Scanner (noch nicht implementiert)
- alle Daten in einer SQLite-Datenbank für einfachen Austausch
- Bedienung vollständig im Browser (Bootstrap, jQuery)
- Ausgabe/Druck von Rechnungen als PDF mit eigenem Layout aus HTML-Template
- Raspberry Pi: Unterstützung von LCD-Display für Barverkauf (noch nicht implementiert)

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

geöffnet werden. Wenn der Debugmodus deaktiviert ist, wird automatisch
ein neues Tab/Fenster geöffnet.

# Fremder Code

- UUID-Generator in Javascript von Jeff Ward (http://jcward.com/UUID.js)
- Font Awesome by Dave Gandy - http://fontawesome.io
- Bootstrap - http://getbootstrap.com
- jQuery - http://jquery.com

# Bilder

- Euro-Bargeld: Wikipedia
- EC- und Kreditkarten: Offizielle Website der Sparkassen
