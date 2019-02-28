#!/usr/bin/env python

import sys

class validate():
    def __init__(self, **parameters):
        target = parameters["target"]
        feedback = "  [ %s ] %s"

        if not parameters["valid"]:
            print(feedback % ("X", parameters["target"]))
            sys.exit("\nError: " + parameters["error"])

        print(feedback % ("✓", parameters["target"]))
