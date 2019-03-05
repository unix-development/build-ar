#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import subprocess

def output(command):
    return subprocess.check_output(command, shell=True).decode(sys.stdout.encoding).strip()

def title(text):
    column = int(output("tput cols")) - 4
    line = "── %s " % text.capitalize()
    line += "─" * (column - len(text))

    return bold(line)

def bold(text):
    return "\n\033[1m" + text + "\033[0m"
