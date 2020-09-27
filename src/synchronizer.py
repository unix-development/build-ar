#!/usr/bin/env python

"""
Copyright (c) Build Your Own Arch Linux Repository developers
See the file 'LICENSE' for copying permission
"""

import os
import sys
import ctypes
import multiprocessing

from core.app import app
from package import Package
from util.process import execute
from util.process import output
from util.style import bold


class Synchronizer():
    """
    Main Synchronizer class used to scan packages defined into pkg
    directory an update.
    """
    def __init__(self):
        """
        Setting synchronizer variables.
        """
        self.is_dependency = False
        self.error = []
        self.need_update = []
        self.to_ensure = []
        self.status_error = 0;
        self.status_need_update = 0;

    def scan(self):
        """
        Scanning packages defined in pkg directory. If there is already
        packages to update, we skip the scan.
        """
        if len(app.need_update) > 0:
            print(bold("Prepare packages... Done"))
            self.status_need_update = len(app.need_update)
            self._print_update_section()
            return

        self._prepare()
        self._execute(app.package)
        self._print_update_section()
        self._print_error_section()

        if len(self.to_ensure) > 0:
            self.is_dependency = True
            print(bold("Prepare missing dependencies..."))

            while len(self.to_ensure) > 0:
                dependencies = self.to_ensure.copy()
                # Creates the dependency if it's missing.
                for dependency in dependencies:
                    print("  -> " + dependency)
                    app.package.append(dependency)
                    self._create_missing_dependency(dependency)
                    self._check_status(dependency)
                    self.to_ensure.remove(dependency)
                # Parses the response after missing dependency is
                # added to dependencies.
                for dependency in dependencies:
                    response = self.result[dependency]
                    self._push_response(dependency, response)

        app.system.write("need_update", self.need_update)
        app.need_update = self.need_update

    def _create_missing_dependency(self, dependency):
        """
        Creating missing package dependency.
        """
        directory = os.path.join(app.path.pkg, dependency)
        execute(f"mkdir {directory};")

        with open(f"{directory}/package.py", "w") as f:
            f.write("%s\n%s\n\n%s\n%s" % (
                "#!/usr/bin/env python",
                "# -*- coding:utf-8 -*-",
                ("name = \"%s\"" % dependency),
                ("source = \"https://aur.archlinux.org/%s.git\"" % dependency)
            ))

    def _prepare(self):
        """
        Preparing multiprocessing and printing how many package was found.
        """
        self.length = len(app.package)
        self.manager = multiprocessing.Manager()
        self.current = multiprocessing.Value(ctypes.c_int, 0)
        self.result = self.manager.dict()

        s = "s" if self.length > 1 else ""
        print(bold("Prepare packages... Done"))
        print(f"  {str(self.length)} package{s} founds")

    def _print_update_section(self):
        """
        Printing how many packages need to be updated.
        """
        need_update = str(self.status_need_update)
        s = "s" if self.status_need_update > 1 else ""
        print(f"  {need_update} package{s} need update")

    def _print_error_section(self):
        """
        Printing packages integrity.
        """
        if self.status_error == 0:
            return

        error = str(self.status_error)
        s = "s" if self.status_error > 1 else ""
        print(bold("Validating integrity... Done"))
        print(f"  {error} package{s} have problem")

    def _execute(self, packages):
        """
        Creating multiprocessing to analyzing packages response.
        """
        processes = []

        self._print()

        for name in packages:
            p = multiprocessing.Process(target=self._check_status, args=(name,))
            processes.append(p)
            p.start()

        for process in processes:
            process.join()

        for name in self.result:
            response = self.result[name]
            self._push_response(name, response)

    def _push_response(self, name, response):
        """
        Pushing package response.
        """
        self.to_ensure = self.to_ensure + response["dependencies"]

        if response["has_error"]:
            self.status_error = self.status_error + 1
            self.error.append(response)
        elif response["need_update"]:
            self.status_need_update = self.status_need_update + 1
            self.need_update.append(name)

    def _check_status(self, name):
        """
        Checking and setting package status.
        """
        to_ensure = []
        package = Package(
            name=name,
            is_dependency=False,
            is_status_checking=True
        )

        package.clean_directory()
        package.validate_configuration()

        if not package.has_error():
            package.pull_repository()
            package.set_real_version()
            package.set_variable()
            package.validate_build()

        if not package.has_error() and not self.is_dependency:
            to_ensure = package.verify_dependencies()

        self.current.value += 1
        self.result[package.name] = {
            "error": package.error,
            "has_error": package.has_error(),
            "need_update": package.need_update(),
            "dependencies": to_ensure
        }

        self._print()

    def _print(self):
        """
        Printing message on same line.
        """
        if self.is_dependency:
            return

        if self.current.value == self.length:
            achivement = "Done"
            end = '\n'
        else:
            achivement = str(round(self.current.value / (self.length) * 100)) + "%"
            end = '\r'

        print(bold(f"Synchronizing packages... {achivement}"), end=end)


synchronizer = Synchronizer()
