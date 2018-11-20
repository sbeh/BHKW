#! /usr/bin/python
# -*- coding: utf-8 -*-
"""Check for input. Treat available input or do other stuff"""
# Daemon-Variante von dispa ohne stdin
# fifo und serial port polling
import sys
import time
import serial
import io
import subprocess
import os
import atexit

FIFO1 = '/var/tmp/fifo1'       # pipo -> dispad
FIFO2 = '/var/tmp/fifo2'       # dispad -> pipo
FIFO3 = '/var/tmp/fifo3'       # dispad -> logging reader

def kontrolliere():
    ip=ser.read(100)          # ganze Zeile lesen
    if ip:                               # keine unnoetige Zugriffe
        time.sleep(0.05)        # vielleicht kommt nochwas?
        ip += ser.read(100)                            # bis Ende lesen 
        if  os.path.exists(FIFO2):                   # hoert jemand zu?                         
            with open(FIFO2, 'a',0) as fifo2:    # unbuffered
                fifo2.write(ip)                              # serial -> fifo
        if  os.path.exists(FIFO3):                   # hoert jemand zu?                         
            with open(FIFO3, 'a',0) as fifo3:    # unbuffered
                fifo3.write(ip)                              # serial -> fifo
    if ip.find('ALARM')>=0:
        subprocess.call("python /home/pi/Desktop/Mail/mail.py %s" % (ip[:ip.find('\r')]) ,shell=True)
        print("Email verschickt")

@atexit.register
def cleanup():
    try:
        os.unlink(FIFO1)
    except:
        pass

def main_loop():
    global ser
    print("Dispad gestartet")
    if os.path.exists(FIFO1):               # Leiche ggf. loeschen
        os.remove(FIFO1)
    if os.path.exists(FIFO2):               # Leiche ggf. loeschen
        os.remove(FIFO2)
    if os.path.exists(FIFO3):               # Leiche ggf. loeschen
        os.remove(FIFO3)
    os.mkfifo(FIFO1)
    ser = serial.Serial('/dev/ttyAMA0', timeout=0, baudrate=9600, bytesize=8, stopbits=1)
    fifo1 = os.open(FIFO1, os.O_RDONLY | os.O_NONBLOCK)
    while True:
        ser.write(os.read(fifo1, 32)) # fifo -> serial
        time.sleep(0.1)
        kontrolliere()    # serial -> fifo und Alarmfilter
    ser.close()    

try:
    main_loop()
except KeyboardInterrupt:
    pass
