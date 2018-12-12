#!/usr/bin/env python

import os
import re
import sys
import shutil
import fileinput
import subprocess

def build(name):
   cwd = os.getcwd()
   if not os.path.exists('build-repository'):
      os.makedirs('build-repository')

   for package in get_packages():
      os.chdir(cwd + '/' + package)
      builder = Builder(package)
      os.chdir(cwd)

   build_database(name)

def commit():
   cwd = os.getcwd()
   for package in get_packages():
      os.chdir(cwd + '/' + package)
      commit_change(package)
      os.chdir(cwd)

   if is_travis():
      git_push()

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

         if not in_repository(module):
            self.build_package()

   def set_helper(self):
      self.package.edit_file = edit_file
      self.package.replace_ending = replace_ending

   def build_package(self):
      os.system(
         'sudo pacman -S $(source ./PKGBUILD && echo ${depends[@]} ${makedepends[@]}) --noconfirm && ' \
         'makepkg -Ad --skipinteg && ' \
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

   packages.sort()
   return packages

def build_database(name):
   os.system(
      'repo-add build-repository/' + name + '.db.tar.gz build-repository/*.pkg.tar.xz && ' \
      'rm -f ' + name + '.db.tar.gz.old && ' \
      'rm -f ' + name + '.files*');

def in_repository(package):
   for file in os.listdir('../build-repository'):
      if file.startswith(package + '-' + version(package) + '-'):
         return True

   for file in os.listdir('../build-repository'):
      if file.startswith(package + '-'):
         os.remove('../build-repository/' + file)

def version(module):
   with open('./PKGBUILD') as f:
      for line in f.readlines():
         if line.startswith('pkgver='):
            return re.sub('[^0-9\.]', '', line.split('=', 1)[1].rstrip("\n\r"))

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
      os.system(
         'git add ./' + module + ' && ' + \
         'git commit -m "Bot: Add ' + module + ' last update on ' + version(module) + ' version"')

def output(command):
   return subprocess.check_output(command, shell=True).decode(sys.stdout.encoding)

if __name__ == '__main__':
   if os.getuid() == 0:
      print('This file needs to be not execute as root.')

   if len(sys.argv) == 3 and sys.argv[1] == 'build':
      build(sys.argv[2])
   elif len(sys.argv) == 2 and sys.argv[1] == 'commit':
      commit()
