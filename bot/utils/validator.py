#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys

class validate():
    def __init__(self, **parameters):
        target = parameters["target"]
        feedback = "  [ %s ] %s"

        if not parameters["valid"]:
            print(feedback % ("x", parameters["target"]))
            sys.exit("\nError: " + parameters["error"])

        print(feedback % ("✓", parameters["target"]))
