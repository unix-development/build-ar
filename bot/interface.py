#!/usr/bin/env python

from utils.constructor import constructor
from utils.pkgbuild import extract

class new(constructor):
   def build(self):
      for package in self.packages:
         module = self.path_pkg + '/' + package

         try:
            file = open(module + '/PKGBUILD')
         except FileNotFoundError:
            continue

      description = extract(module, 'pkgdesc')
      version = extract(module, 'pkgver')
      name = extract(module, 'pkgname')
