#!/usr/bin/env python

import os
from utils.constructor import constructor

class new(constructor):
   def execute(self, scripts):
      os.system("(" + scripts + ") &>/dev/null")

   def is_travis(self):
      return "TRAVIS" in os.environ

   def prepare_git(self):
      email = self.config("git.email")
      name = self.config("git.name")

      self.execute(
         "git config user.email '%s'; " % email +
         "git config user.name '%s';" % name
      )

   def prepare_ssh(self):
      host = self.config("ssh.host")

      self.execute(
         "eval $(ssh-agent); " +
         "chmod 600 %s/deploy_key; " % self.path_base +
         "ssh-add -lf %s/deploy_key; " % self.path_base +
         "ssh-keyscan -t rsa -H %s >> ~/.ssh/known_hosts; " % host
      )
