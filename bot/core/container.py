#!/usr/bin/env python

"""
Copyright (c) Build Your Own Arch Linux Repository developers
See the file 'LICENSE' for copying permission
"""

import sys
import functools


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
            # module.app = self.instances
            # module.config = self.instances.config
            # module.text = self._text
            # module.container = self
            module.register()

    def _text(self, abstract):
        keys = abstract.split(".", 1)
        return self.instances.text[keys[0]][keys[1]]


def return_self(method):
    @functools.wraps(method)
    def enforced_method(*args, **kwargs):
        self = args[0]
        method(*args, **kwargs)
        return self

    return enforced_method


container = Container()
