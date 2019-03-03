#!/usr/bin/env python

import sys

class validate():
    def __init__(self, **parameters):
        target = parameters["target"]
        feedback = "  [ %s ] %s"

        if not parameters["valid"]:
            print(feedback % ("x", parameters["target"]))
            print("\nError: " + parameters["error"])
            sys.exit(-1)

        print(feedback % ("✓", parameters["target"]))
