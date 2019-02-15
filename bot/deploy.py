#!/usr/bin/env python

import os
from utils.git import git_remote_path
from utils.constructor import constructor

class new(constructor):
   def construct(self):
      self.port = self.config("ssh.port")
      self.user = self.config("ssh.user")
      self.host = self.config("ssh.host")
      self.path = self.config("ssh.path")

   def push(self):
      ssh = "ssh -p %i" % self.port
      location = self.user + "@" + self.host + ":" + self.path

      os.system(
         "rsync -avz --update --copy-links --progress -e '%s' %s %s"
         % (ssh, self.path_mirror, location)
      )

      if self.is_travis():
         os.system('git push https://${GITHUB_TOKEN}@%s HEAD:master' % git_remote_path())
