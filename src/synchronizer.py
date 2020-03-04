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


class Synchronizer():
    error = []
    need_update = []
    dependencies_to_ensure =[]
    is_dependency = False

    # This variables define the status of the repository.
    status = {
        "error": 0,
        "need_update": 0
    }

    def scan(self):
        self._prepare()
        self._execute(app.package)

        # Print informations about packages.
        self._print_update_section()
        self._print_error_section()

        if len(self.dependencies_to_ensure) > 0:
            self.is_dependency = True
            print("Prepare missing dependencies...")

            while len(self.dependencies_to_ensure) > 0:
                dependencies = self.dependencies_to_ensure.copy()

                # Create the dependency.
                for dependency in dependencies:
                    print("  -> " + dependency)
                    app.package.append(dependency)
                    self._create_missing_dependency(dependency)
                    self._check_status(dependency)
                    self.dependencies_to_ensure.remove(dependency)

                # Parse the response.
                for dependency in dependencies:
                    response = self.result[dependency]
                    self._push_response(dependency, response)

        app.system.write("need_update", self.need_update)

    def _create_missing_dependency(self, dependency):
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
        self.length = len(app.package)

        self.manager = multiprocessing.Manager()
        self.current = multiprocessing.Value(ctypes.c_int, 0)
        self.result = self.manager.dict()

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

    def _execute(self, packages):
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
        self.dependencies_to_ensure = self.dependencies_to_ensure + response["dependencies"]

        if response["has_error"]:
            self.status["error"] = self.status["error"] + 1
            self.error.append(response)
        elif response["need_update"]:
            self.status["need_update"] = self.status["need_update"] + 1
            self.need_update.append(name)

    def _check_status(self, name):
        dependencies_to_ensure = []
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
            dependencies_to_ensure = package.verify_dependencies()

        self.result[package.name] = {
            "error": package.error,
            "has_error": package.has_error(),
            "need_update": package.need_update(),
            "dependencies": dependencies_to_ensure
        }

        self._print()
        self.current.value += 1

    def _print(self):
        """
        Print message on same line.
        """
        if self.is_dependency:
            return

        if self.current.value == self.length - 1:
            achivement = "Done"
            end = '\n'
        else:
            achivement = str(round(self.current.value / (self.length - 1) * 100)) + "%"
            end = '\r'

        print(f"Synchronizing packages... {achivement}", end=end)


synchronizer = Synchronizer()
