# Fountain project
#
# alert_monitor.py - handle alerts via email
#

import logging
import sys

import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import yaml


class AlertMonitor:
    """Handle fountain alert operations"""

    def __init__(self, fountain):
        self.fountain = fountain

    def test(self):

        ymlfile = open("fountain.yml", 'r')
        cfg = yaml.safe_load(ymlfile)
        emailConfig = cfg['email']
 
        sender_email = emailConfig['sender_email']
        receiver_email = emailConfig['receiver_email']

        host = emailConfig['host']
        port = emailConfig['port']
        login = emailConfig['login']
        password = emailConfig['password']


        message = MIMEMultipart()
        message["Subject"] = "Yukon Fountain alert"
        message["From"] = sender_email
        message["To"] = receiver_email

        html = """\
        <html>
        <body>
            <p>Fountain alert:<br>
            TODO: Put alert info here<br>
            <a href="http://rpitest.local">Fountain Status</a> 
            </p>
        </body>
        </html>
        """

        part1 = MIMEText(html, "html")
        message.attach(part1)
        
        try:
            # Create secure connection with server and send email
            context = ssl.create_default_context()
            server = smtplib.SMTP_SSL(host, port, context=context)
            server.login(login, password)
            server.sendmail(
                sender_email, receiver_email, message.as_string()
            )
            server.close()
            logging.info('Email sent!')
        except:
            e = sys.exc_info()[0]
            logging.error('Something went wrong with email...' + str(e))