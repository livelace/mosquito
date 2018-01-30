#!/usr/bin/env python3

import ast
import eventlet
import feedparser
import logging
import requests
import time

from datetime import datetime
from io import BytesIO
from mosquito.settings import MosquitoSettings


class MosquitoRSS(object):
    def __init__(self, id=None, queue=None):
        self.id = id
        self.queue = queue

        self.logger = logging.getLogger('[RSS]')
        self.settings = MosquitoSettings()

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

    def fetch(self, url):
        messages = []

        eventlet.monkey_patch()

        headers = {'User-Agent': self.settings.user_agent}

        with eventlet.Timeout(self.settings.grab_timeout):
            try:
                with requests.get(url, headers=headers, verify=ast.literal_eval(self.settings.check_ssl)) as r:
                    content = BytesIO(r.content)
                    feed = feedparser.parse(content)

            except eventlet.timeout.Timeout:
                self._logger(
                    "warning",
                    "Timeout for URL was reached: {}".format(url)
                )

                return messages

            except requests.exceptions.SSLError:
                self._logger(
                    "warning",
                    "SSL verification for URL was failed: {}".format(url)
                )

                return messages

            except Exception as error:
                self._logger(
                    "warning",
                    "Cannot grab HTML from URL: {} -> {}".format(url, error)
                )

                return messages

        for post in feed.entries:
            expanded_url = None
            timestamp = None

            # Get URL from a post
            try:
                if len(post.links[0]['href']) > 0:
                    expanded_url = post.links[0]['href']
            except:
                pass

            # Get timestamp from a post
            try:
                timestamp = time.mktime(post.updated_parsed)
            except:
                pass

            # Get timestamp from a post
            try:
                timestamp = time.mktime(post.published_parsed)
            except:
                pass

            # Make a timestamp if there are no any internal timestamps
            if not timestamp:
                timestamp = time.mktime(datetime.utcnow().timetuple())
                
            messages.append([timestamp, post.title, expanded_url])

        self._logger(
            "debug",
            "Fetched messages: {}".format(len(messages))
        )

        return messages
