#!/usr/bin/env python

import os
import sys
import shutil
import fileinput
import subprocess

def main():
   cwd = os.getcwd()
   travis = is_travis()

   if not os.path.exists('build-repository'):
      os.makedirs('build-repository')

   for module in os.listdir('.'):
      if os.path.isdir(module) and os.path.isfile(module + '/package.py'):
         os.chdir(cwd + '/' + module)
         builder = Builder(module, travis)
         os.chdir(cwd)

class Builder():
   def __init__(self, module, travis):
      __import__(module + '.package')
      self.package = sys.modules['%s.package' % module]
      self.module = module

      if self.validate():
         self.set_helper()
         self.clean_directory()
         self.git_clone()
         if 'pre_build' in dir(self.package):
            self.package.pre_build()
            self.set_package_validity()

   def set_package_validity(self):
      os.system('makepkg -g >> PKGBUILD')

   def set_helper(self):
      self.package.edit_file = edit_file
      self.package.replace_ending = replace_ending

   def commit_change(self):
      if output('cd .. && git diff --name-only %s' % self.module) != '':
         version = self.get_package_version()
         print(
            'cd .. && ' + \
            'git add ./' + self.module + ' && ' + \
            'git commit -m "Travis build: Add ' + self.module + ' last update on ' + version + ' version"')

   def clean_directory(self):
      files = os.listdir('.')
      for f in files:
         if os.path.isdir(f):
            shutil.rmtree(f)
         if os.path.isfile(f) and f != 'package.py':
            os.remove(f)

   def get_package_version(self):
      with open('PKGBUILD') as f:
         for line in f.readlines():
            if line.startswith('pkgver='):
               return line.split('=', 1)[1].rstrip("\n\r")

   def git_clone(self):
      os.system(
         'git init && ' \
         'git remote add origin ' + self.package.source + ' && ' \
         'git pull origin master')

      if os.path.isfile('.SRCINFO'):
         os.remove('.SRCINFO')

   def validate(self):
      try:
          self.package.name
          self.package.source
          return True
      except AttributeError:
         return False

def output(command):
   return subprocess.check_output(command, shell=True).decode(sys.stdout.encoding)

def replace_ending(find, replace, string):
   split = string.split(find, 1)
   return split[0] + replace

def edit_file(filename):
   with fileinput.input(filename, inplace=1) as f:
       for line in f:
          yield line.rstrip('\n')

def is_travis():
   if "IS_TRAVIS_BUILD" in os.environ:
      return True
   else:
      return False

if __name__ == '__main__':
   if os.getuid() == 0:
      print('This file needs to be not execute as root.')
   else:
      main()
