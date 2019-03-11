#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import functools


def return_self(name):
    @functools.wraps(name)
    def wrapper(*args, **kwargs):
        self = args[0]
        name(*args, **kwargs)
        return self

    return wrapper

def app(abstract):
    return container.get(abstract)

def config(abstract):
    value = container.get("repository")
    for key in abstract.split('.'):
        value = value[key]

    return value

def repo(abstract):
    value = container.get("repository")
    for key in abstract.split('.'):
        value = value[key]

    return value

def text(abstract):
    keys = abstract.split(".", 1)
    texts = container.get("text")

    return texts[keys[0]][keys[1]]


class Container():
    instances = dict()

    @return_self
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
            bootstrap()


container = Container()
