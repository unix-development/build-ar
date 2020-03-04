#!/usr/bin/env python

"""
Copyright (c) Build Your Own Arch Linux Repository developers
See the file 'LICENSE' for copying permission
"""

import os
import sys
import multiprocessing

from imp import load_source

from core.app import app
from package import Package
from util.process import execute
from util.process import output


class Synchronizer():
    def scan(self):
        sys.path.append(app.path.pkg)

        self._prepare()
        self._execute()
        self._print_update_section()
        self._print_error_section()

    def _prepare(self):
        self.current = 0
        self.error = []
        self.length = len(app.package)

        # This variables define the status of the repository.
        self.status = {
            "error": 0,
            "need_update": 0
        }

        print("Prepare packages... Done")
        print(f"  {str(self.length)} packages founds")

    def _print_update_section(self):
        need_update = str(self.status["need_update"])
        s = "s" if self.status["need_update"] > 1 else ""
        print(f"  {need_update} package{s} need update")

    def _print_error_section(self):
        if self.status["error"] == 0:
            return

        error = str(self.status["error"])
        s = "s" if self.status["error"] > 1 else ""
        print("Validating integrity... Done")
        print(f"  {error} package{s} have problem")

    def _execute(self):
        pool = multiprocessing.Pool()
        process = pool.imap_unordered(self._check_status, app.package)
        pool.close()

        for response in process:
            if response:
                self._print()
                self.current = self.current + 1

                if response["status"] == "error":
                    self.status["error"] = self.status["error"] + 1
                    self.error.append(response)
                elif response["need_update"]:
                    self.status["need_update"] = self.status["need_update"] + 1

        pool.join()

    def _check_status(self, name):
        package = Package(
            name=name,
            is_dependency=False,
            is_status_checking=True
        )

        package.clean_directory()
        package.validate_configuration()

        if package.status != "error":
            package.pull_repository()
            package.set_real_version()
            package.set_variable()
            package.validate_build()

        return {
            "name": package.name,
            "status": package.status,
            "error": package.error,
            "need_update": package.need_update()
        }

    def _print(self):
        """
        Print message on same line.
        """
        if self.current == self.length - 1:
            achivement = "Done"
            end = '\n'
        else:
            achivement = str(round(self.current / (self.length - 1) * 100)) + "%"
            end = '\r'

        print(f"Synchronizing packages.. {achivement}", end=end)


synchronizer = Synchronizer()
