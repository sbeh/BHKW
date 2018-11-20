#!/usr/bin/python

# Kann mehrere TCP-Verbindungen akzeptieren
# Leitet alle ueber TCP reinkommendenen Daten an dispad.py weiter (Forward)
# Leitet alle von dispad.py reinkommendenen Daten an alle TCP-Verbindungen weiter (Broadcast)

FIFO_TO_DISPAD    = '/var/tmp/fifo1'       # tcp -> dispad
FIFO_FROM_DISPAD  = '/var/tmp/dispad->tcp' # dispad -> tcp

TCP_HOST = ''
TCP_PORT = 1234

# ---

import os

from util import debug

# ---

class DispadUnavailable(Exception):
    pass

def dispadTrySend(data):
    try:
        with open(FIFO_TO_DISPAD, 'a', 0) as file:
            file.write(data)
    except StandardError as e:
        debug('TCP->DISPAD: Fehler beim Schreiben in {}: {}'.format(FIFO_TO_DISPAD, e))
        raise DispadUnavailable()

# ---

clients = []

def clientDisconnect(client):
    debug('CLIENT-{}: Trenne Verbindung'.format(clients.index(client)))
    try:
        client.shutdown(socket.SHUT_RDWR)
    except:
        pass # Ignoriere alles was schief gehen kann
    try:
        client.close()
    except:
        pass # Ignoriere alles was schief gehen kann
    clients.remove(client)

def clientSendOrDisconnect(client, data):
    try:
        client.sendall(data)
    except StandardError as error:
        debug('CLIENT-{}: Fehler beim Zusenden von Daten: {}'.format(clients.index(client), error))
        clientDisconnect(client)

def clientsBroadcastOrClientDisconnect(data):
    for client in clients:
        clientSendOrDisconnect(client, data)

class ClientDisconnected(Exception):
    pass

def clientRecvOrDisconnect(client):
    try:
        data = client.recv(2048)
        if data:
            return data
    except StandardError as error:
        debug('CLIENT-{}: Fehler beim Empfangen von Daten: {}'.format(clients.index(client), error))
    # Client hat Verbindung geschlossen oder die Verbindung ist Abgebrochen -> Trenne Verbindung
    clientDisconnect(client)
    raise ClientDisconnected()

# ---

def fifoSetup():
    if not os.path.exists(FIFO_FROM_DISPAD):
        os.mkfifo(FIFO_FROM_DISPAD)
    return os.open(FIFO_FROM_DISPAD, os.O_RDWR) # FIX O_RDWR to avoid EOF on FIFO, tcp.py will not write to it

import atexit
@atexit.register
def fifoCleanup():
    try:
        os.unlink(FIFO_FROM_DISPAD)
    except:
        pass

# ---

def main_loop():
    if not os.path.exists(FIFO_TO_DISPAD):
        print('Warte auf Dispad...')
    while not os.path.exists(FIFO_TO_DISPAD):
        time.sleep(0.1)

    dispad = fifoSetup()

    import socket
    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # FIX socket.error: [Errno 98] Address already in use
    tcp.bind((TCP_HOST, TCP_PORT))
    tcp.listen(0)
    print('TCP: Warte auf neue Verbindungen an {}:{}'.format(TCP_HOST, TCP_PORT))

    while True:
        from select import select
        check = select([dispad, tcp] + clients, [], [])[0]
        for c in check:
            if c == dispad: # Dispad hat Daten gesendet -> Broadcast an alle TCP Clients
                data = os.read(dispad, 2048)
                debug('DISPAD->TCP->CLIENTS: {}'.format(data))
                clientsBroadcastOrClientDisconnect(data)
            elif c == tcp: # Neue Verbindung: Akzeptiere und fuege Client zur Liste hinzu
                client, (host, _) = tcp.accept()
                clients.append(client)
                debug('CLIENT-{}: Verbunden von {}'.format(clients.index(client), host))
            else: # Client braucht aufmerksamkeit
                client = c
                try:
                    data = clientRecvOrDisconnect(client)
                    # Client hat Daten gesendet -> Weiterleitung and Dispad
                    debug('CLIENT-{}->DISPAD: {}'.format(clients.index(client), data))
                    try:
                        dispadTrySend(data)
                    except DispadUnavailable:
                        data = 'DATA IGNORED, DISPAD UNAVAILABLE\n'
                        debug('TCP->CLIENTS: {}'.format(data))
                        clientsBroadcastOrClientDisconnect(data)
                except ClientDisconnected:
                    pass

try:
    main_loop()
except KeyboardInterrupt:
    pass