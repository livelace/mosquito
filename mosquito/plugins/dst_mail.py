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

    def send(self, destinations, headers, priority, subject, original_content, grabbed_html, grabbed_image,
             grabber_text):

        if self.status:
            for email in destinations:
                try:
                    msg = MIMEMultipart()
                    msg.set_charset('utf-8')

                    msg['From'] = self.settings.smtp_from
                    msg['To'] = email

                    # Set a custom header
                    if headers:
                        for header in headers:
                            msg.add_header(header.split(':', 1)[0], header.split(':', 1)[1])

                    # Set a priority
                    if priority:
                        msg['X-Priority'] = priority

                    # Set a subject
                    subject =  Header(subject, 'utf-8')
                    msg['Subject']= subject

                    # Add original content
                    original_content = MIMEText(original_content, 'plain')
                    original_content.set_charset('utf-8')
                    msg.attach(original_content)

                    # Add expanded html
                    if grabbed_html:
                        html = MIMEText(grabbed_html, self.settings.mime)
                        html.add_header('Content-Disposition', 'attachment', filename=self.settings.attachment_name + '.html')
                        msg.attach(html)

                    # Add expanded image
                    if grabbed_image:
                        image = MIMEImage(grabbed_image, 'png')
                        image.add_header('Content-Disposition', 'attachment', filename=self.settings.attachment_name + '.png')
                        msg.attach(image)

                    # Add expanded text
                    if grabber_text:
                        text = MIMEText(grabber_text, self.settings.mime)
                        text.add_header('Content-Disposition', 'attachment', filename=self.settings.attachment_name + '.txt')
                        text.set_charset('utf-8')
                        msg.attach(text)

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
