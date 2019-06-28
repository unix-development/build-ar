#!/usr/bin/env python

"""
Copyright (c) Build Your Own Arch Linux Repository developers
See the file 'LICENSE' for copying permission
"""

import sys


class Runner():
    commands = dict()

    def set(self, abstract, runners):
        self.commands[abstract] = runners

    def get(self):
        for index, arg in enumerate(sys.argv):
            for name in self.commands:
                if name == arg:
                    return self.commands[name]

runner = Runner()
