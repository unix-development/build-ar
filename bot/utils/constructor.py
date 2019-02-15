#!/usr/bin/env python

class constructor():
   def __init__(self, **parameters):
      for name in parameters:
         setattr(self, name, parameters[name])

      self.construct()
