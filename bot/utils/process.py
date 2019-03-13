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
