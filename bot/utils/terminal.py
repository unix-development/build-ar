#!/usr/bin/env python

import sys
import subprocess

def output(command):
    return subprocess.check_output(command, shell=True).decode(sys.stdout.encoding).strip()
