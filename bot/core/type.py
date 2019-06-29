#!/usr/bin/env python

"""
Copyright (c) Build Your Own Arch Linux Repository developers
See the file 'LICENSE' for copying permission
"""


class Attr(dict):
    """
    This class defines an object, inheriting from Python data
    type dictionary.

    >>> foo = Attr()
    >>> foo.bar = 1
    >>> foo.bar
    1
    """

    def __init__(self, initial=None):
        if initial is None:
            initial = {}

        dict.__init__(self, initial)

    def __getattr__(self, item):
        """
        Maps values to attributes
        Only called if there *is NOT* an attribute with this name
        """

        try:
            return self.__getitem__(item)
        except KeyError:
            raise AttributeError("unable to access item '%s'" % item)

    def __setattr__(self, item, value):
        """
        Maps attributes to values
        Only if we are initialised
        """

        # This test allows attributes to be set in the __init__ method
        if "_AttribDict__initialised" not in self.__dict__:
            return dict.__setattr__(self, item, value)

        # Any normal attributes are handled normally
        elif item in self.__dict__:
            dict.__setattr__(self, item, value)
        else:
            self.__setitem__(item, value)

    def __getstate__(self):
        return self.__dict__

    def __setstate__(self, dict):
        self.__dict__ = dict


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

