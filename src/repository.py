#!/usr/bin/env python

"""
Copyright (c) Build Your Own Arch Linux Repository developers
See the file 'LICENSE' for copying permission
"""

import sys

from core.app import app
from environment import environment
from package import Package
from util.process import execute
from util.style import bold


class Repository():
    """
    Main repository class used to compile packages and add it to the
    database repository.
    """
    need_update = []

    def make(self):
        """
        Scanning all packages and compile it.
        If there is no package to update, we skip the make.
        """
        if len(app.need_update) == 0:
            return

        self.need_update = app.need_update.copy()

        for name in app.need_update:
            print(bold(f"Build {name}:"))
            self._compile(name)
            print("")

    def _compile(self, name):
        """
        Creating new package instance by the given name and compile it.
        """
        package = Package(
            name=name,
            is_dependency=False,
            is_status_checking=False
        )

        package.clean_directory()
        package.validate_configuration()

        if not package.has_error():
            package.pull_repository()
            package.set_variable()
            package.validate_build()

        if not package.has_error():
            package.make()

        self._push_to_database(name)
        self.need_update.remove(name)

        app.system.write("need_update", self.need_update)

    def _push_to_database(self, name):
        """
        Pushing package to database repository.
        """
        execute(f"""
        repo-add --remove \
            {app.path.mirror}/{app.database}.db.tar.gz \
            {app.path.mirror}/{name}-*.pkg.tar.xz
        """)

        environment.syncronize_database()


repository = Repository()
