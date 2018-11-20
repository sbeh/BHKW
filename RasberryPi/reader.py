# reader.py
import os
import sys
import atexit
import time

FIFO = '/var/tmp/fifo3'

@atexit.register
def cleanup():
    try:
        os.unlink(FIFO)
    except:
        pass
    
def main():
    print("Logging Reader gestartet")
    if os.path.exists(FIFO):
        os.remove(FIFO)
    os.mkfifo(FIFO)
    fifo = os.open(FIFO, os.O_RDONLY | os.O_NONBLOCK)
    while True:
        try:
            line = os.read(fifo, 100)
        except OSError:
            print "OSError bei Lesen von fifo3 - warte 1s"
            time.sleep(1)
        time.sleep(0.1)
        if line:
            sys.stdout.write(line)  # stdout-Ausgabe ohne \n\r
            sys.stdout.flush()      # sofort anzeigen

try:
    main()
except KeyboardInterrupt:
    pass
