#!/usr/bin/env python3

import logging
import os
import subprocess

from uuid import uuid4

from mosquito.settings import MosquitoSettings


class MosquitoExec(object):
    def __init__(self, id=None, queue=None):
        self.id = id
        self.queue = queue

        self.logger = logging.getLogger('[EXEC]')
        self.settings = MosquitoSettings()

    def _delete(self, filename):
        if filename:
            try:
                os.remove(filename)
                self._logger(
                    "debug",
                    "Temporary file has been deleted: {}".format(filename)
                )
            except Exception as error:
                self._logger(
                    "warning",
                    "Cannot delete the temporary file: {} -> {}".format(filename, error)
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

    def _write(self, filename, data, mode):
        if data:
            try:
                f = open(filename, mode)
                f.write(data)
                f.close()

                self._logger(
                    "debug",
                    "Data has been written to a temporary file: {}".format(filename)
                )

            except Exception as error:
                self._logger(
                    "error",
                    "Cannot write data to a temporary file: {} -> {}".format(filename, error)
                )

    def run(self, config_id, exec_path, timestamp, tags, title, html, screenshot, text, images):
        working_path = self.settings.exec_path + "/" + str(config_id) + "/" + str(uuid4())

        if not os.path.isdir(working_path):
            try:
                os.makedirs(working_path)
            except Exception as e:
                self._logger(
                    "error",
                    "Cannot create a temporary directory where data will be processed: {}".format(e)
                )

                return False

        if not tags:
            tags = ["None"]

        self._write(working_path + "/title.txt", title, "w")
        self._write(working_path + "/content.html", html, "w")
        self._write(working_path + "/screenshot.png", screenshot, "wb")
        self._write(working_path + "/content.txt", text, "w")

        if images:
            if not os.path.isdir(working_path + "/images"):
                try:
                    os.makedirs(working_path + "/images")
                except Exception as e:
                    self._logger(
                        "error",
                        "Cannot create a temporary directory where images will be saved: {}".format(e)
                    )

            for image in images:
                image_data = image[0]
                image_format = image[1]

                filename = working_path + "/images/" + str(images.index(image)) + "." + image_format.lower()
                self._write(filename, image_data, "wb")

        try:
            subprocess.call(
                [
                    exec_path,
                    str(timestamp),
                    ",".join(tags),
                    working_path
                ]
            )

            self._logger(
                "debug",
                "Script has been executed: {}".format(exec_path)
            )

        except Exception as error:
            self._logger(
                "warning",
                "Script execution was finished with errors: {} -> {}".format(exec_path, error)
            )

