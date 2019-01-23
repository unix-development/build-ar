#!/usr/bin/env python

import os
import re
import sys
import json
import time
import base64

from globals import *
from helpers import *

class Repository():
   def build(self):
      if not os.path.exists(repository_dir):
         os.makedirs(repository_dir)

      feedback = "  [ %s ] %s"
      sys.path.append(pkg_dir)

      for package in packages:
         name = package.name
         path = package.path

         if not os.path.isfile(path + "/package.py"):
            print(feedback % ("X", name))
            exit("No package.py was found in %s directory." % name)
         else:
            print(feedback % ("✓", name))

         __import__(name + '.package')
         os.chdir(path)
         module = sys.modules[name + '.package']

   def parameter(self, name):
      value = repository
      for key in name.split('.'):
         value = value[key]

      return value

   def validate(self):
      self.validate_files()
      self.validate_config()
      self.validate_ssh()

   def prepare_git(self):
      if is_travis():
         email = self.parameter("git.email")
         name = self.parameter("git.name")
         scripts = [
            "git config user.email '" + email + "'",
            "git config user.name '" + name + "'"
         ]

         for script in scripts:
            os.system(script)

   def prepare_ssh(self):
      if is_travis():
         host = self.parameter("ssh.host")
         scripts = [
            "chmod 600 " + base_dir + "/deploy_key",
            "ssh-add " + base_dir + "/deploy_key",
            "ssh-keyscan -t rsa -H " + host + " >> ~/.ssh/known_hosts"
         ]

         for script in scripts:
            os.system(script)

   def validate_files(self):
      if is_travis():
         print("Validation files:")

         validate({
            "error"  : "deploy_key could not been found.",
            "target" : "deploy_key",
            "valid"  : os.path.isfile(base_dir + "/deploy_key")
         })

   def validate_ssh(self):
      print("Validating ssh connection:")

      self.prepare_ssh()
      ssh = repository["ssh"]

      validate({
         "error"  : "ssh connection could not be established.",
         "target" : "ssh connection",
         "valid"  : output( \
            "ssh -i ./deploy_key -p %i -q %s@%s [[ -d %s ]] && echo 1 || echo 0" % \
            (ssh["port"], ssh["user"], ssh["host"], ssh["path"])) is "1"
      })

   def validate_config(self):
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

      for name in requirements:
         value = self.parameter(name)
         target = name.replace(".", " ")

         for validation in requirements[name]:
            if validation == "not_blank":
               validate({
                  "valid"  : value,
                  "target" : target,
                  "error"  : "%s must be defined in repository.json" % target,
               })

            elif validation == "is_integer":
               validate({
                  "valid"  : type(value) is int,
                  "target" : target,
                  "error"  : "%s must be an integer in repository.json" % target
               })

def main(argv):
   repository = Repository()
   repository.validate()
   repository.build()

if __name__ == "__main__":
   if os.getuid() == 0:
      print("This file needs to be not execute as root.")
      sys.exit(2)

   main(sys.argv[1:])
