#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import subprocess

def output(command):
    return subprocess.check_output(command, shell=True).decode(sys.stdout.encoding).strip()

def column():
    return int(output("tput cols")) - 4
