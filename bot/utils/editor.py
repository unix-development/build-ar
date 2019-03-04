#!/usr/bin/env python

import re
import fileinput

def replace_ending(find, replace, string):
    split = string.split(find, 1)
    return split[0] + replace


def edit_file(filename):
    with fileinput.input(filename, inplace=1) as f:
        for line in f:
            yield line.rstrip('\n')

def extract(module, name):
    with open(module + '/PKGBUILD') as f:
        for line in f.readlines():
            line = line.strip()

            if line.startswith(name + '='):
                string = line.split('=', 1)[1].strip('\n\r\"\' ')
                pattern = re.compile('\${\w+}')

                for var in re.findall(pattern, string):
                    name = var.replace('${', '').replace('}', '')
                    string = string.replace(var, extract(module, name))

                return string

    return ""
