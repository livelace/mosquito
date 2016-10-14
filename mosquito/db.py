#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Module for configurations database """

import os
import logging
import sys
import sqlite3

class MosquitoDB(object):
    
    def _sql(self, request):
        cursor = self.conn.cursor()
        cursor.execute(request)       
        results = cursor.fetchall()
        self.conn.commit()
        return results 
    
    def __init__(self):
        # Set logger
        self.logger = logging.getLogger('[DB]')

        self.mosquito_db = os.path.join(os.environ['HOME'], '.mosquito.sqlite3')
        
        if not os.path.exists(self.mosquito_db):
            self.logger.debug('Trying to initialize the database')
            
            try:
                self.conn = sqlite3.connect(self.mosquito_db)
                
                self._sql('''CREATE TABLE configuration (
                                                id INTEGER PRIMARY KEY NOT NULL,
                                                enabled TEXT NOT NULL,
                                                plugin TEXT NOT NULL,
                                                source TEXT NOT NULL,
                                                destination TEXT NOT NULL,
                                                update_alert INTEGER NOT NULL,
                                                update_interval INTEGER NOT NULL,
                                                description TEXT,
                                                regexp TEXT,
                                                regexp_action TEXT,
                                                timestamp INTEGER NOT NULL,
                                                counter INTEGER
                                                )''')
                
                self._sql('''CREATE TABLE archive (
                                            id INTEGER PRIMARY KEY NOT NULL,
                                            source_id INTEGER NOT NULL,
                                            destination TEXT NOT NULL,
                                            header TEXT,
                                            priority TEXT,
                                            subject TEXT,
                                            original_content TEXT,
                                            expanded_text_content TEXT,
                                            expanded_image_content BLOB,
                                            timestamp INTEGER NOT NULL
                                            )''')   
                
                self.logger.debug('Database has been initialized')             
            except:
                self.logger.error('Cannot initialize the database')
                sys.exit(1)
        else:  
            try:
                self.conn = sqlite3.connect(self.mosquito_db)
                try:
                    self.conn.execute('VACUUM;')
                    self.logger.debug('Database has been vacuumed')
                except Exception as error:
                    self.logger.error('Cannot clean the database: {}'.format(error))
            except:
                self.logger.error('Cannot connect to the database')
                sys.exit(1)
                
    def add_archive(self, source_id, destination_list, header, priority, subject, 
                    original_content, expanded_text_content, 
                    expanded_image_content, timestamp):

        try:
            if expanded_image_content:
                expanded_image_content = sqlite3.Binary(expanded_image_content)

            sql = '''INSERT INTO archive (
                                        source_id, destination, header, priority, 
                                        subject,original_content, expanded_text_content, 
                                        expanded_image_content, timestamp) 
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);'''
         
            self.conn.execute(sql,[source_id, str(destination_list), header, priority, 
                               subject, original_content, expanded_text_content, 
                               expanded_image_content, timestamp])    
            self.conn.commit()
        except Exception as error:
            self.logger.error('Cannot archive data to the database: {}'.format(error))
        
    def create(self, enabled, plugin, source, destination_list, update_alert, 
               update_interval, description, regexp_list, regexp_action_list, 
               timestamp, counter):
        
        try:
            sql = '''INSERT INTO configuration (
                                                enabled, plugin, source, destination, 
                                                update_alert, update_interval, 
                                                description, regexp, regexp_action, 
                                                timestamp, counter
                                                ) VALUES (?,?,?,?,?,?,?,?,?,?,?);'''
        
            self.conn.execute(sql,[enabled, plugin, source, str(destination_list), 
                               update_alert, update_interval, description, 
                               str(regexp_list), str(regexp_action_list), 
                               timestamp, counter])
            self.conn.commit()
            self.logger.info('The configuration has been created: {} -> {}'.format(plugin, source))
        except Exception as error:
            self.logger.error('Cannot create the configuration: {}'.format(error))
        
    def delete(self, plugin, id):
        if plugin == 'all' and id == 'all':
            try:
                sql = "DELETE FROM configuration"
                self._sql(sql)
                self.logger.info('All configurations have been deleted')
            except:
                self.logger.error('Cannot delete configuration: {} -> {}'.format(plugin, id))
                
        elif plugin == 'all' and id != 'all':
            try:
                sql = "DELETE FROM configuration WHERE id = '{}'".format(id)
                self._sql(sql)
                self.logger.info('The configuration has been deleted: {} -> {}'.format(plugin, id))
            except:
                self.logger.error('Cannot delete configuration: {} -> {}'.format(plugin, id))
            
        elif plugin != 'all' and id == 'all':
            try:
                sql = "DELETE FROM configuration WHERE plugin = '{}'".format(plugin)
                self._sql(sql)        
                self.logger.info('All configurations for specific plugin have been deleted: {}'.format(plugin))
            except:
                self.logger.error('Cannot delete configurations for specific plugin: {}'.format(plugin))
        
        elif plugin != 'all' and id != 'all':
            try:
                sql = "DELETE FROM configuration WHERE plugin = '{}' AND id = '{}'".format(plugin, id)
                self._sql(sql)
                self.logger.info('The configuration has been deleted: {} -> {}'.format(plugin, id))
            except:
                self.logger.error('Cannot delete configuration: {} -> {}'.format(plugin, id))
   
    def delete_archive(self, id):
        try:
            sql = "DELETE FROM archive WHERE id = '{}'".format(id)
            self._sql(sql)
        except Exception as error:
            self.logger.error('Cannot delete data from the archive: {} '.format(error))
                   
    def list(self, plugin, id):
        try:
            if plugin == 'all' and id == 'all':
                sql = "SELECT * FROM configuration"
                return self._sql(sql)    
            elif plugin == 'all' and id != 'all':
                sql = "SELECT * FROM configuration WHERE id = '{}'".format(id)
                return self._sql(sql)
            elif plugin != 'all' and id == 'all':
                sql = "SELECT * FROM configuration WHERE plugin = '{}'".format(plugin)
                return self._sql(sql)
            elif plugin != 'all' and id != 'all':
                sql = "SELECT * FROM configuration WHERE plugin = '{}' AND id = '{}'".format(plugin, id)
                return self._sql(sql)
        except Exception as error:
            self.logger.error('Cannot get the list of configurations: {}'.format(error))
 
    def list_archive(self):
        try:
            sql = "SELECT * FROM archive"
            return self._sql(sql)
        except Exception as error:
            self.logger.error('Cannot get the list of archives: {}'.format(error))

    def update(self, id, enabled, plugin, source, destination_list, update_alert, 
               update_interval, description, regexp_list, regexp_action_list, 
               timestamp, counter):
        
        try:
            sql = '''UPDATE configuration SET enabled=?, plugin=?, source=?, 
                                    destination=?, update_alert=?, 
                                    update_interval=?, description=?, 
                                    regexp=?, regexp_action=?, timestamp=?, 
                                    counter=? WHERE id=?;'''
        
            self.conn.execute(sql,[enabled, plugin, source, str(destination_list), 
                               update_alert, update_interval, description, 
                               str(regexp_list), str(regexp_action_list), 
                               timestamp, counter, id])
            self.conn.commit()
            self.logger.info('The configuration has been updated: {} -> {}'.format(plugin, source))
        except Exception as error:
            self.logger.error('Cannot update the configuration: {}'.format(error))

    def update_counter(self, id, count):
        try:
            sql = "UPDATE configuration SET counter = counter + '{}' WHERE id = '{}'".format(count, id)
            self._sql(sql)
        except Exception as error:
            self.logger.error('Cannot update the counter for the configuration: {}'.format(error))
 
    def update_timestamp(self, id, timestamp):
        try:
            sql = "UPDATE configuration SET timestamp = '{}' WHERE id = '{}'".format(timestamp, id)
            self._sql(sql)
        except Exception as error:
            self.logger.error('Cannot update the timestamp for the configuration: {}'.format(error))


