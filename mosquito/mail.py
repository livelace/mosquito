#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import smtplib
from email.header import Header
from email.MIMEImage import MIMEImage
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from settings import MosquitoSettings

class MosquitoMail(object):
    
    def __init__(self):
        # Get the settings
        self.settings = MosquitoSettings()

        # Set logger
        self.logger = logging.getLogger('[MAIL]')
        
        self.active = False

        if self.settings.smtp_usessl:
            try:
                self.server = smtplib.SMTP_SSL(self.settings.smtp_server, self.settings.smtp_port)   
                self.logger.debug('SSL connection has been established: {}:{}'.format(self.settings.smtp_server, self.settings.smtp_port))
            except smtplib.ssl.SSLError:
                try:
                    self.server = smtplib.SMTP(self.settings.smtp_server, self.settings.smtp_port)
                    self.server.starttls()
                    self.logger.debug('STARTTLS connection has been established: {}:{}'.format(self.settings.smtp_server, self.settings.smtp_port))
                except:
                    self.logger.warning('Cannot establish SSL connection to SMTP server: {}:{}'.format(self.settings.smtp_server, self.settings.smtp_port))
            except Exception:
                self.logger.warning('Cannot establish connection to SMTP server: {}:{}'.format(self.settings.smtp_server, self.settings.smtp_port))
        else:
            try:
                self.server = smtplib.SMTP(self.settings.smtp_server, self.settings.smtp_port)       
            except:
                self.logger.warning('Cannot establish plain connection to SMTP server: {}:{}'.format(self.settings.smtp_server, self.settings.smtp_port))
                
        if self.settings.smtp_auth:
            try:
                self.server.login(self.settings.smtp_username, self.settings.smtp_password)
                self.active = True
                self.logger.debug('Authentification has been passed: {}:{}'.format(self.settings.smtp_server, self.settings.smtp_port))
            except Exception:
                self.logger.warning('Cannot authenticate on SMTP server: {}:{}'.format(self.settings.smtp_server, self.settings.smtp_port))
                
    def send(self, destination_list, header_list, priority, subject, original_content, expanded_text_content, expanded_image_content):
        for email in destination_list:       
            try:
                msg = MIMEMultipart()
                msg.set_charset('utf-8')
            
                msg['From'] = self.settings.smtp_from
                msg['To'] = email

                # Set a custom header
                if header_list:
                    for header in header_list:
                        msg.add_header(header.split(':')[0], header.split(':')[1])
                      
                # Set a priority
                if priority:
                    msg['X-Priority'] = priority
                
                # Set a subject
                subject =  Header(subject, 'utf-8')
                msg['Subject']= subject

                # Add original content
                original_content = MIMEText(original_content.encode('utf-8'), 'plain')
                original_content.set_charset('utf-8')
                msg.attach(original_content)
           
                # Add expanded text
                if expanded_text_content:
                    text = MIMEText(expanded_text_content.encode('utf-8'), 'plain')
                    text.add_header('Content-Disposition', 'attachment', filename='page.txt')
                    text.set_charset('utf-8')
                    msg.attach(text)

                # Add expanded image
                if expanded_image_content:
                    image = MIMEImage(expanded_image_content, 'png')
                    image.add_header('Content-Disposition', 'attachment', filename='page.png')
                    msg.attach(image)
                    
                # Convert envelope to string
                text = msg.as_string()
                
                self.logger.debug('Envelope has been assembled')
            except Exception as error:
                self.logger.error('Cannot assemble the envelope: {}'.format(error))
            
            try:
                self.server.sendmail(self.settings.smtp_from, email, text)
                self.logger.debug('Email has been sent: {}'.format(email))
                return True
            except Exception as error:
                self.logger.error('Cannot send letter: {} {}'.format(email, error) )
                return False
            

        
    