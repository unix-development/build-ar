#!/usr/bin/env python

import os
import sys
import shutil
import fileinput
import subprocess

def main():
   cwd = os.getcwd()
   if not os.path.exists('build-repository'):
      os.makedirs('build-repository')

   for module in os.listdir('.'):
      if os.path.isdir(module) and os.path.isfile(module + '/package.py'):
         os.chdir(cwd + '/' + module)
         builder = Builder(module)
         os.chdir(cwd)

   build_database()

def build_database():
   os.system('repo-add build-repository/lognoz.db.tar.gz build-repository/*.pkg.tar.xz');

class Builder():
   def __init__(self, module):
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
         if output('cd .. && git status %s' % module) != '':
            self.build_package()

   def set_package_validity(self):
      os.system('makepkg -g >> md5sums.txt')

      with open('md5sums.txt') as f:
         replace = False
         cpt = 0
         md5 = f.readlines()
         os.remove('md5sums.txt')

      for line in edit_file('PKGBUILD'):
         if line.startswith('md5sums=(') or replace:
            replace = True
            line = md5[cpt].rstrip('\n')
            cpt = cpt + 1

         if cpt > len(md5) - 1:
            replace = False

         print(line)

   def set_helper(self):
      self.package.edit_file = edit_file
      self.package.replace_ending = replace_ending

   def build_package(self):
      os.system(
         'makepkg -Acs && ' \
         'mv *.pkg.tar.xz ../build-repository/');

   def clean_directory(self):
      files = os.listdir('.')
      for f in files:
         if os.path.isdir(f):
            shutil.rmtree(f)
         if os.path.isfile(f) and f != 'package.py':
            os.remove(f)

   def git_clone(self):
      os.system(
         'git init && ' \
         'git remote add origin ' + self.package.source + ' && ' \
         'git pull origin master && ' \
         'rm -rf .git')

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

if __name__ == '__main__':
   if os.getuid() == 0:
      print('This file needs to be not execute as root.')
   else:
      main()
