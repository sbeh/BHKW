# -*- coding: utf-8 -*-
# rw.py stdin + fifo1 zu dispa.py
# fifos werden vom Leser erzeugt und geloescht!!
# Lesezugriffe alle 100ms duerften keinen SD-Card verschleiss erzeugen
import os
import atexit
import sys
import select
import io
import datetime
import time
time.sleep(1)		# genug Zeit bis dispad oben ist

FIFO1 = '/var/tmp/fifo1'   # rw to dispad - 
FIFO2 = '/var/tmp/fifo2'   # dispad to rw
read_list = [sys.stdin]      # multiple files monitored for input
timeout = 0.1                   # select()  wait secs for input. ausreichend fuer eine Zeile

def fifo_reader(fifo):        # dispad abhören          
    global line
    try:                                # hat einer fifo1 geloescht ...
        line = os.read(fifo, 100)
        if line:
           time.sleep(0.05)           # vielleicht kommt nochwas?
           line += os.read(fifo, 100)
    except OSError:
        pass                          # um mir zu sagen, Selbstmord
    if line:
        sys.stdout.write(line)  # stdout-Ausgabe ohne \n\r
        sys.stdout.flush()      # sofort anzeigen
        if line.find('RA_TI')>=0:
           today = datetime.datetime.today()
           sys.stdout.write("TI_")  # stdout-Ausgabe ohne \n\r
           print today              # Ausgabe -> Terminal
           fifo1_writer("TI_"+str(today)) # Ausgabe -> dispad -> Funk

def fifo1_writer(linein):      # dispad versorgen
    if os.path.exists(FIFO1):   # wenn dispad laeuft?
        with open(FIFO1, 'w',0) as fifo1:   # unbuffered oeffnen
            fifo1.write(linein)  # wegschreiben

@atexit.register
def cleanup():
    try:
        os.unlink(FIFO2)        # Lesefifo loeschen
    except:
        pass

def main():
    global read_list
    print("Dialog  gestartet mit: BM_Werte ...")
    today = datetime.datetime.today()
    print today
    if os.path.exists(FIFO2):os.remove(FIFO2)	# ggf. vorher löschen
    os.mkfifo(FIFO2)				# FIFO erstellen
    fifo2 = os.open(FIFO2, os.O_RDONLY | os.O_NONBLOCK)
    fifo1_writer("BM_Werte\n")
    while read_list:                        # alle 0.2s
        ready = select.select(read_list, [], [], timeout)[0]    # stdin abfragen \n - terminiert
        if ready:   
            for file in ready:              # ansonsten stdin-Eingabe abarbeiten
                line = file.readline()
                if line:
                    fifo1_writer(line)      # rw -> dispad
                if line.find('RA_TI')>=0:
                   today = datetime.datetime.today()
                   print today              # Ausgabe -> raspi
                   fifo1_writer(str(today)) # Ausgabe -> dispad -> Funk
        fifo_reader(fifo2)               # dispad -> rw  Antwort einen Zyklus spaeter abholen

try:
    main()
except KeyboardInterrupt:
    pass
