#!/usr/bin/env python
# -*- coding: utf-8 -*-

import feedparser
import logging
import time
from datetime import datetime


class MosquitoRSS(object):
    def __init__(self, url):
        self.url = url
        
    def fetch(self):
        results = []
        
        parser = feedparser.parse(self.url)
        
        for post in parser.entries:
            expanded_url = None
            
            if len(post.links[0]['href']) > 0:
                expanded_url = post.links[0]['href']
                
            results.append([time.mktime(post.published_parsed), post.title, expanded_url])
            
        return results
            

        