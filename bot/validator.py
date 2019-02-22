#!/usr/bin/env python

import os
import re
import sys
import socket
import secrets
import platform
import requests

from utils.terminal import output
from utils.validator import validate
from utils.constructor import constructor

class new(constructor):
   def requirements(self):
      print("Validating requirements:")

      validate(
         error = "This program needs to be not execute as root.",
         target = "user privileges",
         valid = os.getuid() != 0
      )

      validate(
         error = "This program needs to be executed in Arch Linux.",
         target = "arch linux",
         valid = platform.dist()[0] == "arch"
      )

      try:
         socket.create_connection(("www.github.com", 80))
         connected = True
      except OSError:
         connected = False

      validate(
         error = "This program needs to connect to internet.",
         target = "internet",
         valid = connected
      )

      validate(
         error = "This program needs to have ssh installed.",
         target = "ssh",
         valid = os.path.exists("/usr/bin/ssh")
      )

   def files(self):
      print("Validating files:")

      validate(
         error = "deploy_key could not been found.",
         target = "deploy_key",
         valid = os.path.isfile(self.path_base + "/deploy_key")
      )

   def ssh(self):
      print("Validating connection:")

      for name in [ "port", "user", "host", "path" ]:
         globals()[name] = self.config("ssh." + name)

      url = self.config("url")
      token = secrets.token_hex(15)
      source = self.path_mirror + "/validation_token"

      with open(source, "w") as f:
         f.write(token)
         f.close()

      os.system(
         "rsync -aqvz -e 'ssh -p %i' %s %s@%s:%s" %
         (port, source, user, host, path))

      try:
         response = requests.get(url + "/validation_token")
         valid = True if response.status_code == 200 else False
      except:
         valid = False

      validate(
         error = "This program can't connect to %s." % url,
         target = url,
         valid = valid
      )

      script = "ssh -i ./deploy_key -p %i -q %s@%s [[ -d %s ]] && echo 1 || echo 0" % (
         self.config("ssh.port"),
         self.config("ssh.user"),
         self.config("ssh.host"),
         self.config("ssh.path")
      )

      validate(
         error = "ssh connection could not be established.",
         target = "%s@%s" % (
            self.config("ssh.user"),
            self.config("ssh.host"),
         ),
         valid = output(script) is "1"
      )

   def container(self):
      print("Validating packages:")

      validate(
         error = "No package was found in pkg directory.",
         target = "directory",
         valid = len(self.packages) > 0
      )

      folders = [ f.name for f in os.scandir(self.path_pkg) if f.is_dir() ]
      diff = set(folders) - set(self.packages)

      validate(
         error = "No package.py was found in pkg subdirectories: " + ", ".join(diff),
         target = "package.py",
         valid = len(diff) == 0
      )

      #print("\n─────────────────────────────────────\n")

      #requirements = {
      #   "name": [ "is_exists" ],
      #   "source": [ "is_exists" ]
      #}

      #errors = {
      #   "is_exists" : "No %s variable was found in %s package.py",
      #   "is_git_repository" : "%s source in package.py does not appear to be a git repository",
      #}

      #sys.path.append(self.path_pkg)

      #for module in self.packages:
      #   print("Validating %s:" % module)
      #   __import__(module + ".package")

      #   os.chdir(self.path_pkg + "/" + module)
      #   package = sys.modules[module + ".package"]

      #   for name in requirements:
      #      for validation in requirements[name]:
      #         if validation == "is_exists":
      #            valid = True

      #            try:
      #               getattr(package, name)
      #            except AttributeError:
      #               valid = False

      #            validate(
      #               error = errors["is_exists"] % (name, module),
      #               target = name,
      #               valid = valid
      #            )

   def repository(self):
      print("Validating repository.json:")

      requirements = {
         "database"  : [ "not_blank" ],
         "git.email" : [ "not_blank" ],
         "git.name"  : [ "not_blank" ],
         "ssh.host"  : [ "not_blank" ],
         "ssh.path"  : [ "not_blank" ],
         "ssh.port"  : [ "not_blank", "is_integer" ],
         "ssh.user"  : [ "not_blank" ],
         "url"       : [ "not_blank" ]
      }

      errors = {
         "not_blank"  : "%s must be defined in repository.json",
         "is_integer" : "%s must be an integer in repository.json"
      }

      for name in requirements:
         value = self.config(name)
         target = name.replace(".", " ")

         for validation in requirements[name]:
            if validation == "not_blank":
               validate(
                  error = errors["not_blank"] % target,
                  target = target,
                  valid = value
               )

            elif validation == "is_integer":
               validate(
                  error = errors["is_integer"] % target,
                  target = target,
                  valid = type(value) is int
               )
