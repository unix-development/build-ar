#!/usr/bin/env python

"""
Copyright (c) Build Your Own Arch Linux Repository developers
See the file 'LICENSE' for copying permission
"""

from utils.process import output


def title(text):
    column = int(output("tput cols")) - 4
    line = "── %s " % text.capitalize()
    line += "─" * (column - len(text))

    return bold(line)

def bold(text):
    return "\n\033[1m" + text + "\033[0m"
