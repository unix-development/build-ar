#!/usr/bin/env python
# -*- coding:utf-8 -*-

import re
import fileinput
import subprocess

def replace_ending(find, replace, string):
    split = string.split(find, 1)
    return split[0] + replace


def edit_file(filename):
    with fileinput.input(filename, inplace=1) as f:
        for line in f:
            yield line.rstrip('\n')

def extract(module, name):
    command = "echo $(source %s; echo ${%s[@]})" % (module + "/PKGBUILD", name)
    process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True, executable="/bin/bash")
    output, error = process.communicate()

    return output.strip().decode("UTF-8")
