#!/usr/bin/env python

"""
Copyright (c) Build Your Own Arch Linux Repository developers
See the file 'LICENSE' for copying permission
"""

import sys
import subprocess


def output(command):
    return subprocess.check_output(command, shell=True).decode(sys.stdout.encoding).strip()

def strict_execute(command):
    try:
        subprocess.check_call(command, shell=True)
    except subprocess.CalledProcessError as error:
        sys.exit(error)
    except OSError as error:
        sys.exit(error)

def git_remote_path():
    return output('git remote get-url origin') \
        .replace('https://', '') \
        .replace('http://', '') \
        .replace('git://', '')

def extract(module, name):
    command = "echo $(source %s; echo ${%s[@]})" % (module + "/PKGBUILD", name)
    process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True, executable="/bin/bash")
    output, error = process.communicate()

    return output.strip().decode("UTF-8")

def is_travis(self):
    return ("TRAVIS" in os.environ and os.environ["TRAVIS"] != "")
