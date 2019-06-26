#!/usr/bin/env python
# -*- coding:utf-8 -*-

import fileinput


def replace_ending(find, replace, string):
    split = string.split(find, 1)
    return split[0] + replace


def edit_file(filename):
    with fileinput.input(filename, inplace=1) as f:
        for line in f:
            yield line.rstrip('\n')
