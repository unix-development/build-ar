#!/usr/bin/env python

"""
Copyright (c) Build Your Own Arch Linux Repository developers
See the file 'LICENSE' for copying permission
"""

import sys


class validate():
    def __init__(self, **parameters):
        target = parameters["target"]
        feedback = "  [ %s ] %s"

        if not parameters["valid"]:
            print(feedback % ("x", parameters["target"]))
            sys.exit("\nError: " + parameters["error"])

        print(feedback % ("✓", parameters["target"]))
