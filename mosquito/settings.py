#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Settings module. Supports .mosquito.ini """

import logging
import os
import sys
import ConfigParser


class MosquitoSettings(object):
    
    def __init__(self):
        # Set logger
        self.logger = logging.getLogger(__name__)
        
        # Statuses of plugins
        self.twitter = False
        self.facebook = False
                
        # Try to find the configuration file
        inifile = os.path.join(os.environ['HOME'], '.mosquito.ini')
        
        if not os.path.exists(inifile):
            self.logger.error('Configuration files were not found. You should place .mosquito.ini into your home directory.')
            sys.exit(1)        
        
        settings = ConfigParser.RawConfigParser({
                                               'grab_timeout': 30,
                                               'smtp_server': 'localhost',
                                               'smtp_port': 25,
                                               'smtp_usessl': 'False',
                                               'smtp_auth': 'False',
                                               'smtp_from': None,
                                               'smtp_username': None,
                                               'smtp_password': None,
                                               'verbose': 'info'
                                               })
        
        # Try to parse configuration file
        try:
            settings.read(inifile)
            
            self.grab_timeout = settings.get('main', 'grab_timeout')
            self.smtp_server = settings.get('main', 'smtp_server')
            self.smtp_port = settings.get('main', 'smtp_port')
            self.smtp_usessl = settings.getboolean('main', 'smtp_usessl')
            self.smtp_auth = settings.getboolean('main', 'smtp_auth')
            self.smtp_from = settings.get('main', 'smtp_from')
            self.smtp_username = settings.get('main', 'smtp_username')
            self.smtp_password = settings.get('main', 'smtp_password')
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
                
            # Try to obtain Facebook settings
            if settings.has_section('facebook'):
                try:
                    self.facebook_access_token = settings.get('facebook', 'access_token')
                    self.facebook = True
                except:
                    pass

        except Exception as error:
            self.logger.error('Invalid configuration file: {} {}'.format(inifile, error))
            sys.exit(1)
            
        
        
        
        
        
        
        
        
        
        
        
        