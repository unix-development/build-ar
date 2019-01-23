#!/usr/bin/env python

import os
import json

# Base directory
base_dir = os.path.realpath(__file__).replace('/src/globals.py', '')

# Mirror directory
mirror_dir = base_dir + '/mirror'

# Html directory
www_dir = base_dir + '/www'

# Packages directory
pkg_dir = base_dir + '/pkg'

# Packages list
packages = [ f for f in os.scandir(pkg_dir) if f.is_dir() ]

# Config list
with open(base_dir + '/repository.json') as file:
   config = json.load(file)
