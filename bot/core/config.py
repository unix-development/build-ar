#!/usr/bin/env python

import json

class init():
   def __init__(self, **parameters):
      with open(parameters['path_base'] + '/repository.json') as file:
         self.config = json.load(file)

   def get(self, name):
      value = self.config
      for key in name.split('.'):
         value = value[key]

      return value
