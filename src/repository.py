#!/usr/bin/env python

"""
Copyright (c) Build Your Own Arch Linux Repository developers
See the file 'LICENSE' for copying permission
"""

import sys

from core.app import app
from package import Package


class Repository():
    def make(self):
        # If there is no package to update, we skip the make.
        if len(app.need_to_update) == 0:
            return

        for name in app.need_to_update:
            self._compile(name)

    def _compile(self, name):
        package = Package(
            name=name,
            is_dependency=False,
            is_status_checking=False
        )

        package.clean_directory()
        package.validate_configuration()

        if not package.has_error():
            package.pull_repository()
            package.set_real_version()
            package.set_variable()
            package.validate_build()

        package._make()

        sys.exit()


repository = Repository()
