#!/usr/bin/env python

import os
import sys
import shutil

from utils.editor import edit_file, replace_ending
from utils.terminal import output
from utils.constructor import constructor

class new(constructor):
   def build(self):
      sys.path.append(self.path_pkg)

      for name in self.packages:
         module = package(
            name = name,
            path_pkg = self.path_pkg,
            path_mirror = self.path_mirror
         )

         module.prepare()
         module.pull()
         module.make()

      repository(
         config = self.config,
         database = self.config("database"),
         path_mirror = self.path_mirror
      )

class repository(constructor):
   def construct(self):
      os.chdir(self.path_mirror)

      self.add_packages()
      self.clean_directory()

   def clean_directory(self):
      scripts = [
         "rm -f ./%s.old" % self.database,
         "rm -f ./%s.files" % self.database,
         "rm -f ./%s.files.tar.gz" % self.database,
         "rm -f ./%s.files.tar.gz.old" % self.database
      ]

      for script in scripts:
         os.system(script)

   def add_packages(self):
      scripts = [
         "rm -f ./%s.db" % self.database,
         "rm -f ./%s.db.tar.gz" % self.database,
         "repo-add ./%s.db.tar.gz ./*.pkg.tar.xz" % self.database
      ]

      for script in scripts:
         os.system(script)

class package(constructor):
   def construct(self):
      __import__(self.name + ".package")
      os.chdir(self.path_pkg + "/" + self.name)

      self.path = self.path_pkg + "/" + self.name
      self.package = sys.modules[self.name + ".package"]

   def prepare(self):
      self.set_utils()
      self.clean_directory()

   def make(self):
      if "pre_build" in dir(self.package):
         self.package.pre_build()

      self.install_dependencies()
      self.build()

   def install_dependencies(self):
      packages = output("source ./PKGBUILD && echo ${makedepends[@]}")

      if packages.strip() != "":
         os.system("sudo pacman -S %s --noconfirm" % packages)

   def build(self):
      os.system(
         "makepkg -Asc && " \
         "mv *.pkg.tar.xz " + self.path_mirror);

   def pull(self):
      os.system(
         "git init --quiet && " \
         "git remote add origin " + self.package.source + " && " \
         "git pull origin master --quiet && " \
         "rm -rf .git")

      if os.path.isfile(".SRCINFO"):
         os.remove(".SRCINFO")

   def clean_directory(self):
      files = os.listdir(".")
      for f in files:
         if os.path.isdir(f):
            shutil.rmtree(f)
         elif os.path.isfile(f) and f != "package.py":
            os.remove(f)

   def set_utils(self):
      self.package.edit_file = edit_file
      self.package.replace_ending = replace_ending
