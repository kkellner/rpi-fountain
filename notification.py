# Fountain project
#
# notification.py - handle notification via email
#

import logging
import sys
import threading

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import yaml

from water_level import WaterLevel, WaterLevelState

logger = logging.getLogger('notification')


class Notification:
    """Handle fountain notification operations"""

    def __init__(self, fountain):
        self.fountain = fountain
        fountain.water_level.add_state_change_notify(
            self.notify_water_level_state_change_callback)

        ymlfile = open("config.yml", 'r')
        cfg = yaml.safe_load(ymlfile)
        emailConfig = cfg['email']

        self.sender_email = emailConfig['sender_email']
        self.receiver_email = emailConfig['receiver_email']

        self.host = emailConfig['host']
        self.port = emailConfig['port']
        self.login = emailConfig['login']
        self.password = emailConfig['password']

        # TODO: Testing
        #self.send_water_level_state_change_email(WaterLevelState.OK, WaterLevelState.OK)


    def notify_water_level_state_change_callback(self, waterLevel, oldState, newState):
        logger.debug("email notification callback." +
                     " oldState:" + str(oldState) +
                     " newState:"+str(newState) +
                     " waterLevelPct:" + str(waterLevel.get_percent_full()))
        #self.send_water_level_state_change_email(oldState, newState)

    def send_water_level_state_change_email(self, oldState, newState):

        if (oldState is WaterLevelState.UNKNOWN or newState is WaterLevelState.UNKNOWN):
            # We don't want to notify on UNKNOWN state changes
            return

        waterPercentFull = self.fountain.water_level.get_percent_full()
        waterDepthInches = self.fountain.water_level.get_depth_inches()

        subject = "Fountain Notify - Water Level State: " + str(newState.name)
        bodyTemplate = """\
        <html>
        <body>
            <p>
                <h1>Water fountain notification</h1>
                Water Level: <span style='font-weight: bold;'>%s</span><br/>
                <br/>
                Details:<br/>
                waterPercentFull: %.1f<br/>
                waterDepth: %.1f<br/>
                Old Water Level: %s<br/>

                <a href="http://rpitest.local">Fountain Status</a> 
            </p>
        </body>
        </html>
        """

        bodyHtml = bodyTemplate % (
            newState.name, waterPercentFull, waterDepthInches, oldState.name)

        self.send_email(subject, bodyHtml)

    def send_email(self, subject, bodyHtml):
        thread = threading.Thread(
            target=self.__send_email_blocking, args=[subject, bodyHtml])
        thread.daemon = True
        thread.start()

    def __send_email_blocking(self, subject, bodyHtml):

        message = MIMEMultipart()
        message["From"] = self.sender_email
        message["To"] = self.receiver_email
        message["Subject"] = subject

        part1 = MIMEText(bodyHtml, "html")
        message.attach(part1)

        try:
            # Create secure connection with server and send email
            context = ssl.create_default_context()
            server = smtplib.SMTP_SSL(self.host, self.port, context=context)
            server.login(self.login, self.password)
            server.sendmail(
                self.sender_email, self.receiver_email, message.as_string()
            )
            server.close()
            logger.info('Email sent!')
        except:
            #e = sys.exc_info()
            logger.exception('Something went wrong with email...')
