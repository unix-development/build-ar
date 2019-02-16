#!/usr/bin/env python

import os
from utils.git import git_remote_path
from utils.constructor import constructor

class new(constructor):
   def construct(self):
      self.database = self.config("database")

      for name in [ "port", "user", "host", "path" ]:
         setattr(self, name, self.config("ssh." + name))

   def build(self):
      os.chdir(self.path_mirror)

      self.create_database()
      self.clean_directory()

   def clean_directory(self):
      scripts = [
         "rm -f ./%s.old" % self.database,
         "rm -f ./%s.files" % self.database,
         "rm -f ./%s.files.tar.gz" % self.database,
         "rm -f ./%s.files.tar.gz.old" % self.database
      ]

      for script in scripts:
         os.system(script)

   def create_database(self):
      scripts = [
         "rm -f ./%s.db" % self.database,
         "rm -f ./%s.db.tar.gz" % self.database,
         "repo-add ./%s.db.tar.gz ./*.pkg.tar.xz" % self.database
      ]

      for script in scripts:
         os.system(script)

   def deploy(self):
      ssh = "ssh -p " + self.port
      location = self.user + "@" + self.host + ":" + self.path

      os.system(
         "rsync -avz --update --copy-links --progress -e '%s' %s/ %s"
         % (ssh, self.path_mirror, location)
      )

      if self.is_travis():
         os.system('git push https://${GITHUB_TOKEN}@%s HEAD:master' % git_remote_path())
