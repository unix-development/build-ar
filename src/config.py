#!/usr/bin/env python

import os
from globals import ( config, path_base )
from helpers import ( output, is_travis, validate )

class Config():
   def get(self, name):
      value = config
      for key in name.split('.'):
         value = value[key]

      return value

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

      errors = {
         "not_blank"  : "%s must be defined in repository.json",
         "is_integer" : "%s must be an integer in repository.json"
      }

      for name in requirements:
         value = self.get(name)
         target = name.replace(".", " ")

         for validation in requirements[name]:
            if validation == "not_blank":
               validate({
                  "error"  : errors["not_blank"] % target,
                  "target" : target,
                  "valid"  : value
               })

            elif validation == "is_integer":
               validate({
                  "error"  : errors["is_integer"] % target,
                  "target" : target,
                  "valid"  : type(value) is int
               })

   def validate_files(self):
      if is_travis():
         print("Validation files:")

         validate({
            "error"  : "deploy_key could not been found.",
            "target" : "deploy_key",
            "valid"  : os.path.isfile(path_base + "/deploy_key")
         })

   def validate_ssh(self):
      print("Validating ssh connection:")

      script = "ssh -i ./deploy_key -p %i -q %s@%s [[ -d %s ]] && echo 1 || echo 0" % (
         config["ssh"]["port"],
         config["ssh"]["user"],
         config["ssh"]["host"],
         config["ssh"]["path"]
      )

      validate({
         "error"  : "ssh connection could not be established.",
         "target" : "ssh connection",
         "valid"  : output(script) is "1"
      })
