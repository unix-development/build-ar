#!/usr/bin/env python

"""
Copyright (c) Build Your Own Arch Linux Repository developers
See the file 'LICENSE' for copying permission
"""


class attr(dict):
    def __getattr__(self, item):
        value = self.get(item)

        if type(value) is dict:
            return attr(value)
        else:
            return value

    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__
