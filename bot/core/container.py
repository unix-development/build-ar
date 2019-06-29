#!/usr/bin/env python

"""
Copyright (c) Build Your Own Arch Linux Repository developers
See the file 'LICENSE' for copying permission
"""

import sys


class Container(object):
    def __init__(self):
        self.bindings = dict()

    def run(self):
        functions = self.bindings["runner"].get()
        for name in functions:
            self.bindings[name]()

    def register(self, abstract, value):
        self.bindings[abstract] = value

    def bootstrap(self, bootstrappers):
        for bootstrap in bootstrappers:
            __import__(bootstrap)
            module = sys.modules[bootstrap]
            parameters = module.register()

            if parameters is None:
                continue

            for key in parameters:
                self.register(key, parameters[key])


container = Container()
