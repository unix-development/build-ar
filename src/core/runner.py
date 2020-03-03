#!/usr/bin/env python

"""
Copyright (c) Build Your Own Arch Linux Repository developers
See the file 'LICENSE' for copying permission
"""

import sys

from core.app import app


class Runner():
    parameters = dict()

    def set(self, name, runners):
        if type(runners) is list:
            self.parameters[name] = runners
        else:
            self.parameters[name] = [runners]

    def execute(self):
        if not app.runner:
            return

        elif app.runner not in self.parameters:
            return

        for runner in self.parameters[app.runner]:
            runner()


runner = Runner()
