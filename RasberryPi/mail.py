# Aufruf von der console: z.B. python ./mail.py 5 20

import subprocess
import smtplib
import socket
import datetime
import sys
from email.mime.text import MIMEText

# Accountinformationen zum Senden der E-Mail
Empfaenger1 = 'a@b.c'
Empfaenger2 = 'b@b.c'
Absender = 'c@b.c'
Passwort = '******'                               # Passwort noch eintragen
smtpserver = smtplib.SMTP('smtp.web.de', 587)
smtpserver.ehlo()
smtpserver.starttls()
smtpserver.ehlo

smtpserver.login(Absender, Passwort)
Datum = datetime.datetime.today()
Wert = str(sys.argv[1])
msg = MIMEText(Wert)
msg['Subject'] = 'Hausalarm - %s' % Datum.strftime('%H:%M:%S %d. %b %Y')
#msg['From'] = Absender
msg['To'] =  '%s,%s ' %(Empfaenger1,Empfaenger2)
smtpserver.sendmail(Absender, [Empfaenger1,Empfaenger2], msg.as_string())
smtpserver.quit()
