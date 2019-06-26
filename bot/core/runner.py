#!/usr/bin/env python
# -*- coding:utf-8 -*-

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
