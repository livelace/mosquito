#!/usr/bin/env python
# -*- coding: utf-8 -*-

import coloredlogs
import logging
import time
import twitter

from datetime import datetime
from mosquito.settings import MosquitoSettings

class MosquitoTwitter(object):
    
    def __init__(self):
        # Get the settings
        self.settings = MosquitoSettings()
        
        # Set logger
        coloredlogs.DEFAULT_LOG_FORMAT = '%(asctime)s %(name)s %(levelname)s %(message)s'
        coloredlogs.install(level=self.settings.verbose)
        self.logger = logging.getLogger('[TWITTER]')
        
        # Hide HTTP requests
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        
        # Status of the plugin
        self.active = False
        
        if self.settings.twitter:
            try:
                self.api = twitter.Api(consumer_key=self.settings.twitter_consumer_key,
                    consumer_secret=self.settings.twitter_consumer_secret,
                    access_token_key=self.settings.twitter_access_token_key,
                    access_token_secret=self.settings.twitter_access_token_secret)
                self.api.VerifyCredentials()
                self.active = True
                self.logger.debug('Logon process to Twitter account has been successfully completed')
            except:
                self.logger.error('Cannot login to Twitter account. The plugin has been disabled.')
        else:
            self.logger.warning('Twitter settings are not set. The plugin has been disabled.')

    def fetch(self, source):
        if self.active:
            try:
                results = []
                #print self.api.GetUserTimeline(screen_name=source)
                statuses = self.api.GetUserTimeline(screen_name=source, count=200)

                for status in statuses:
                    expanded_url = None
                    timestamp = time.mktime(datetime.strptime(status.created_at, '%a %b %d %H:%M:%S +0000 %Y').timetuple())
                
                    if len(status.urls) > 0:
                        expanded_url = status.urls[0].expanded_url
                
                    results.append([timestamp, status.text, expanded_url])
                
                self.logger.debug('Data has been fetched from the source: {}'.format(source))
                return results
            except:
                self.logger.error('Cannot fetch data from the source: {}'.format(source))
            