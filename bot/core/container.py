#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys

class Container():
    instances = dict()

    def register(self, abstract, instance):
        self.instances[abstract] = instance

    def run(self):
        functions = self.get("runner").get()
        for name in functions:
            self.get(name)()

    def get(self, abstract):
        return self.instances[abstract]

    def bootstrap(self, bootstrappers):
        for bootstrap in bootstrappers:
            __import__(bootstrap)

            module = sys.modules[bootstrap]
            module.app = app
            module.path = path
            module.repo = repo
            module._ = text

            module.register(self)

def text(abstract):
    keys = abstract.split(".", 1)
    texts = container.get("text")

    return texts[keys[0]][keys[1]]

def app(abstract):
    return container.get(abstract)

def path(abstract):
    return container.get("path." + abstract)

def repo(abstract):
    value = container.get("repository")
    for key in abstract.split('.'):
        value = value[key]

    return value

container = Container()
