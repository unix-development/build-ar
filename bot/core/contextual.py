#!/usr/bin/env python

import os

# Base directory
path_base = os.path.realpath(__file__).replace('/bot/core/contextual.py', '')

# Mirror directory
path_mirror = path_base + '/mirror'

# Html directory
path_www = path_base + '/www'

# Packages directory
path_pkg = path_base + '/pkg'
