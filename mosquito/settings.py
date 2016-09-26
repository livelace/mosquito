#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Settings module. Supports ~/.mosquito.ini """

import logging
import os
import sys
import ConfigParser


class MosquitoSettings(object):
    
    def __init__(self):
        # Set logger
        logging.basicConfig()
        self.logger = logging.getLogger('[SETTINGS]')
        
        # Try to find the configuration file
        inifile = os.path.join(os.environ['HOME'], '.mosquito.ini')
        
        if not os.path.exists(inifile):
            self.logger.error('Configuration files were not found. You should place .mosquito.ini into your home directory.')
            sys.exit(1)        
        
        settings = ConfigParser.RawConfigParser({
                                               'destination': None,
                                               'grab_timeout': 60,
                                               'smtp_server': 'localhost',
                                               'smtp_port': 25,
                                               'smtp_usessl': 'False',
                                               'smtp_auth': 'False',
                                               'smtp_from': None,
                                               'smtp_username': None,
                                               'smtp_password': None,
                                               'update_interval': '15m',
                                               'verbose': 'info'
                                               })
        
        # Try to parse configuration file
        try:
            settings.read(inifile)
            
            self.destination = settings.get('main', 'destination')
            if self.destination:
                self.destination = self.destination.split(',')
                self.destination = [x.strip(' ') for x in self.destination]
                
            self.grab_timeout = settings.get('main', 'grab_timeout')
            self.smtp_server = settings.get('main', 'smtp_server')
            self.smtp_port = settings.get('main', 'smtp_port')
            self.smtp_usessl = settings.getboolean('main', 'smtp_usessl')
            self.smtp_auth = settings.getboolean('main', 'smtp_auth')
            self.smtp_from = settings.get('main', 'smtp_from')
            self.smtp_username = settings.get('main', 'smtp_username')
            self.smtp_password = settings.get('main', 'smtp_password')
            self.update_interval = settings.get('main', 'update_interval')
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
            
        
        
        
        
        
        
        
        
        
        
        
        