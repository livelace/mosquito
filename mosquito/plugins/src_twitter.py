#!/usr/bin/env python3

import eventlet
import logging
import time
import twitter

from datetime import datetime
from mosquito.settings import MosquitoSettings


class MosquitoTwitter(object):
    def __init__(self, id=None, queue=None):
        self.id = id
        self.queue = queue

        self.logger = logging.getLogger('[TWITTER]')
        self.settings = MosquitoSettings()
        self.status = False
        
        if self.settings.twitter:
            try:
                self.api = twitter.Api(
                    consumer_key=self.settings.twitter_consumer_key,
                    consumer_secret=self.settings.twitter_consumer_secret,
                    access_token_key=self.settings.twitter_access_token_key,
                    access_token_secret=self.settings.twitter_access_token_secret
                )

                self.api.VerifyCredentials()
                self.status = True

                self._logger(
                    "debug",
                    "Logon to a Twitter account has been successfully completed"
                )

            except:
                self._logger(
                    "error",
                    "Cannot login to a Twitter account. The plugin has been disabled"
                )
        else:
            self._logger(
                "error",
                "Twitter settings are not set. The plugin has been disabled"
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

    def fetch(self, url):
        messages = []

        eventlet.monkey_patch()

        if self.status:
            with eventlet.Timeout(self.settings.grab_timeout):
                try:
                    posts = self.api.GetUserTimeline(screen_name=url, count=200)
                except eventlet.timeout.Timeout:
                    self._logger(
                        "warning",
                        "Timeout for URL was reached: {}".format(url)
                    )

                    return messages

            for post in posts:
                expanded_url = None
                timestamp = time.mktime(datetime.strptime(post.created_at, '%a %b %d %H:%M:%S +0000 %Y').timetuple())

                if len(post.urls) > 0:
                    expanded_url = post.urls[0].expanded_url

                messages.append([timestamp, post.text, expanded_url])

            self._logger(
                "debug",
                "Fetched messages: {}".format(len(messages))
            )

        return messages
