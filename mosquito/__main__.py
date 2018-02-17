#!/usr/bin/env python3

import argparse
import ast
import chardet
import coloredlogs
import eventlet
import fcntl
import logging
import multiprocessing
import os
import re
import requests
import sys
import time
import validators
import warnings

from bs4 import BeautifulSoup
from datetime import datetime
from distutils.util import strtobool
from html2text import HTML2Text
from io import BytesIO
from selenium import webdriver
from terminaltables import AsciiTable
from textwrap import wrap
from PIL import Image

from mosquito.db import MosquitoDB
from mosquito.settings import MosquitoSettings
from mosquito.help import MosquitoHelp

from mosquito.plugins.dst_exec import MosquitoExec
from mosquito.plugins.dst_mail import MosquitoMail
from mosquito.plugins.src_rss import MosquitoRSS
from mosquito.plugins.src_twitter import MosquitoTwitter


class MosquitoParallelFetching(object):
    def __init__(self, force, settings):
        self.settings = settings
        self.force = force

        coloredlogs.install(level=self.settings.log_level)
        self.logger = logging.getLogger('[POOL]')

    def _convert_encoding(self, data, id, queue, new_encoding='UTF-8'):
        """ Detect encoding and convert it to UTF-8 """

        encoding = chardet.detect(data)['encoding']

        queue.put([
            id,
            "debug",
            "Detected encoding: {}".format(encoding)
        ])

        if encoding.upper() != new_encoding.upper():
            data = data.decode(encoding, new_encoding)
        else:
            data = data.decode()

        return data

    def _grab_content(self, url, mode, id, queue, params=None):
        """ Grab data in different formats """

        eventlet.monkey_patch()

        headers = {"User-Agent": self.settings.user_agent}

        if mode == "images":
            image_min_width = 0
            image_min_height = 0
            image_max_width = 0
            image_max_height = 0

            if params:
                for param in params:
                    k, v = param.split(':')
                    w, h = v.split('x')

                    if k == 'min':
                        image_min_width = int(w)
                        image_min_height = int(h)
                    else:
                        image_max_width = int(w)
                        image_max_height = int(h)

            with eventlet.Timeout(self.settings.grab_timeout):
                try:
                    # -------------------------------------------------------------------------------------

                    links = []
                    images = []

                    # -------------------------------------------------------------------------------------

                    with requests.get(url, headers=headers, verify=ast.literal_eval(self.settings.check_ssl)) as r:
                        body = self._convert_encoding(r.content, id, queue)

                    # -------------------------------------------------------------------------------------

                    soup = BeautifulSoup(body, "lxml")

                    for image in soup.find_all('img', src=True):
                        link = image['src']

                        if validators.url(link):
                            links.append(link)

                    # -------------------------------------------------------------------------------------

                    for link in links:
                        with requests.get(link, headers=headers, verify=ast.literal_eval(self.settings.check_ssl)) as r:
                            image_data = BytesIO(r.content)

                            try:
                                with Image.open(image_data) as image:
                                    width, height = image.size

                                    if width >= image_min_width and height >= image_min_height:
                                        if width <= image_max_width and height <= image_max_height:
                                            queue.put([
                                                id,
                                                "debug",
                                                "Image was matched: {}".format(link)
                                            ])
                                            images.append([image_data.getvalue(), image.format])
                            except:
                                pass

                    return images

                except eventlet.timeout.Timeout:
                    queue.put([
                        id,
                        "warning",
                        "Timeout for URL was reached: {}".format(url)
                    ])

                except requests.exceptions.SSLError:
                    queue.put([
                        id,
                        "warning",
                        "SSL verification for URL was failed: {}".format(url)
                    ])

                except Exception as error:
                    queue.put([
                        id,
                        "warning",
                        "Cannot grab images from URL: {} -> {}".format(url, error)
                    ])

        elif mode == "html":
            with eventlet.Timeout(self.settings.grab_timeout):
                try:
                    with requests.get(url, headers=headers, verify=ast.literal_eval(self.settings.check_ssl)) as r:
                        body = self._convert_encoding(r.content, id, queue)

                    return body

                except eventlet.timeout.Timeout:
                    queue.put([
                        id,
                        "warning",
                        "Timeout for URL was reached: {}".format(url)
                    ])

                except requests.exceptions.SSLError:
                    queue.put([
                        id,
                        "warning",
                        "SSL verification for URL was failed: {}".format(url)
                    ])

                except Exception as error:
                    queue.put([
                        id,
                        "warning",
                        "Cannot grab HTML from URL: {} -> {}".format(url, error)
                    ])

        elif mode == "screenshot":
            if re.search("firefox", self.settings.browser_path):
                browser_options = webdriver.FirefoxOptions()
                browser_options.add_argument("--headless")
                browser_options.binary_location = self.settings.browser_path

                driver = webdriver.Firefox(
                    executable_path=self.settings.browser_driver_path,
                    firefox_options=browser_options
                )

            elif re.search("chrome|chromium", self.settings.browser_path):
                browser_options = webdriver.ChromeOptions()
                browser_options.add_argument("--headless")
                browser_options.binary_location = self.settings.browser_path

                driver = webdriver.Chrome(
                    executable_path=self.settings.browser_driver_path,
                    chrome_options=browser_options
                )

            with eventlet.Timeout(self.settings.grab_timeout):
                try:
                    driver.get(url)
                    element = driver.find_element_by_tag_name('body')
                    screenshot = element.screenshot_as_png
                    driver.quit()

                    return screenshot

                except eventlet.timeout.Timeout:
                    queue.put([
                        id,
                        "warning",
                        "Timeout for URL was reached: {}".format(url)
                    ])

                except Exception as error:
                    queue.put([
                        id,
                        "warning"
                        "Cannot grab screenshot from URL: {} -> {}".format(url, error)
                    ])

        elif mode == "text":
            with eventlet.Timeout(self.settings.grab_timeout):
                try:
                    with requests.get(url, headers=headers, verify=ast.literal_eval(self.settings.check_ssl)) as r:
                        h2t = HTML2Text()
                        h2t.body_width = 0
                        h2t.ignore_emphasis = True
                        #h2t.ignore_images = True

                        text = self._convert_encoding(r.content, id, queue)
                        text = h2t.handle(text)

                    return text

                except eventlet.timeout.Timeout:
                    queue.put([
                        id,
                        "warning",
                        "Timeout for URL was reached: {}".format(url)
                    ])

                except requests.exceptions.SSLError:
                    queue.put([
                        id,
                        "warning",
                        "SSL verification for URL was failed: {}".format(url)
                    ])

                except Exception as error:
                    queue.put([
                        id,
                        "warning",
                        "Cannot grab text from URL: {} -> {}".format(url, error)
                    ])

    def _logger(self, queue):
        while True:
            item = queue.get()

            if item:
                config_id = item[0]
                level = item[1]
                message = item[2]

                coloredlogs.DEFAULT_LOG_FORMAT = '%(asctime)s %(name)s[{}] %(levelname)s  %(message)s'.format(config_id)
                coloredlogs.install(level=self.settings.log_level)

                if level == "debug":
                    self.logger.debug(message)
                elif level == "error":
                    self.logger.error(message)
                elif level == "info":
                    self.logger.info(message)
                elif level == "warning":
                    self.logger.warning(message)

    def _match_regex(self, data, regexs, id, queue):
        """ Search patterns in data """

        if regexs:
            regex_found = False

            for regex in regexs:
                pattern = re.compile(regex,re.IGNORECASE + re.UNICODE)

                if re.search(pattern, data):
                    regex_found = True
                    queue.put([
                        id,
                        "debug",
                        "Regex was matched: {}".format(regex)
                    ])
                else:
                    queue.put([
                        id,
                        "debug",
                        "Regex wasn't matched: {}".format(regex)
                    ])

            if regex_found:
                queue.put([
                    id,
                    "debug",
                    "Content was matched"
                ])
            else:
                if regex_found:
                    queue.put([
                        id,
                        "debug",
                        "Content wasn't matched"
                    ])

            return regex_found
        else:
            print("Regexp list is empty!")
            return False

    def _process_config(self, config):
        config_id = config[0]
        config_enabled = config[1]
        config_plugin = config[2]
        config_source = config[3]
        config_destination = ast.literal_eval(config[4])
        config_update_alert = config[5]
        config_update_interval = config[6]
        config_regex = ast.literal_eval(config[8])
        config_regex_action = ast.literal_eval(config[9])
        config_timestamp = config[10]
        config_alert_timestamp = config[12]
        config_images_settings = ast.literal_eval(config[13])
        current_timestamp = time.mktime(datetime.utcnow().timetuple())
        queue = config[14]

        db = MosquitoDB(config_id, queue)
        exec = MosquitoExec(config_id, queue)
        mail = MosquitoMail(config_id, queue)

        if self.force or config_enabled == "True":
            if self.force or (current_timestamp - config_timestamp) > config_update_interval:

                queue.put([
                    config_id,
                    "info",
                    "Working with configuration: {}".format(config_id)
                ])

                if config_plugin == "rss":
                    plugin = MosquitoRSS(config_id, queue)
                elif config_plugin == "twitter":
                    plugin = MosquitoTwitter(config_id, queue)

                messages = plugin.fetch(config_source)

                count = 0

                for message in messages:
                    message_timestamp = message[0]
                    message_url = message[2]
                    message_title = message[1]

                    if message_timestamp > config_timestamp:
                        if self._match_regex(message_title, config_regex, config_id, queue):
                            grab_list = []
                            tag_list = []

                            mail_priority = None
                            mail_subject = None

                            grabbed_images = []
                            grabbed_html = None
                            grabbed_screenshot = None
                            grabbed_text = None

                            for action in config_regex_action:
                                action_type = action.split("=")[0]
                                action_value = action.split("=")[1]

                                if action_type == "grab":
                                    grab_list.append(action_value)
                                elif action_type == "priority":
                                    mail_priority = action_value
                                elif action_type == "subject":
                                    mail_subject = action_value
                                elif action_type == "tag":
                                    tag_list.append(action_value)

                            # ------------------------------------------------------------------------
                            # Process a grab list

                            if grab_list and message_url:
                                for grab in grab_list:

                                    if grab == "full":
                                        grabbed_images = self._grab_content(message_url, "images", config_id, queue, params=config_images_settings)
                                        grabbed_html = self._grab_content(message_url, "html", config_id, queue)
                                        grabbed_screenshot = self._grab_content(message_url, "screenshot", config_id, queue)
                                        grabbed_text = self._grab_content(message_url, "text", config_id, queue)

                                    elif grab == "images":
                                        grabbed_images = self._grab_content(message_url, grab, config_id, queue, params=config_images_settings)

                                    elif grab == "html":
                                        grabbed_html = self._grab_content(message_url, grab, config_id, queue)

                                    elif grab == "screenshot":
                                        grabbed_screenshot = self._grab_content(message_url, grab, config_id, queue)

                                    elif grab == "text":
                                        grabbed_text = self._grab_content(message_url, grab, config_id, queue)

                            # ------------------------------------------------------------------------

                            for destination in config_destination:
                                k, v = destination.split(":", 1)

                                if k == "exec":
                                    exec.run(
                                        config_id,
                                        v,                      # path to executable
                                        tag_list,
                                        message_title,
                                        grabbed_html,
                                        grabbed_screenshot,
                                        grabbed_text,
                                        grabbed_images
                                    )

                                elif k == "mail":
                                    mail_headers = tag_list

                                    if mail_subject:
                                        mail_subject = mail_subject + " " + message_title.split("\n", 1)[0]
                                    else:
                                        mail_subject = message_title.split("\n", 1)[0]

                                    if mail_subject:
                                        if len(mail_subject) > self.settings.subject_length:
                                            mail_subject = mail_subject[:self.settings.subject_length] + " ..."

                                        mail_subject = re.sub(r"https?:\/\/.*", "", mail_subject)

                                    # Add default headers
                                    mail_headers.append("X-mosquito-id:" + str(config_id))
                                    mail_headers.append("X-mosquito-plugin:" + str(config_plugin))
                                    mail_headers.append("X-mosquito-source:" + str(config_source))
                                    mail_headers.append("X-mosquito-message-url:" + str(message_url))

                                    # Set email priority
                                    if mail_priority:
                                        if mail_priority == "high":
                                            mail_priority = "1"
                                        elif mail_priority == "normal":
                                            mail_priority = "3"
                                        elif mail_priority == "low":
                                            mail_priority = "5"

                                    # Append URL to mail body
                                    mail_body = message_title + "\n\n---\n{}".format(message_url)

                                    if not mail.send(
                                            v, mail_headers, mail_priority, mail_subject, mail_body, grabbed_html,
                                            grabbed_screenshot, grabbed_text, grabbed_images
                                    ):
                                        queue.put([
                                            config_id,
                                            "warning",
                                            "SMTP server is not available. Add message to archive!"
                                        ])

                                        db.add_archive(
                                            config_id, v, mail_headers, mail_priority, mail_subject, mail_body,
                                            grabbed_html, grabbed_screenshot, grabbed_text, current_timestamp
                                        )

                            count += 1
                    else:
                        queue.put([
                            config_id,
                            "debug",
                            "The message timestamp is lower than the config timestamp, skipping: {} < {}".format(
                                int(message_timestamp), int(config_timestamp))
                        ])

                if count > 0:
                    # Update timestamp for a configuration
                    db.update_timestamp(config_id, time.mktime(datetime.utcnow().timetuple()))

                    # Increase counter for a configuration
                    db.update_counter(config_id, count)
                else:
                    # Check if we haven't received new data during a specific interval
                    if current_timestamp > (config_timestamp + int(config_update_alert)):
                        queue.put([
                            config_id,
                            "warning",
                            "No new data for the configuration: {}".format(config_id)
                        ])

                        # Check if we are reached "alert_interval". If so, send a letter.
                        if current_timestamp > (int(config_alert_timestamp) +
                                                self._validate_interval(self.settings.alert_interval)):
                            queue.put([
                                config_id,
                                "warning",
                                "Alert interval reached. Sending an alert email: {}".format(config_id)
                            ])

                            if mail.send(
                                config_destination, None, None, self.settings.alert_subject,
                                "{} -> {} -> {}".format(
                                    config_id, config_plugin, config_source
                                ), None, None, None
                            ):
                                db.update_alert_timestamp(config_id, current_timestamp)
            else:
                queue.put([
                    config_id,
                    "info",
                    "Update interval hasn't been reached, skipping: {}".format(config_id)
                ])

                return False

        else:
            queue.put([
                config_id,
                "info",
                "Configuration is disabled, skipping: {}".format(config_id)
            ])

            return False

        queue.put([
            config_id,
            "info",
            "Configuration has been processed: {}".format(config_id)
        ])

        return True

    def _validate_interval(self, interval):
        """
        Validate time types:
        "s" - seconds
        "m" - minutes
        "h" - hours
        "d" - days
        """

        if interval:
            if re.match('^[0-9]+[smhd]', interval):
                if interval.endswith('s'):
                    return int(interval[:-1])

                elif interval.endswith('m'):
                    return int(interval[:-1]) * 60

                elif interval.endswith('h'):
                    return int(interval[:-1]) * 60 * 60

                elif interval.endswith('d'):
                    return int(interval[:-1]) * 60 * 60 * 24

            elif interval.isdigit():
                return interval
            else:
                self.logger.error("Time interval must be a digit or a digit with suffix: {}".format(interval))
                sys.exit(1)

    def run(self, configs):
        # ----------------------------------------------------------------------------
        m = multiprocessing.Manager()
        q = m.Queue()

        lp = multiprocessing.Process(target=self._logger, args=(q,))
        lp.daemon = True
        lp.start()

        # ----------------------------------------------------------------------------

        configs_number = len(configs)

        if configs_number < self.settings.pool:
            pool_size = configs_number
        else:
            pool_size = self.settings.pool

        self.logger.info("Process pool size: {}".format(pool_size))

        # ----------------------------------------------------------------------------

        chunk_size = int((configs_number / pool_size) + 1)

        self.logger.info("Chunk size of the pool: {}".format(chunk_size))

        # ----------------------------------------------------------------------------

        configs_with_queue = []

        for config in configs:
            config = config + (q,)
            configs_with_queue.append(config)

        # ----------------------------------------------------------------------------

        self.logger.info("Putting configurations to the process pool: {}".format(configs_number))

        p = multiprocessing.Pool(pool_size)
        results = p.map(self._process_config, configs_with_queue, chunk_size)

        p.close()
        p.join()
        lp.terminate()

        # ----------------------------------------------------------------------------

        self.logger.info("Number of processed configurations: {}".format(results.count(True)))
        self.logger.info("Number of skipped configurations: {}".format(results.count(False)))


class Mosquito(object):

    def __init__(self):
        self.settings = MosquitoSettings()

        coloredlogs.DEFAULT_LOG_FORMAT = '%(asctime)s %(name)s %(levelname)s  %(message)s'
        coloredlogs.install(level=self.settings.log_level)

        self.logger = logging.getLogger('[MAIN]')

        # Hide HTTP requests
        if self.settings.log_level.upper() != 'DEBUG':
            logging.getLogger("requests").setLevel(logging.WARNING)

        # Hide feedparser deprecation warnings
        warnings.filterwarnings("ignore", category=DeprecationWarning)

        # List of supported plugins
        self.plugins = ['twitter', 'rss']

        self.db = MosquitoDB()
        self.help = MosquitoHelp()
        self.mail = MosquitoMail()

        # Try to send archived data
        if self.mail.status:
            self._send_archive()

        # Try to clean database
        self.db.clean()

        # Create root parser
        parser = argparse.ArgumentParser(prog='mosquito', description=self.help.description)
        subparsers = parser.add_subparsers()

        # Create 'create' parser
        parser_create = subparsers.add_parser('create', help=self.help.create1)
        parser_create.add_argument('--plugin', required=True, help=self.help.create2)
        parser_create.add_argument('--source', required=True, help=self.help.create3)
        parser_create.add_argument('--destination', nargs='+', default=self.settings.destination,
                                   help=self.help.create4)
        parser_create.add_argument('--update-alert', default=self.settings.update_alert, help=self.help.create5)
        parser_create.add_argument('--update-interval', default=self.settings.update_interval, help=self.help.create6)
        parser_create.add_argument('--description', nargs='+', help=self.help.create7)
        parser_create.add_argument('--regex', nargs='+', default=self.settings.regex, help=self.help.create8)
        parser_create.add_argument('--regex-action', nargs='+', default=self.settings.regex_action,
                                   help=self.help.create9)
        parser_create.add_argument('--images-settings', nargs='+',
                                   default=['min:' + self.settings.images_min, 'max:' + self.settings.images_max],
                                   help=self.help.create10)
        parser_create.set_defaults(func=self.create)

        # Create 'delete' parser
        parser_delete = subparsers.add_parser('delete', help=self.help.delete1)
        group_delete = parser_delete.add_mutually_exclusive_group(required=True)
        group_delete.add_argument('--plugin', nargs='+', help=self.help.delete2)
        group_delete.add_argument('--id', nargs='+', help=self.help.delete3)
        group_delete.set_defaults(func=self.delete)

        # Create 'fetch' parser
        parser_fetch = subparsers.add_parser('fetch', help=self.help.fetch1)
        parser_fetch.add_argument('--plugin', nargs='+', help=self.help.fetch2)
        parser_fetch.add_argument('--id', nargs='+', help=self.help.fetch3)
        parser_fetch.add_argument('--force', action='store_true', help=self.help.fetch4)
        parser_fetch.set_defaults(func=self.fetch)

        # Create 'list' parser
        parser_list = subparsers.add_parser('list', help=self.help.list1)
        parser_list.add_argument('--plugin', nargs='+', help=self.help.list2)
        parser_list.add_argument('--id', nargs='+', help=self.help.list3)
        parser_list.set_defaults(func=self.list)

        # Create 'set' parser
        parser_set = subparsers.add_parser('set', help=self.help.set1)
        parser_set.add_argument('--enabled', help=self.help.set2)
        parser_set.add_argument('--id', nargs='+', help=self.help.set3)
        parser_set.add_argument('--plugin', nargs='+', help=self.help.set4)
        parser_set.add_argument('--source', help=self.help.set5)
        parser_set.add_argument('--destination', nargs='+', help=self.help.set6)
        parser_set.add_argument('--update-alert', help=self.help.set7)
        parser_set.add_argument('--update-interval', help=self.help.set8)
        parser_set.add_argument('--description', nargs='+', help=self.help.set9)
        parser_set.add_argument('--regex', nargs='+', help=self.help.set10)
        parser_set.add_argument('--regex-action', nargs='+', help=self.help.set11)
        parser_set.add_argument('--images-settings', nargs='+', help=self.help.set12)
        parser_set.set_defaults(func=self.set)

        args = parser.parse_args()

        #try:
        args.func(args)
        #except AttributeError:
        #    parser.print_help()
        #    sys.exit(0)

    def _human_time(self, seconds):
        """ Convert seconds to human time """

        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)

        object_string = ''

        if d > 0: object_string += '{}d '.format(d)
        if h > 0: object_string += '{}h '.format(h)
        if m > 0: object_string += '{}m '.format(m)
        if s > 0: object_string += '{}s '.format(s)
         
        return object_string
    
    def _send_archive(self):
        """ Send archived data to a SMTP server """

        records = self.db.list_archive()

        if isinstance(records, list):
            for record in records:
                id = record[0]
                destinations = ast.literal_eval(record[2])
                headers = ast.literal_eval(record[3])
                priority = record[4]
                subject = record[5]
                original_content = record[6]
                grabbed_html = record[7]
                grabbed_screenshot = record[8]
                grabbed_text = record[9]

                if self.mail.send(destinations, headers, priority, subject, original_content, grabbed_html,
                                  grabbed_screenshot, grabbed_text):

                    self.logger.warning('Archived records are sending ...')
                    self.db.delete_archive(id)

    def _validate_action(self, destinations, actions):
        """
        Validate actions types:
        "execute" - execute script if data matches
        "grab" - fetch data in different formats
        "priority" - set priority for an email
        "subject" - set subject for an email
        "tag" - add a tag to an email or pass a tag to executable
        """

        available_actions = []

        if destinations:
            for destination in destinations:
                k, v = destination.split(":", 1)

                if k == "exec":
                    available_actions.extend(["grab", "tag"])
                elif k == "mail":
                    available_actions.extend(["grab", "priority", "subject", "tag"])

        available_actions = list(set(available_actions))

        if actions:
            for action in actions:
                action_type = action.split("=")[0]

                if action_type in available_actions:
                    if action_type == "grab":
                        try:
                            grab_content = action.split("=")[1]
                            if grab_content != "full" and grab_content != "html" and grab_content != "images" and \
                                    grab_content != "screenshot" and grab_content != "text":
                                raise Exception

                        except Exception:
                            self.logger.error("Action \"grab\" must be in format: grab=html|images|screenshot|text")
                            sys.exit(1)

                    elif action_type == "tag":
                        try:
                            tag_name = action.split("=")[1].split(":")[0]
                            tag_value = action.split("=")[1].split(":")[1]
                            if not tag_name or not tag_value:
                                raise Exception

                        except Exception:
                            self.logger.error("Action \"tag\" must be in format: tag=Foo:Bar")
                            sys.exit(1)

                    elif action_type == "priority":
                        try:
                            priority_type = action.split("=")[1]
                            if priority_type != "high" and priority_type != "normal" and priority_type != "low":
                                raise Exception

                        except Exception:
                            self.logger.error("Action \"priority\" must be in format: priority=low|normal|high")
                            sys.exit(1)

                    elif action_type == "subject":
                        try:
                            subject_text = action.split("=")[1]
                            if not subject_text:
                                raise Exception

                        except Exception:
                            self.logger.error("Action \"subject\" must be in format: subject=FooBar")
                            sys.exit(1)
                    else:
                        self.logger.error("Action type doesn't exist: {}".format(action_type))
                        sys.exit(1)
                else:
                    self.logger.error(
                        "There are no destinations whose support this type of an action: \"{}\"".format(action_type)
                    )
                    sys.exit(1)

        return actions

    def _validate_confirmation(self, question):
        """ Ask user confirmation """

        sys.stdout.write('%s [y/n]: ' % question)

        while True:
            try:
                return strtobool(input().lower())
            except ValueError:
                sys.stdout.write('Please respond with \'y\' or \'n\'.\n')

    def _validate_description(self, data):
        """ Transform quotes in description """

        if data:
            data = ' '.join(data)
            data = data.replace('"', '')
            data = data.replace("'", "")

            return data

    def _validate_destination(self, params):
        """ Validate destinations  """
        status = True

        if params:
            for param in params:
                try:
                    k, v = param.split(":", 1)

                    if k not in ["exec", "mail"]:
                        raise NameError("There are no valid destinations!")

                    if k == "exec":
                        if not os.path.isfile(v):
                            raise NameError("There is no valid executable file!")

                    if k == "mail":
                        if not validators.email(v):
                            raise NameError("There are no valid emails!")

                except NameError as error:
                    self.logger.error(error)
                    status = False

                except Exception:
                    self.logger.error("There are no valid destinations! See documentation for available destinations.")
                    status = False

        if status:
            return params
        else:
            sys.exit(1)

    def _validate_interval(self, interval):
        """
        Validate time types:
        "s" - seconds
        "m" - minutes
        "h" - hours
        "d" - days
        """

        if interval:
            if re.match('^[0-9]+[smhd]', interval):
                if interval.endswith('s'):
                    return int(interval[:-1])

                elif interval.endswith('m'):
                    return int(interval[:-1]) * 60

                elif interval.endswith('h'):
                    return int(interval[:-1]) * 60 * 60

                elif interval.endswith('d'):
                    return int(interval[:-1]) * 60 * 60 * 24

            elif interval.isdigit():
                return interval
            else:
                self.logger.error("Time interval must be a digit or a digit with suffix: {}".format(interval))
                sys.exit(1)

    def _validate_images_settings(self, params):
        status = True

        if params:
            for param in params:
                try:
                    k, v = param.split(':')
                    w, h = v.split('x')

                    if k not in ['min', 'max']:
                        raise Exception

                    int(w), int(h)
                except:
                    status = False

        if status:
            return params
        else:
            self.logger.error("There are no valid images size! Check your input and/or configuration file!")
            sys.exit(1)

    def _validate_plugin(self, plugin):
        """ Supported plugins """

        if plugin:
            plugin_status = True

            # ------------------------------------------------------------------------

            if isinstance(plugin, str):
                if plugin not in self.plugins:
                    plugin_status = False
            elif isinstance(plugin, list):
                for item in plugin:
                    if item not in self.plugins:
                        plugin_status = False
            else:
                plugin_status = False

            # ------------------------------------------------------------------------

            if plugin_status:
                return plugin
            else:
                if isinstance(plugin, str):
                    self.logger.error("Unsupported plugins detected: {}".format(plugin))
                elif isinstance(plugin, list):
                    self.logger.error("Unsupported plugins detected: {}".format(' '.join(str(i) for i in plugin)))

                sys.exit(1)

    def create(self, args):
        """ Create a configuration """

        plugin = self._validate_plugin(args.plugin)
        source = args.source
        destination = self._validate_destination(args.destination)
        update_alert = self._validate_interval(args.update_alert)
        update_interval = self._validate_interval(args.update_interval)
        description = self._validate_description(args.description)
        regex = args.regex
        regex_action = self._validate_action(destination, args.regex_action)
        images_settings = self._validate_images_settings(args.images_settings)

        self.db.create(
            'True', plugin, source, destination, update_alert, update_interval, description, regex, regex_action,
            '0', '0', '0', images_settings
        )

    def delete(self, args):
        """
        Delete configurations:
        "plugin": all or a space separated list of plugin names
        "id": all or a space separated list of IDs
        """

        if args.plugin:
            for plugin in args.plugin:
                self.logger.info(
                    'All configurations for a specific plugin have been selected for deletion: {}'.format(plugin)
                )

                if self._validate_confirmation('Please, confirm plugin deletion'):
                    self.db.delete(plugin, None)

        if args.id:
            self.logger.info('IDs have been selected for deletion: {}'.format(' '.join(str(i) for i in args.id)))

            if self._validate_confirmation('Please, confirm ID deletion'):
                for id in args.id:
                    self.db.delete(None, id)

    def fetch(self, args):
        """ Fetch data from source """

        # Set lock
        try:
            flock = open(self.settings.lock_file, 'a')
            fcntl.flock(flock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self.logger.error('Mosquito already running. Cannot set lock on: {}'.format(self.settings.lock_file))
            sys.exit(1)

        configs = []

        if not args.plugin and not args.id:
            configs = self.db.list('all', 'all')

        elif args.plugin and not args.id:
            for plugin in args.plugin:
                configs = configs + self.db.list(plugin, 'all')

        elif not args.plugin and args.id:
            for id in args.id:
                configs = configs + self.db.list('all', id)

        elif args.plugin and args.id:
            for plugin in args.plugin:
                configs = configs + self.db.list(plugin, 'all')
            for id in args.id:
                configs = configs + self.db.list('all', id)

        configs = list(set(configs))

        if configs:
            self.logger.debug("Configurations were retrieved: {}".format(len(configs)))

            pf = MosquitoParallelFetching(args.force, self.settings)
            pf.run(configs)
        else:
            self.logger.info("There are no configurations!")

        # Unset lock
        try:
            fcntl.flock(flock, fcntl.LOCK_UN)
        except:
            pass

    def list(self, args):
        """ List configurations """

        table = [[
                  'ID', 'Enabled', 'Plugin', 'Source', 'Destination', 'Alert', 'Interval', 'Desc', 'Regex',
                  'Regex Action', 'Images', 'Update', 'Count'
                ]]

        configs = []

        if not args.plugin and not args.id:
            configs = self.db.list('all', 'all')

        elif args.plugin and not args.id:
            for plugin in args.plugin:
                configs = configs + self.db.list(plugin, 'all')

        elif not args.plugin and args.id:
            for id in args.id:
                configs = configs + self.db.list('all', id)

        elif args.plugin and args.id:
            for plugin in args.plugin:
                configs = configs + self.db.list(plugin, 'all')
            for id in args.id:
                configs = configs + self.db.list('all', id)

        configs = sorted(list(set(configs)))

        if configs:
            for config in configs:
                if len(config) > 0:
                    table.append([
                        config[0], config[1], config[2], '\n'.join(wrap(str(config[3]), 15)),
                        '\n'.join(ast.literal_eval(config[4])), self._human_time(int(config[5])),
                        self._human_time(int(config[6])), '\n'.join(wrap(str(config[7]), 20)),
                        '\n'.join(ast.literal_eval(config[8])), '\n'.join(ast.literal_eval(config[9])), '\n'.join(ast.literal_eval(config[13])),
                        datetime.fromtimestamp(int(config[10])), config[11]
                    ])
                    
        if len(table) > 1:
            table = AsciiTable(table)
            table.justify_columns[0] = 'center'
            table.justify_columns[1] = 'center'
            table.justify_columns[2] = 'center'
            table.justify_columns[3] = 'center'
            table.justify_columns[4] = 'center'
            table.justify_columns[5] = 'center'
            table.justify_columns[6] = 'center'
            table.justify_columns[7] = 'center'
            table.justify_columns[10] = 'center'
            table.justify_columns[11] = 'center'
            table.inner_row_border = True
            print(table.table)
        else:
            self.logger.info('There are no configurations!')
    
    def set(self, args):
        """ Set parameters for configurations """

        ids = args.id
        enabled = args.enabled
        plugins = self._validate_plugin(args.plugin)
        source = args.source
        destination = args.destination
        update_alert = self._validate_interval(args.update_alert)
        update_interval = self._validate_interval(args.update_interval)
        description = self._validate_description(args.description)
        regex = args.regex
        regex_action = args.regex_action
        images_settings = self._validate_images_settings(args.images_settings)

        configs = []

        if not plugins and not ids:
            self.logger.error("You must choose --id and/or --plugin parameters")
            sys.exit(1)

        elif plugins and not ids:
            for plugin in plugins:
                configs = configs + self.db.list(plugin, 'all')

        elif not plugins and ids:
            for id in ids:
                configs = configs + self.db.list('all', id)

        elif plugins and ids:
            for plugin in plugins:
                configs = configs + self.db.list(plugin, 'all')
            for id in ids:
                configs = configs + self.db.list('all', id)

        configs = sorted(list(set(configs)))

        if configs:
            if self._validate_confirmation('Please, confirm configurations changes'):
                for config in configs:
                    config_id = config[0]

                    if enabled != "True" and enabled != "False":
                        config_enabled = config[1]
                    else:
                        config_enabled = enabled

                    if source:
                        config_source = source
                    else:
                        config_source = config[3]

                    if destination:
                        config_destination = self._validate_destination(destination)
                    else:
                        config_destination = ast.literal_eval(config[4])

                    if update_alert:
                        config_update_alert = update_alert
                    else:
                        config_update_alert = config[5]

                    if update_interval:
                        config_update_interval = update_interval
                    else:
                        config_update_interval = config[6]

                    if description:
                        config_description = description
                    else:
                        config_description = config[7]

                    if regex:
                        config_regex = regex
                    else:
                        config_regex = config[8]

                    if regex_action:
                        config_regex_action = self._validate_action(config_destination, regex_action)
                    else:
                        config_regex_action = self._validate_action(config_destination, ast.literal_eval(config[9]))

                    if images_settings:
                        config_images_settings = images_settings
                    else:
                        config_images_settings = config[13]

                    config_plugin = config[2]
                    config_timestamp = config[10]
                    config_counter = config[11]
                    config_alert_timestamp = config[12]

                    self.db.update(
                        config_id, config_enabled, config_plugin, config_source, config_destination, config_update_alert,
                        config_update_interval, config_description, config_regex, config_regex_action, config_timestamp,
                        config_counter, config_alert_timestamp, config_images_settings
                    )
        else:
            self.logger.info("There are no configurations for changes!")


def main():
    Mosquito()


if __name__ == '__main__':
    main()
