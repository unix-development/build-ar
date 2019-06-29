#!/usr/bin/env python

"""
Copyright (c) Build Your Own Arch Linux Repository developers
See the file 'LICENSE' for copying permission
"""

import collections


class Attr(collections.defaultdict):
    """
    This class defines an object, inheriting from Python data
    type dictionary.

    >>> foo = Attr()
    >>> foo.bar = 1
    >>> foo.bar
    1
    """
    def __init__(self):
        super(Attr, self).__init__(Attr)

    def __getattr__(self, abstract):
        try:
            return self[abstract]
        except KeyError:
            raise AttributeError(abstract)

    def __setattr__(self, abstract, value):
        self[abstract] = value


class Dict(dict):
    def __init__(self, arg):
        super(Dict, self).__init__(arg)

        for key, value in arg.items():
            if type(value) is dict:
                self[key] = Dict(value)
            else:
                self[key] = value

    def __getattr__(self, attr):
        return self.get(attr)

    def __setattr__(self, key, value):
        self.__setitem__(key, value)


def get_attr_value(ref, name):
    for key in name.split(" "):
        try:
             ref = ref[key]
        except:
            return None

    return ref

