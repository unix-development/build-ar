#!/usr/bin/env python

import sys

class new():
    def __init__(self, **commands):
        self.commands = commands

        for index, arg in enumerate(sys.argv):
            for name in commands:
                if name == arg:
                    self.execute(name)
                    break;

    def execute(self, name):
        for function in self.commands[name]:
            function()
