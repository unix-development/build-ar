#!/usr/bin/env python

import os
import sys
import shutil

from utils.editor import edit_file, replace_ending
from utils.terminal import output

class new():
   def __init__(self, **parameters):
      self.packages = parameters["packages"]
      self.path_pkg = parameters["path_pkg"]
      self.path_mirror = parameters["path_mirror"]

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


class package():
   def __init__(self, **parameters):
      name = parameters["name"]
      path_pkg = parameters["path_pkg"]

      __import__(name + ".package")
      os.chdir(path_pkg + "/" + name)

      self.name = name
      self.path = path_pkg + "/" + name
      self.mirror = parameters["path_mirror"]
      self.package = sys.modules[name + ".package"]

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
         "mv *.pkg.tar.xz " + self.mirror);

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
