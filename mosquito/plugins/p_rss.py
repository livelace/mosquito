#!/usr/bin/env python
# -*- coding: utf-8 -*-

import feedparser
import logging
import time
from datetime import datetime


class MosquitoRSS(object):
    def __init__(self, url):
        # Set logger
        self.logger = logging.getLogger('[RSS]')
        
        self.url = url
        
    def fetch(self):
        results = []
        
        parser = feedparser.parse(self.url)
        
        for post in parser.entries:
            expanded_url = None
            
            try:
                if len(post.links[0]['href']) > 0:
                    expanded_url = post.links[0]['href']
            except:
                pass
                
            try:
                timestamp = time.mktime(post.updated_parsed)
            except:
                pass    
                
            try:
                timestamp = time.mktime(post.published_parsed)
            except:
                pass
            
            if not timestamp:
                timestamp = time.mktime(datetime.utcnow().timetuple())
                
            results.append([timestamp, post.title, expanded_url])
        
        return results
            

        