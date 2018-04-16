#!/usr/bin/env python3

import logging
import smtplib

from email.header import Header
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from mosquito.settings import MosquitoSettings


class MosquitoMail(object):
    
    def __init__(self, id=None, queue=None):
        self.id = id
        self.queue = queue

        self.logger = logging.getLogger('[MAIL]')
        self.settings = MosquitoSettings()
        self.server = None
        self.status = False

        if self.settings.smtp_usessl:
            try:
                self.server = smtplib.SMTP_SSL(self.settings.smtp_server, self.settings.smtp_port)

                self._logger(
                    "debug",
                    "SSL connection has been established: {}:{}".format(
                        self.settings.smtp_server, self.settings.smtp_port
                    )
                )
            except smtplib.ssl.SSLError:
                try:
                    self.server = smtplib.SMTP(self.settings.smtp_server, self.settings.smtp_port)
                    self.server.starttls()

                    self._logger(
                        "debug",
                        "STARTTLS connection has been established: {}:{}".format(
                            self.settings.smtp_server, self.settings.smtp_port
                        )
                    )
                except Exception:
                    self._logger(
                        "warning",
                        "Cannot establish SSL connection to the SMTP server: {}:{}".format(
                            self.settings.smtp_server, self.settings.smtp_port
                        )
                    )
            except Exception:
                self._logger(
                    "warning",
                    "Cannot establish connection to SMTP server: {}:{}".format(
                        self.settings.smtp_server, self.settings.smtp_port
                    )
                )
        else:
            try:
                self.server = smtplib.SMTP(self.settings.smtp_server, self.settings.smtp_port)

            except Exception:
                self._logger(
                    "warning",
                    "Cannot establish plain connection to SMTP server: {}:{}".format(
                        self.settings.smtp_server,self.settings.smtp_port
                    )
                )

        if self.server:
            if self.settings.smtp_auth:
                try:
                    self.server.login(self.settings.smtp_username, self.settings.smtp_password)

                    self.status = True

                    self._logger(
                        "debug",
                        "Authentification has been passed: {}:{}".format(
                            self.settings.smtp_server, self.settings.smtp_port
                        )
                    )

                except Exception as error:
                    self._logger(
                        "warning",
                        "Cannot authenticate on SMTP server: {}:{} -> {}".format(
                            self.settings.smtp_server, self.settings.smtp_port, error
                        )
                    )

    def _logger(self, level, message):
        if self.id and self.queue:

            self.queue.put([
                self.id,
                level,
                message
            ])
        else:
            if level == "debug":
                self.logger.debug(message)
            elif level == "error":
                self.logger.error(message)
            elif level == "info":
                self.logger.info(message)
            elif level == "warning":
                self.logger.warning(message)

    def send(self, email, headers, priority, subject, body, html, screenshot, text, images):

        if self.status:
            try:
                msg = MIMEMultipart()
                msg.set_charset('utf-8')

                msg['From'] = self.settings.smtp_from
                msg['To'] = email

                # Add headers
                if headers:
                    for name, value in headers.items():
                        msg.add_header(name, value)

                # Set a priority
                if priority:
                    msg['X-Priority'] = priority

                # Set a subject
                subject = Header(subject, 'utf-8')
                msg['Subject']= subject

                # Add body
                body = MIMEText(body, 'plain')
                body.set_charset('utf-8')
                msg.attach(body)

                # Add grabbed html
                if html:
                    html = MIMEText(html, self.settings.attachment_mime)
                    html.add_header('Content-Disposition', 'attachment', filename=self.settings.attachment_name + '.html')
                    msg.attach(html)

                # Add grabbed image
                if screenshot:
                    image = MIMEImage(screenshot, 'png')
                    image.add_header('Content-Disposition', 'attachment', filename=self.settings.attachment_name + '.png')
                    msg.attach(image)

                # Add grabbed text
                if text:
                    text = MIMEText(text, self.settings.attachment_mime)
                    text.add_header('Content-Disposition', 'attachment', filename=self.settings.attachment_name + '.txt')
                    text.set_charset('utf-8')
                    msg.attach(text)

                # Add grabbed image
                if images:
                    for image in images:
                        image_data = image[0]
                        image_format = image[1]
                        image_name = image[2]

                        image = MIMEImage(image_data, image_format)
                        image.add_header(
                            'Content-Disposition',
                            'attachment',
                            filename=self.settings.attachment_name + image_name + "." + image_format.lower())
                        msg.attach(image)

                # Convert envelope to string
                text = msg.as_string()

                self._logger(
                    "debug",
                    "Envelope has been assembled"
                )

                # Try to send letter
                try:
                    self.server.sendmail(self.settings.smtp_from, email, text)

                    self._logger(
                        "debug",
                        "Email has been sent: {}".format(email)
                    )

                    return True

                except Exception as error:

                    self._logger(
                        "warning",
                        "Cannot send letter to: {} -> {}".format(email, error)
                    )

                    return False

            except Exception as error:
                self._logger(
                    "warning",
                    "Cannot assemble envelope: {}".format(error)
                )

                return False

        else:
            return False
