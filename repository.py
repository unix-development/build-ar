#!/usr/bin/env python

import os
import re
import sys
import shutil
import fileinput
import subprocess

def main():
   cwd = os.getcwd()
   if not os.path.exists('build-repository'):
      os.makedirs('build-repository')

   for package in get_packages():
      os.chdir(cwd + '/' + package)
      builder = Builder(package)
      os.chdir(cwd)

   build_database()

class Builder():
   def __init__(self, module):
      __import__(module + '.package')
      self.package = sys.modules['%s.package' % module]
      self.module = module

      if self.validate():
         self.set_helper()
         self.clean_directory()
         self.git_clone()

         if not in_repository(module):
            if 'pre_build' in dir(self.package):
               self.package.pre_build()
               self.set_package_validity()

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
         'sudo pacman -S $(source ./PKGBUILD && echo ${depends[@]} ${makedepends[@]}) --noconfirm && ' \
         'makepkg -Ad --skippgpcheck && ' \
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

def get_packages():
   packages = []
   for module in os.listdir('.'):
      if os.path.isdir(module) and os.path.isfile(module + '/package.py'):
         packages.append(module)

   return packages

def build_database():
   os.system('repo-add build-repository/lognoz.db.tar.gz build-repository/*.pkg.tar.xz');

def in_repository(package):
   for file in os.listdir('../build-repository'):
      if file.startswith(package + '-' + version(package) + '-'):
         return True

def version(module):
   with open('./PKGBUILD') as f:
      for line in f.readlines():
         if line.startswith('pkgver='):
            return re.sub('[^0-9\.]', '', line.split('=', 1)[1].rstrip("\n\r"))

if __name__ == '__main__':
   if os.getuid() == 0:
      print('This file needs to be not execute as root.')
   else:
      main()
