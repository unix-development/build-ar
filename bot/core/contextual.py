#!/usr/bin/env python

import os

class new():
   def __init__(self, **parameters):
      self.parameters = parameters

      self.setPathsLocation()
      self.setPackages()

   def setPackages(self):
      packages = []
      for name in os.listdir(self.path_pkg):
         if os.path.isfile(self.path_pkg + '/' + name + '/package.py'):
            packages.append(name)

      packages.sort()
      self.packages = packages

   def setPathsLocation(self):
      # Base directory
      self.path_base = os.path.realpath(self.parameters["pwd"]).replace("/bot/__main__.py", "")

      # Mirror directory
      self.path_mirror = self.path_base + "/mirror"

      # Html directory
      self.path_www = self.path_base + "/www"

      # Packages directory
      self.path_pkg = self.path_base + "/pkg"
