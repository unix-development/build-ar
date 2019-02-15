#!/usr/bin/env python

class constructor():
   def __init__(self, **parameters):
      for name in parameters:
         setattr(self, name, parameters[name])

      if "construct" in dir(self):
         self.construct()
