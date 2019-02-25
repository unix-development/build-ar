#!/usr/bin/env python

import os
from utils.constructor import constructor

class new(constructor):
   def is_travis(self):
      return "TRAVIS" in os.environ

   def prepare_git(self):
      email = self.config("git.email")
      name = self.config("git.name")
      scripts = [
         "git config user.email '" + email + "'",
         "git config user.name '" + name + "'"
      ]

      for script in scripts:
         os.system(script)

   def prepare_ssh(self):
      host = self.config("ssh.host")
      script = (
         "eval $(ssh-agent); "
         "chmod 600 " + self.path_base + "/deploy_key; "
         "ssh-add -lf " + self.path_base + "/deploy_key; "
         "ssh-keyscan -t rsa -H " + host + " >> ~/.ssh/known_hosts; "
      )

      os.system("(" + script + ") &>/dev/null")
