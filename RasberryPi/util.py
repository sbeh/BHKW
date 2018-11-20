from re import sub
from time import strftime

DEBUG = True

def debug(message):
    if DEBUG:
        print(
            strftime('%A, %H:%M, ') + # Montag, 09:00,
            sub(r'[^ !"#$%&\'()*+,-./0-9:;<=>?@`A-Z\[\\\]^_`a-z{|}~]', '.', message) # Ersetzt unerwuenschte Zeichen durch Punkt
        )