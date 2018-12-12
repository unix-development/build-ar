#!/usr/bin/env python

import os
import re
import sys
import subprocess
import fileinput

# Base directory
base_path = os.path.realpath(__file__).replace('/build/helper.py', '')

# Repository directory
repository_path = base_path + '/repository'

# Packages directory
packages_path = base_path + '/packages'

def git_repository():
   repository = output('git remote get-url origin') \
      .replace('https://', '') \
      .replace('http://', '') \
      .replace('git://', '') \
      .rstrip("\n\r")

def is_travis():
   return "TRAVIS" in os.environ

def output(command):
   return subprocess.check_output(command, shell=True).decode(sys.stdout.encoding)

def replace_ending(find, replace, string):
   split = string.split(find, 1)
   return split[0] + replace

def edit_file(filename):
   with fileinput.input(filename, inplace=1) as f:
       for line in f:
          yield line.rstrip('\n')

def version(module):
   with open(module + '/PKGBUILD') as f:
      for line in f.readlines():
         if line.startswith('pkgver='):
            return re.sub('[^0-9\.]', '', line.split('=', 1)[1].rstrip("\n\r"))

def get_packages():
   packages = []
   for module in os.listdir(packages_path):
      if os.path.isfile(packages_path + '/' + module + '/package.py'):
         packages.append(module)

   packages.sort()
   return packages
