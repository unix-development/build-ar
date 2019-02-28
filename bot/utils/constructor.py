#!/usr/bin/env python

import functools

class constructor():
    def __init__(self, **parameters):
        for name in parameters:
            setattr(self, name, parameters[name])

        if "construct" in dir(self):
            self.construct()

def fluent(func):
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        self = args[0]
        func(*args, **kwargs)
        return self

    return wrapped
