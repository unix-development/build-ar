#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import subprocess

def output(command):
    return subprocess.check_output(command, shell=True).decode(sys.stdout.encoding).strip()

def execute(commands):
    for command in commands:
        try:
            process = subprocess.check_call(command, shell=True)
        except subprocess.CalledProcessError as error:
            sys.exit(error)
        except OSError as error:
            sys.exit(error)

def git_remote_path():
    return output('git remote get-url origin') \
        .replace('https://', '') \
        .replace('http://', '') \
        .replace('git://', '')

def title(text):
    column = int(output("tput cols")) - 4
    line = "── %s " % text.capitalize()
    line += "─" * (column - len(text))

    return bold(line)

def bold(text):
    return "\n\033[1m" + text + "\033[0m"
