#!/usr/bin/env python

import os
import re
import sys
import json
import base64
import subprocess
import fileinput

def is_travis():
   return "TRAVIS" in os.environ

def output(command):
   return subprocess.check_output(command, shell=True).decode(sys.stdout.encoding).strip()

class validate():
   def __init__(self, **parameters):
      target = parameters["target"]
      feedback = "  [ %s ] %s"

      if not parameters["valid"]:
         print(feedback % ("X", parameters["target"]))
         sys.exit("\nError: " + parameters["error"])

      print(feedback % ("✓", parameters["target"]))
