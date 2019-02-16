#!/usr/bin/env python

import json
from utils.constructor import constructor

class new(constructor):
   def construct(self):
      with open(self.path_base + '/repository.json') as file:
         self.config = json.load(file)

   def get(self, name):
      value = self.config
      for key in name.split('.'):
         value = value[key]

      return value
