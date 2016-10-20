#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Main module """

import argparse
import ast
import chardet
import coloredlogs
import logging
import os
import re
import requests
import sys
import subprocess
import time
import validators
import warnings

from datetime import datetime
from distutils.util import strtobool
from html2text import HTML2Text
from selenium import webdriver
from tempfile import mkstemp
from terminaltables import AsciiTable
from textwrap import wrap

from db import MosquitoDB
from mail import MosquitoMail
from settings import MosquitoSettings
from help import MosquitoHelp

from plugins.p_rss import MosquitoRSS
from plugins.p_twitter import MosquitoTwitter

class Mosquito(object):
       
    def _check_action(self, value):
        if value:
            """ execute, header, priority, subject, grab """
            
            action_type = value.split('=')[0]
            
            if  action_type == 'execute':
                try:
                    script_path = value.split('=')[1]
                    if not script_path:
                        raise
                except:
                    self.logger.error('Action \'execute\'  must have a value')
                    sys.exit(1)
            elif action_type == 'grab':
                try:
                    grab_content = value.split('=')[1]
                    if grab_content != 'full' and grab_content != 'text' and grab_content != 'image':
                        raise
                except:
                    self.logger.error('Action \'grab\' must have a value')
                    sys.exit(1)                
            elif action_type == 'header':
                try:
                    header_name = value.split('=')[1].split(':')[0]
                    header_value = value.split('=')[1].split(':')[1]
                    if not header_name or not header_value:
                        raise 
                except:
                    self.logger.error('Action \'header\' must have a value')
                    sys.exit(1)       
            elif action_type == 'priority':
                try:
                    priority_type = value.split('=')[1]
                    if priority_type != 'high' and priority_type != 'normal' and priority_type != 'low':
                        raise
                except:
                    self.logger.error('Action \'priority\' must have a value')
                    sys.exit(1)
            elif action_type == 'subject':
                try:
                    subject_text = value.split('=')[1]
                    if not subject_text:
                        raise
                except:
                    self.logger.error('Action \'subject\' must have a value')
                    sys.exit(1)
            else:
                self.logger.error('Action type does not found: {}'.format(action_type))
                sys.exit(1)
                
        return value
    
    def _check_confirmation(self, question):
        sys.stdout.write('%s [y/n]: ' % question)
        while True:
            try:
                return strtobool(raw_input().lower())
            except ValueError:
                sys.stdout.write('Please respond with \'y\' or \'n\'.\n')
        
    def _check_description(self, value):
        if value:
            string = ' '.join(value)
            string = string.replace('"', '')
            string = string.replace("'", "")
            return string
    
    def _check_destination(self, value_list):
        if value_list:
            object_list = []
            error_status = False
        
            for email in value_list:
                if not validators.email(email):
                    error_status = True
                    self.logger.error('Destination must be a valid email: {}'.format(email))
                else:
                    object_list.append(email)
                
            if not error_status:
                return object_list
            else:
                sys.exit(1)

    def _check_interval(self, value):
        if value:
            if re.match('^[0-9]+[smhd]', value):
                if value.endswith('s'):
                    return value[:-1]
                elif value.endswith('m'):
                    return int(value[:-1])*60
                elif value.endswith('h'):
                    return int(value[:-1])*60*60
                elif value.endswith('d'):
                    return int(value[:-1])*60*60*24
            elif value.isdigit():
                return value
            else:
                self.logger.error('Interval must be a digit or a digit with suffix: {}'.format(value))
                sys.exit(1)
    
    def _check_plugin(self, value):
        if value:
            if not value in self.plugins:
                self.logger.error('This plugin is not supported: {}'.format(value))
                sys.exit(1)
            else:
                return value
            
    def _check_regexp(self, content, regexp_list):
        if regexp_list:
            for regexp in regexp_list:
                pattern = re.compile(regexp.encode('utf-8'),re.IGNORECASE + re.UNICODE)
                if re.search(pattern, content):
                    self.logger.debug('Regexp was found: {}'.format(regexp))
                    return True
                else:
                    self.logger.debug('Regexp was not found: {}'.format(regexp))
                    return False
        else:
            self.logger.debug('Regexp list is empty: {}'.format(regexp))
            return False
 
    def _convert_encoding(self, data, new_coding = 'UTF-8'):
        encoding = chardet.detect(data)['encoding']

        if new_coding.upper() != encoding.upper():
            data = data.decode(encoding, data)
        else:
            data = data.decode(new_coding)

        self.logger.debug('Detected encoding: {}'.format(encoding))
        return data
 
    def _execute(self, execute, original_content, expanded_text_content, expanded_image_content):

        def delete(filename):
            try:
                os.remove(filename)
                self.logger.debug('Temporary file has been deleted: {}'.format(filename))
            except:
                self.logger.error('Cannot delete the temporary file: {}'.format(filename))

        def write(data):
            try:
                fd, filename = mkstemp(prefix='mosquito_')
                tfile = os.fdopen(fd, "w")
                tfile.write(data)
                tfile.close()
                self.logger.debug('Data has been written to temporary file: {}'.format(filename))
                return filename
            except:
                self.logger.error('Cannot write data to temporary file: {}'.format(filename))
                return None
        
        original_content_file = write(original_content)
        expanded_text_file = write(expanded_text_content)
        expanded_image_file = write(expanded_image_content)
        
        try:
            subprocess.call([execute, original_content_file, expanded_text_file ,expanded_image_file])
            self.logger.debug('Script has been executed: {}'.format(execute))
        except:
            self.logger.error('Cannot execute script with parameters: {}'.format(execute))
        finally:
            delete(original_content_file)
            delete(expanded_text_file)
            delete(expanded_image_file)

    def _grab(self, expanded_url, grab):
        if grab == 'image':
            try:
                driver = webdriver.PhantomJS()
                driver.set_window_size(1024, 768)
                driver.set_page_load_timeout(self.settings.grab_timeout)
                driver.get(expanded_url)
                return driver.get_screenshot_as_png()
            except Exception as warning:
                self.logger.warning('Cannot grab image from the URL: {} -> {}'.format(expanded_url, warning))
        elif grab == 'text':
            headers = {'User-Agent': self.settings.user_agent}
            
            try:
                page = requests.get(expanded_url, headers=headers, timeout=float(self.settings.grab_timeout))
                h2t = HTML2Text()
                h2t.ignore_links = True
                return h2t.handle(self._convert_encoding(page.content))
            except Exception as warning:
                self.logger.warning('Cannot grab text from the URL: {} -> {}'.format(expanded_url, warning))
                
    def _handle_content(self, source_id, original_content, expanded_url):
        config_data = self.db.list('all', source_id)
        plugin = config_data[0][2]
        source = config_data[0][3]
        destination_list = ast.literal_eval(config_data[0][4])
        regexp_action_list = ast.literal_eval(config_data[0][9])
        current_timestamp = time.mktime(datetime.utcnow().timetuple())
        
        self.logger.debug('Trying to process data')
            
        execute = None
        grab = None
        priority = None
        subject = None
        expanded_text_content = None
        expanded_image_content = None

        # Multiple headers support
        header_list = []
        # Add service headers
        header_list.append('X-mosquito-id:' + str(source_id))
        header_list.append('X-mosquito-plugin:' + str(plugin))
        header_list.append('X-mosquito-source:' + str(source))
        header_list.append('X-mosquito-expanded-url:' + str(expanded_url))

        # Check actions which were set for configuration
        for action in regexp_action_list:
            action_name = action.split('=')[0]
            action_value = action.split('=')[1]
                                
            if action_name == 'execute':
                execute = action_value
            elif action_name == 'grab':
                grab = action_value
            elif action_name == 'header':
                header_list.append(action_value)
            elif action_name == 'priority':
                priority = action_value
            elif action_name == 'subject':
                subject = action_value
                
        # Change priority
        if priority:                
            if priority == 'high':
                priority = '1'
            elif priority == 'normal':
                priority = '3'
            elif priority == 'low':
                priority = '5'
                
        # Change subject
        if subject:
            subject = subject + ' ' + original_content.split('\n', 1)[0]
        else:
            subject = original_content.split('\n', 1)[0]
            
        if subject and len(subject) > self.settings.subject_length:
            subject = subject[:self.settings.subject_length] + ' ...'
                                              
        # Add service data
        original_content = original_content + '\n\n---\n{}'.format(expanded_url)
                                              
        # Grab a remote content
        if grab == 'text' and expanded_url:
            expanded_text_content = self._grab(expanded_url, grab)
        elif grab == 'screenshot' and expanded_url:
            expanded_image_content = self._grab(expanded_url, grab)
        elif grab == 'full' and expanded_url:
            expanded_text_content = self._grab(expanded_url, 'text')
            expanded_image_content = self._grab(expanded_url, 'image')
                                                
        # Execute script
        if execute:
            self._execute(execute, original_content, expanded_text_content, expanded_image_content)
                                        
        # If a mail server is alive we:
        # 1. We will try send archived data
        # 2. If a mail server goes down in the middle of operation we just have to save data to archive
        if self.mail.active:       
            if not self.mail.send(destination_list, header_list, priority, subject, 
                                  original_content, expanded_text_content, 
                                  expanded_image_content):
                
                self.logger.warning('SMTP server is not available. Add data to the archive')
                self.db.add_archive(
                                    source_id, destination_list, header_list, priority, 
                                    subject, original_content, 
                                    expanded_text_content, expanded_image_content, 
                                    current_timestamp
                                    )                                                                       
        else:                      
            self.logger.warning('SMTP server is not available. Add data to the archive')
            self.db.add_archive(
                                source_id, destination_list, header_list, priority, 
                                subject, original_content,
                                expanded_text_content, expanded_image_content,
                                current_timestamp
                                )
                
    def _human_time(self, seconds):   
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
        archive_list = self.db.list_archive()

        for archive in archive_list:
            destination_list = ast.literal_eval(archive[2])
            header_list = archive[3]
            priority = archive[4]
            subject = archive[5]
            original_content = archive[6]
            expanded_text_content = archive[7]
            expanded_image_content = archive[8]
                
            if self.mail.send(destination_list, header_list, priority, subject, 
                              original_content, expanded_text_content, 
                              expanded_image_content):
                
                self.db.delete_archive(archive[0])
     
    def create(self, args):
        plugin = self._check_plugin(args.plugin)
        source = args.source
        destination_list = self._check_destination(args.destination)
        update_alert = self._check_interval(args.update_alert)
        update_interval = self._check_interval(args.update_interval)
        description = self._check_description(args.description)
        regexp_list = args.regexp
        regexp_action_list = args.regexp_action

        if not destination_list:
            self.logger.error('Destination is required')
            sys.exit(1)

        if regexp_action_list:
            for action in regexp_action_list:
                self._check_action(action)

        self.db.create('True', plugin , source, destination_list, update_alert, 
                        update_interval, description, regexp_list, 
                        regexp_action_list, '0', '0')

    def delete(self, args):
        if self._check_confirmation('Please, confirm the deletion'):
            for plugin in args.plugin:
                if plugin == 'all' or plugin in self.plugins:
                    for id in args.id:
                        self.db.delete(plugin, id)      
            
    def fetch(self, args):
        
        # Check if mosquito already running
        if os.path.exists(self.settings.lock_file):
            self.logger.error('Mosquito already running. The lock file exist: {}'.format(self.settings.lock_file))
            sys.exit(1)
        else:
            try:
                open(self.settings.lock_file, 'a').close()
            except Exception as error:
                self.logger.error('Cannot set lock: {}'.format(error))
                sys.exit(1)

        # Loop over configurations
        for plugin in args.plugin:
            for id in args.id:
                config_data = self.db.list(plugin, id)
            
                for data in config_data:
                    source_id = data[0]
                    config_enabled = data[1]
                    plugin = data[2]
                    source = data[3]
                    destination_list = ast.literal_eval(data[4])
                    update_alert = data[5]
                    update_interval = data[6]
                    regexp_list = ast.literal_eval(data[8])
                    config_timestamp = data[10]
                    current_timestamp = time.mktime(datetime.utcnow().timetuple())
                                     
                    if args.force or config_enabled == 'True':
                        if args.force or (current_timestamp - config_timestamp) > update_interval:
                            self.logger.info('Processing the configuration: {} -> {} -> {}'.format(source_id, plugin, source))
                            
                            if plugin == 'rss':
                                self.rss = MosquitoRSS(source)
                                posts = self.rss.fetch()
                                
                                if posts:
                                    count = 0
                                    
                                    for post in posts:
                                        post_timestamp = post[0]
                                        original_content = post[1]
                                        expanded_url = post[2]
                                        
                                        if (post_timestamp > config_timestamp):
                                            if self._check_regexp(original_content, regexp_list):
                                                self._handle_content(source_id, original_content, expanded_url)
                                                count += 1
                                        else:
                                            self.logger.debug('The message timestamp is lower than the config timestamp: {} -> {}'.format(post_timestamp, config_timestamp))
                                            
                                    self.logger.info('Data has been processed: {} -> {} -> {} -> {}'.format(source_id, plugin, source, count))

                            elif plugin == 'twitter':
                                self.twitter = MosquitoTwitter()
                                
                                if self.twitter.active:
                                    tweets = self.twitter.fetch(source)
                                    
                                    if tweets:
                                        count = 0
                                        
                                        for tweet in tweets:
                                            tweet_timestamp = tweet[0]
                                            original_content = tweet[1]
                                            expanded_url = tweet[2]
                                        
                                            if (tweet_timestamp > config_timestamp):
                                                if self._check_regexp(original_content, regexp_list):
                                                    self._handle_content(source_id, original_content, expanded_url)
                                                    count += 1
                                            else:
                                                self.logger.debug('The message timestamp is lower than the config timestamp: {} -> {}'.format(tweet_timestamp, config_timestamp))
                                                
                                        self.logger.info('Data has been processed: {} -> {} -> {} -> {}'.format(source_id, plugin, source, count))
                                else:
                                    self.logger.warning('Cannot load the configuration because the plugin is not active: {} -> {} -> {}'.format(source_id, plugin, source))
                            
                            if count > 0:
                                # Update timestamp for the configuration
                                self.db.update_timestamp(source_id, time.mktime(datetime.utcnow().timetuple()))
                                # Increase counter for the configuration
                                self.db.update_counter(source_id, count)
                            else:
                                # Check if we haven't received the new data during a specific interval
                                if current_timestamp > (config_timestamp + int(update_alert)):
                                    self.logger.warning('No new data for the configuration: {} -> {} -> {}'.format(source_id, plugin, source))
                                    self.mail.send(destination_list, None, None, '***No new data from the configuration***', '{} -> {} -> {}'.format(source_id, plugin, source), None, None)
                        else:
                            self.logger.info('Update interval has not been reached: {} -> {} -> {}'.format(source_id, plugin, source))
                    else:
                        self.logger.info('Configuration is disabled: {} -> {} -> {}'.format(source_id, plugin, source)) 
        
        try:
            os.remove(self.settings.lock_file)
        except:
            pass
        
    def list(self, args):
        table = [[
                  'ID', 'Enabled', 'Plugin', 'Source', 'Destination', 
                  'Alert', 'Interval', 'Desc', 'Regexp', 
                  'Regexp action', 'Last update', 'Count'
                ]]
        
        for plugin in args.plugin:
            for id in args.id:
                for data in self.db.list(plugin, id):
                    if len(data) > 0:                        
                        table.append([
                              data[0], data[1], data[2], '\n'.join(wrap(str(data[3]), 42)), 
                              '\n'.join(ast.literal_eval(data[4])), 
                              self._human_time(int(data[5])), 
                              self._human_time(int(data[6])), '\n'.join(wrap(str(data[7]), 30)), 
                              '\n'.join(ast.literal_eval(data[8])), 
                              '\n'.join(ast.literal_eval(data[9])), 
                              datetime.fromtimestamp(int(data[10])),
                              data[11]])
                    
        if len(table) > 1:
            table = AsciiTable(table)
            table.justify_columns[1] = 'center'
            table.justify_columns[2] = 'center'
            table.justify_columns[5] = 'center'
            table.justify_columns[6] = 'center'
            table.justify_columns[7] = 'center'
            table.justify_columns[10] = 'center'
            table.inner_row_border = True
            print table.table  
        else:
            self.logger.info('No configurations were found')
    
    def set(self, args):
        id_list = args.id
        enabled = args.enabled
        plugin = self._check_plugin(args.plugin)
        source = args.source
        destination_list = self._check_destination(args.destination)
        update_alert = self._check_interval(args.update_alert)
        update_interval = self._check_interval(args.update_interval)
        description = self._check_description(args.description)
        regexp_list = args.regexp
        regexp_action_list = args.regexp_action

        if not id_list:
            self.logger.error('ID is required')
            sys.exit(1)

        if regexp_action_list:
            for action in regexp_action_list:
                self._check_action(action)
            
        for id in id_list:
            config_data = self.db.list('all', id)
            
            if enabled != 'True' or enabled != 'False':
                enabled = config_data[0][1]
                
            if not plugin:
                plugin = config_data[0][2]
                
            if not source:
                source = config_data[0][3]
                timestamp = config_data[0][10]
                counter = config_data[0][11]
            else:
                timestamp = 0
                counter = 0
                
            if not destination_list:
                destination_list = config_data[0][4]
                
            if not update_alert:
                update_alert = config_data[0][5]
                
            if not update_interval:
                update_interval = config_data[0][6]
                
            if not description:
                description = config_data[0][7]
                
            if not regexp_list:
                regexp_list = config_data[0][8]
                
            if not regexp_action_list:
                regexp_action_list = config_data[0][9]
        
            self.db.update(id, enabled, plugin , source, destination_list, 
                           update_alert, update_interval, description, regexp_list, 
                           regexp_action_list, timestamp, counter)
    
    def __init__(self):
        # Get the settings
        self.settings = MosquitoSettings()
        
        coloredlogs.DEFAULT_LOG_FORMAT = '%(asctime)s %(name)s %(levelname)s %(message)s'
        coloredlogs.install(level=self.settings.verbose)    
        self.logger = logging.getLogger('[MAIN]')

        # Hide HTTP requests
        if self.settings.verbose.upper() != 'DEBUG': 
            logging.getLogger("requests").setLevel(logging.WARNING)

        # Hide feedparser deprecation warnings
        warnings.filterwarnings("ignore", category=DeprecationWarning)

        # List of supported plugins
        self.plugins = ['twitter', 'rss']

        self.db = MosquitoDB()
        self.help = MosquitoHelp()
        self.mail = MosquitoMail()
        
        # Try to send archived data
        if self.mail.active:
            self._send_archive()
        
        # Create root parser
        parser = argparse.ArgumentParser(prog='mosquito', description=self.help.description)
        subparsers = parser.add_subparsers()
        
        # Create 'create' parser
        parser_create = subparsers.add_parser('create', help=self.help.create)
        parser_create.add_argument('--plugin', required=True, 
                                          help='a plugin name e.g. rss, twitter')
        parser_create.add_argument('--source', required=True, 
                                          help='see documentation')
        parser_create.add_argument('--destination', nargs='+', default=self.settings.destination, 
                                          help='space separated list of email addresses')
        parser_create.add_argument('--update-alert', default=self.settings.update_alert,
                                          help='update alert e.g. 1s, 2m, 3h, 4d')  
        parser_create.add_argument('--update-interval', default=self.settings.update_interval,
                                          help='update interval e.g. 1s, 2m, 3h, 4d')
        parser_create.add_argument('--description', nargs='+', type=lambda s: unicode(s, 'utf8'),
                                          help='description text')
        parser_create.add_argument('--regexp', nargs='+', type=lambda s: unicode(s, 'utf8'), 
                                          help='see documentation')
        parser_create.add_argument('--regexp-action', nargs='+',
                                          help='see documentation')
        parser_create.set_defaults(func=self.create)       
        
        # Create 'delete' parser
        parser_delete = subparsers.add_parser('delete', help=self.help.delete)
        parser_delete.add_argument('--plugin', nargs='+', default=['all'], 
                                          help='a space separated list of plugins')
        parser_delete.add_argument('--id', nargs='+', default=['all'], 
                                          help='a space separated list of IDs')
        parser_delete.set_defaults(func=self.delete)
        
        # Create 'fetch' parser
        parser_fetch = subparsers.add_parser('fetch', help=self.help.fetch)
        parser_fetch.add_argument('--plugin', nargs='+', default=['all'], 
                                          help='a space separated list of plugins')
        parser_fetch.add_argument('--id', nargs='+', default=['all'], 
                                          help='a space separated list of IDs')
        parser_fetch.add_argument('--force', action='store_true', 
                                          help='ignore update interval')
        parser_fetch.set_defaults(func=self.fetch)
        
        # Create 'list' parser
        parser_list = subparsers.add_parser('list', help=self.help.list)
        parser_list.add_argument('--plugin', nargs='+', default=['all'],  
                                          help='a space separated list of plugins')
        parser_list.add_argument('--id', nargs='+', default=['all'], 
                                          help='a space separated list of IDs')
        parser_list.set_defaults(func=self.list)        

        # Create 'set' parser
        parser_set = subparsers.add_parser('set', help=self.help.set)
        parser_set.add_argument('--id', nargs='+', 
                                          help='a space separated list of IDs')
        parser_set.add_argument('--enabled',
                                          help='')
        parser_set.add_argument('--plugin',
                                          help='a plugin name e.g. rss, twitter')
        parser_set.add_argument('--source', 
                                          help='see documentation')
        parser_set.add_argument('--destination', nargs='+', 
                                          help='space separated list of email addresses')
        parser_set.add_argument('--update-alert',
                                          help='update alert e.g. 1s, 2m, 3h, 4d')  
        parser_set.add_argument('--update-interval',
                                          help='update interval e.g. 1s, 2m, 3h, 4d')
        parser_set.add_argument('--description', nargs='+', type=lambda s: unicode(s, 'utf8'),
                                          help='description text')
        parser_set.add_argument('--regexp', nargs='+', type=lambda s: unicode(s, 'utf8'), 
                                          help='see documentation')
        parser_set.add_argument('--regexp-action', nargs='+',
                                          help='see documentation')
        parser_set.set_defaults(func=self.set)
       
        results = parser.parse_args()
        results.func(results)

def main():
    Mosquito()
    
if __name__ == '__main__':
    main()
    
    