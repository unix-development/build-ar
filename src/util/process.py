#!/usr/bin/env python

"""
Copyright (c) Build Your Own Arch Linux Repository developers
See the file 'LICENSE' for copying permission
"""


import sys
import subprocess


def execute(command, type_process=""):
    if type_process == "strict":
        try:
            return subprocess.call(command, shell=True)
        except subprocess.CalledProcessError as error:
            sys.exit(error)
        except OSError as error:
            sys.exit(error)
    else:
        subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True
        )

def output(command):
    output = subprocess.check_output(
        command,
        shell=True,
        stderr=subprocess.STDOUT
    )

    return output.decode(sys.stdout.encoding).strip()

def extract(module, name):
    command = "echo $(source %s; echo ${%s[@]})" % (module + "/PKGBUILD", name)
    process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True, executable="/bin/bash")
    output, error = process.communicate()

    return output.strip().decode("UTF-8")
