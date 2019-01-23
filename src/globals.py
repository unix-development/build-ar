#!/usr/bin/env python

import os
import json

# Base directory
path_base = os.path.realpath(__file__).replace('/src/globals.py', '')

# Mirror directory
path_mirror = path_base + '/mirror'

# Html directory
path_www = path_base + '/www'

# Packages directory
path_pkg = path_base + '/pkg'

# Packages list
packages = [ f for f in os.scandir(path_pkg) if f.is_dir() ]

# Config list
with open(path_base + '/repository.json') as file:
   config = json.load(file)
