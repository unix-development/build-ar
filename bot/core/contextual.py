#!/usr/bin/env python

import os

class init():
   def __init__(self, **parameters):
      # Base directory
      self.path_base = os.path.realpath(parameters['pwd']).replace('bot/__main__.py', '')

      # Mirror directory
      self.path_mirror = self.path_base + '/mirror/'

      # Html directory
      self.path_www = self.path_base + '/www/'

      # Packages directory
      self.path_pkg = self.path_base + '/pkg/'
