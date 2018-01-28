#!/usr/bin/env python3

""" Settings module. Supports ~/.mosquito.ini """

import logging
import os
import sys
import configparser


class MosquitoSettings(object):
    
    def __init__(self):
        # Set logger
        self.logger = logging.getLogger('[SETTINGS]')
        
        # Try to find the configuration file
        inifile = os.path.join(os.environ['HOME'], '.mosquito.ini')
        
        if not os.path.exists(inifile):
            self.logger.error('Configuration files were not found. You should place .mosquito.ini into your home directory.')
            sys.exit(1)        
        
        settings = configparser.RawConfigParser(
            {
                'attachment_mime': 'logstash',
                'attachment_name': 'mosquito',
                'destination': None,
                'firefox_path': '/usr/bin/firefox',
                'geckodriver_path': '/usr/local/bin/geckodriver',
                'grab_timeout': 60,
                'lock_file': '/tmp/mosquito.lock',
                'regex': '.*',
                'regex_action': 'subject=Mosquito:',
                'smtp_server': 'localhost',
                'smtp_port': 25,
                'smtp_usessl': 'False',
                'smtp_auth': 'False',
                'smtp_from': None,
                'smtp_username': None,
                'smtp_password': None,
                'subject_length': 100,
                'pool': 2,
                'update_alert': '7d',
                'update_interval': '15m',
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
                'verbose': 'info'
            }
        )
        
        # Try to parse configuration file
        try:
            settings.read(inifile)
            
            self.destination = settings.get('main', 'destination')
            if self.destination:
                self.destination = self.destination.split(',')
                self.destination = [x.strip(' ') for x in self.destination]

            self.attachment_mime = settings.get('main', 'attachment_mime')
            self.attachment_name = settings.get('main', 'attachment_name')
            self.grab_timeout = int(settings.get('main', 'grab_timeout'))
            self.lock_file = settings.get('main', 'lock_file')
            self.regex = settings.get('main', 'regex').split()
            self.regex_action = settings.get('main', 'regex_action').split()
            self.smtp_server = settings.get('main', 'smtp_server')
            self.smtp_port = int(settings.get('main', 'smtp_port'))
            self.smtp_usessl = settings.getboolean('main', 'smtp_usessl')
            self.smtp_auth = settings.getboolean('main', 'smtp_auth')
            self.smtp_from = settings.get('main', 'smtp_from')
            self.smtp_username = settings.get('main', 'smtp_username')
            self.smtp_password = settings.get('main', 'smtp_password')
            self.subject_length = int(settings.get('main', 'subject_length'))
            self.pool = int(settings.get('main', 'pool'))
            self.update_alert = settings.get('main', 'update_alert')
            self.update_interval = settings.get('main', 'update_interval')
            self.user_agent = settings.get('main', 'user_agent')
            self.verbose = settings.get('main', 'verbose')
            
            # Try to obtain Twitter settings
            if settings.has_section('twitter'):
                try:
                    self.twitter_consumer_key = settings.get('twitter', 'consumer_key')
                    self.twitter_consumer_secret = settings.get('twitter', 'consumer_secret')
                    self.twitter_access_token_key = settings.get('twitter', 'access_token_key')
                    self.twitter_access_token_secret = settings.get('twitter', 'access_token_secret')
                    self.twitter = True
                except:
                    pass

        except Exception as error:
            self.logger.error('Invalid configuration file: {} {}'.format(inifile, error))
            sys.exit(1)