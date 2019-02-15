#!/usr/bin/env python

import os

class new():
   def __init__(self, **parameters):
      self.config = parameters["config"]
      self.path_base = parameters["path_base"]

   def is_travis(self):
      return "TRAVIS" in os.environ

   def prepare_git(self):
      if self.is_travis():
         email = self.config("git.email")
         name = self.config("git.name")
         scripts = [
            "git config user.email '" + email + "'",
            "git config user.name '" + name + "'"
         ]

         for script in scripts:
            os.system(script)

   def prepare_ssh(self):
      if self.is_travis():
         host = self.config("ssh.host")
         scripts = [
            "chmod 600 " + self.path_base + "/deploy_key",
            "ssh-add " + self.path_base + "/deploy_key",
            "ssh-keyscan -t rsa -H " + host + " >> ~/.ssh/known_hosts"
         ]

         for script in scripts:
            os.system(script)
