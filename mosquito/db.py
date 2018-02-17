#!/usr/bin/env python3

import os
import logging
import sys
import sqlite3


class MosquitoDB(object):

    def __init__(self, id=None, queue=None):
        self.id = id
        self.queue = queue

        self.db = os.path.join(os.environ['HOME'], '.mosquito.sqlite3')
        self.logger = logging.getLogger('[DB]')

        if not os.path.exists(self.db):
            self.logger.debug('Trying to initialize a database')
            
            try:
                self._sql_query(
                    """CREATE TABLE configuration (
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
                                                counter INTEGER,
                                                alert_timestamp INTEGER NOT NULL,
                                                images_settings TEXT
                    )
                    """
                )
                
                self._sql_query(
                    """CREATE TABLE archive (
                                            id INTEGER PRIMARY KEY NOT NULL,
                                            source_id INTEGER NOT NULL,
                                            destination TEXT NOT NULL,
                                            header TEXT,
                                            priority TEXT,
                                            subject TEXT,
                                            original_content TEXT,
                                            grabbed_html TEXT,
                                            grabbed_screenshot BLOB,
                                            grabbed_text TEXT,
                                            timestamp INTEGER NOT NULL
                    )
                    """
                )
                
                self._logger(
                    "debug",
                    "Database has been initialized: {}".format(self.db)
                )

            except Exception as error:
                self._logger(
                    "error",
                    "Cannot initialize a database: {}".format(error)
                )
                sys.exit(1)

    def _logger(self, level, message):
        """ Log with logger, or put message to a queue """

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

    def _sql_query(self, request):
        """ Execute SQL query """

        try:
            conn = sqlite3.connect(self.db)
            cursor = conn.cursor()
            cursor.execute(request)
            results = cursor.fetchall()
            conn.commit()

            return results

        except Exception as error:
            self._logger(
                "error",
                "SQL query was failed: {}".format(error)
            )

            return False

    def add_archive(self, config_id, destinations, headers, priority, subject, original_content, grabbed_html,
                    grabbed_screenshot, grabbed_text, timestamp):

        try:
            if grabbed_screenshot:
                grabbed_screenshot = sqlite3.Binary(grabbed_screenshot)

            sql = """INSERT INTO archive (
                                        source_id, destination, header, priority, 
                                        subject, original_content, grabbed_html, 
                                        grabbed_screenshot, grabbed_text, timestamp) 
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"""

            conn = sqlite3.connect(self.db)
            conn.execute(sql, [config_id, str(destinations), str(headers), priority, subject, original_content,
                               grabbed_html, grabbed_screenshot, grabbed_text, timestamp])
            conn.commit()

        except Exception as error:
            self._logger(
                "error",
                "Cannot archive data to the database: {}".format(error)
            )
        
    def create(self, enabled, plugin, source, destination, update_alert, update_interval, description, regex,
               regex_action, timestamp, counter, alert_timestamp, images_settings):
        
        try:
            sql = """INSERT INTO configuration (
                                                enabled, plugin, source, destination, 
                                                update_alert, update_interval, 
                                                description, regexp, regexp_action, 
                                                timestamp, counter, alert_timestamp, images_settings
                                                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?);"""

            conn = sqlite3.connect(self.db)
            conn.execute(sql, [enabled, plugin, source, str(destination), update_alert, update_interval, description,
                               str(regex), str(regex_action), timestamp, counter, alert_timestamp, str(images_settings)])
            conn.commit()

            self._logger(
                "info",
                "Configuration has been created: {} -> {}".format(plugin, source)
            )

        except Exception as error:
            self._logger(
                "error",
                "Cannot create configuration: {}".format(error)
            )
        
    def delete(self, plugin, id):
        if plugin:
            query = "DELETE FROM configuration WHERE plugin = '{}'".format(plugin)
        elif id:
            query = "DELETE FROM configuration WHERE id = '{}'".format(id)

        results = self._sql_query(query)

        if isinstance(results, list):
            if plugin:
                self._logger(
                    "info",
                    "Plugin specific configurations were deleted: {}".format(plugin)
                )
            else:
                self._logger(
                    "info",
                    "Configuration has been deleted: {}".format(id)
                )

            return True

        else:
            if plugin:
                self._logger(
                    "error",
                    "Cannot delete plugin specific configurations: {}".format(plugin)
                )
            else:
                self._logger(
                    "error",
                    "Cannot delete configuration: {}".format(id)
                )

            return False

    def delete_archive(self, id):
        query = "DELETE FROM archive WHERE id = '{}'".format(id)
        results = self._sql_query(query)

        if isinstance(results, list):
            self._logger(
                "debug",
                "Archived record has been deleted: {}".format(id)
            )

            return True

        else:
            self._logger(
                "error",
                "Cannot delete archived record: {}".format(id)
            )

            return False

    def clean(self):
        try:
            conn = sqlite3.connect(self.db)
            conn.execute('VACUUM;')

            self._logger(
                "debug",
                "Database has been vacuumed"
            )

        except Exception as error:
            self._logger(
                "error",
                "Cannot clean database: {}".format(error)
            )
                   
    def list(self, plugin, id):
        if plugin == 'all' and id == 'all':
            query = "SELECT * FROM configuration"
        elif plugin == 'all' and id != 'all':
            query = "SELECT * FROM configuration WHERE id = '{}'".format(id)
        elif plugin != 'all' and id == 'all':
            query = "SELECT * FROM configuration WHERE plugin = '{}'".format(plugin)

        results = self._sql_query(query)

        if isinstance(results, list):

            return results

        else:
            self._logger(
                "error",
                "Cannot retrieve configurations from database"
            )

            return False
 
    def list_archive(self):
        query = "SELECT * FROM archive"
        results = self._sql_query(query)

        if isinstance(results, list):
            if len(results) > 0:
                self._logger(
                    "debug",
                    "Archived records have been retrieved: {}".format(len(results))
                )

                return results

            elif len(results) == 0:
                self._logger(
                    "debug",
                    "There are no archived records. Skipping sending archived records."
                )

                return True

        else:
            self._logger(
                "error",
                "Cannot get archived data!"
            )

            return False

    def update(self, id, enabled, plugin, source, destination, update_alert, update_interval, description,
               regex, regex_action, timestamp, counter, alert_timestamp, images_settings):

        try:
            query = """UPDATE configuration SET enabled=?, plugin=?, source=?, destination=?, update_alert=?, 
                      update_interval=?, description=?, regexp=?, regexp_action=?, timestamp=?, counter=?,
                       alert_timestamp=?, images_settings=? WHERE id=?;"""

            conn = sqlite3.connect(self.db)
            conn.execute(query, [enabled, plugin, source, str(destination), update_alert, update_interval,
                                 description, str(regex), str(regex_action), timestamp, counter, alert_timestamp,
                                 str(images_settings), id])
            conn.commit()

            self._logger(
                "info",
                "Configuration has been updated: {}".format(id)
            )

        except Exception as error:
            self._logger(
                "error",
                "Cannot update configuration: {}".format(error)
            )

    def update_counter(self, id, count):
        query = "UPDATE configuration SET counter = counter + '{}' WHERE id = '{}'".format(count, id)
        results = self._sql_query(query)

        if isinstance(results, list):
            self._logger(
                "debug",
                "Configuration counter has been updated: {}".format(id)
            )

            return True

        else:
            self._logger(
                "error",
                "Cannot update configuration's counter: {}".format(id)
            )

            return False
 
    def update_timestamp(self, id, timestamp):
        query = "UPDATE configuration SET timestamp = '{}' WHERE id = '{}'".format(timestamp, id)
        results = self._sql_query(query)

        if isinstance(results, list):
            self._logger(
                "debug",
                "Configuration timestamp has been updated: {}".format(id)
            )

            return True

        else:
            self._logger(
                "error",
                "Cannot update configuration's timestamp: {}".format(id)
            )

            return False

    def update_alert_timestamp(self, id, timestamp):
        query = "UPDATE configuration SET alert_timestamp = '{}' WHERE id = '{}'".format(timestamp, id)
        results = self._sql_query(query)

        if isinstance(results, list):
            self._logger(
                "debug",
                "Alert timestamp has been updated: {}".format(id)
            )

            return True

        else:
            self._logger(
                "error",
                "Cannot update alert's timestamp: {}".format(id)
            )

            return False
