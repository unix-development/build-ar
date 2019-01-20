#!/usr/bin/env python

import os
import re
import sys
import json
import datetime
import subprocess
import fileinput

# Base directory
base_path = os.path.realpath(__file__).replace('/src/helper.py', '')

# Repository directory
repository_path = base_path + '/repository'

# Html directory
html_path = base_path + '/www'

# Packages directory
packages_path = base_path + '/pkg'

# Repository setting
with open(base_path + '/repository.json') as file:
   repository = json.load(file)


def git_repository():
   return output('git remote get-url origin') \
      .replace('https://', '') \
      .replace('http://', '') \
      .replace('git://', '')


def is_travis():
   return "TRAVIS" in os.environ


def output(command):
   return subprocess.check_output(command, shell=True).decode(sys.stdout.encoding).strip()


def replace_ending(find, replace, string):
   split = string.split(find, 1)
   return split[0] + replace


def edit_file(filename):
   with fileinput.input(filename, inplace=1) as f:
       for line in f:
          yield line.rstrip('\n')


def extract(module, name):
   with open(module + '/PKGBUILD') as f:
      for line in f.readlines():
         if line.startswith(name + '='):
            string = line.split('=', 1)[1].strip('\n\r\"\' ')
            pattern = re.compile('\${\w+}')

            for var in re.findall(pattern, string):
               name = var.replace('${', '').replace('}', '')
               string = string.replace(var, extract(module, name))

            return string


def get_packages():
   packages = []
   for module in os.listdir(packages_path):
      if os.path.isfile(packages_path + '/' + module + '/package.py'):
         packages.append(module)

   packages.sort()
   return packages
