#!/usr/bin/env python

import os
import sys

from utils.terminal import output
from utils.validator import validate
from utils.constructor import constructor

class new(constructor):
   def uid(self):
      print("Validating environment:")

      validate(
         error = "This file needs to be not execute as root.",
         target = "user",
         valid = os.getuid() != 0
      )

   def files(self):
      print("Validating files:")

      validate(
         error = "deploy_key could not been found.",
         target = "deploy_key",
         valid = os.path.isfile(self.path_base + "/deploy_key")
      )

   def ssh(self):
      print("Validating ssh connection:")

      script = "ssh -i ./deploy_key -p %i -q %s@%s [[ -d %s ]] && echo 1 || echo 0" % (
         self.config("ssh.port"),
         self.config("ssh.user"),
         self.config("ssh.host"),
         self.config("ssh.path")
      )

      validate(
         error = "ssh connection could not be established.",
         target = "ssh connection",
         valid = output(script) is "1"
      )

   def pkg(self):
      print("Validating packages:")

      #requirements = {
      #   "name": [ "is_exists" ],
      #   "source": [ "is_exists" ]
      #}

      #errors = {
      #   "is_exists" : "No %s was found in %s package.py",
      #   "is_git_repository" : "%s source in package.py does not appear to be a git repository",
      #}

      #sys.path.append(self.path_pkg)

      #for module in self.packages:
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
      #               target = module,
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
