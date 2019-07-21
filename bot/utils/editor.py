#!/usr/bin/env python

"""
Copyright (c) Build Your Own Arch Linux Repository developers
See the file 'LICENSE' for copying permission
"""

import os
import sys
import fileinput

from shutil import copy2


def replace_ending(find, replace, string):
    split = string.split(find, 1)
    return split[0] + replace

def edit_file(filename):
    with fileinput.input(filename, inplace=1) as f:
        for line in f:
            yield line.rstrip('\n')

def copy_file(src, dest=""):
    src = src.strip("/")
    dest = dest.strip("/")

    src = os.path.join(sys.path[1], "../files", src)
    dest = os.path.join(sys.path[0], dest)

    copy2(src, dest)
