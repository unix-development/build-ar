#!/usr/bin/env python

import os
import sys
import subprocess

def main():
   if is_travis():
      set_git_config()

   for module in os.listdir('.'):
      if os.path.isdir(module) and os.path.isfile(module + '/package.py'):
         commit_change(module)

   if is_travis():
      git_push()


def set_git_config():
   if 'NAME' in os.environ and 'EMAIL' in os.environ:
      os.system(
         'git config user.email ' + os.environ['EMAIL'] + ' && ' \
         'git config user.name ' + os.environ['NAME'])

def is_travis():
   return "TRAVIS" in os.environ

def git_push():
   repository = output('git remote get-url origin') \
      .replace('https://', '') \
      .replace('http://', '') \
      .replace('git://', '') \
      .rstrip("\n\r")

   os.system('git push https://${GITHUB_TOKEN}@%s HEAD:master' % repository)

def commit_change(module):
   if output('git status %s --porcelain | sed s/^...//' % module):
      version = get_package_version(module)
      os.system(
         'git add ./' + module + ' && ' + \
         'git commit -m "Travis: Add ' + module + ' last update on ' + version + ' version"')

def output(command):
   return subprocess.check_output(command, shell=True).decode(sys.stdout.encoding)

def get_package_version(module):
   with open(module + '/PKGBUILD') as f:
      for line in f.readlines():
         if line.startswith('pkgver='):
            return line.split('=', 1)[1].rstrip("\n\r")

if __name__ == '__main__':
   main()
