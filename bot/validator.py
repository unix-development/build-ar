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
from utils.constructor import constructor, fluent

class validator(constructor):
   @fluent
   def user_privileges(self):
      validate(
         error = "This program needs to be not execute as root.",
         target = "user privileges",
         valid = os.getuid() != 0
      )

   @fluent
   def operating_system(self):
      validate(
         error = "This program needs to be executed in Arch Linux.",
         target = "operating system",
         valid = platform.dist()[0] == "arch"
      )

   @fluent
   def openssh_installed(self):
      validate(
         error = "This program needs to have ssh installed.",
         target = "openssh",
         valid = os.path.exists("/usr/bin/ssh")
      )

   @fluent
   def internet_up(self):
      try:
         socket.create_connection(("www.github.com", 80))
         connected = True
      except OSError:
         connected = False

      validate(
         error = "This program needs to be connected to internet.",
         target = "internet",
         valid = connected
      )

   @fluent
   def deploy_key(self):
      validate(
         error = "deploy_key could not been found.",
         target = "deploy_key",
         valid = os.path.isfile(self.path_base + "/deploy_key")
      )

   @fluent
   def ssh_connection(self):
      script = "ssh -i ./deploy_key -p %i -q %s@%s [[ -d %s ]] && echo 1 || echo 0" % (
         self.config("ssh.port"),
         self.config("ssh.user"),
         self.config("ssh.host"),
         self.config("ssh.path")
      )

      validate(
         error = "ssh connection could not be established.",
         target = "ssh address",
         valid = output(script) is "1"
      )

   @fluent
   def mirror_connection(self):
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
         target = "mirror host",
         valid = valid
      )

   @fluent
   def repository(self):
      valid = True

      for name in [ "database", "git.email", "git.name", "ssh.host", "ssh.path", "ssh.port", "url" ]:
         if not self.config(name):
            valid = False
            break

      name = name.replace(".", " ")

      validate(
         error = "%s must be defined in repository.json" % name,
         target = "is defined",
         valid = valid
      )

   @fluent
   def port(self):
      validate(
         error = "port must be an interger in repository.json",
         target = "port",
         valid = type(self.config("ssh.port")) == int
      )

   @fluent
   def pkg_directory(self):
      validate(
         error = "No package was found in pkg directory.",
         target = "directory",
         valid = len(self.packages) > 0
      )

   @fluent
   def pkg_content(self):
      folders = [ f.name for f in os.scandir(self.path_pkg) if f.is_dir() ]
      diff = set(folders) - set(self.packages)

      validate(
         error = "No package.py was found in pkg subdirectories: " + ", ".join(diff),
         target = "content",
         valid = len(diff) == 0
      )

class new(constructor):
   def construct(self):
      self.validator = validator(
         config = self.config,
         packages = self.packages,
         path_pkg = self.path_pkg,
         path_base = self.path_base,
         path_mirror = self.path_mirror
      )

   def requirements(self):
      print("Validating requirements:")

      (self.validator
         .user_privileges()
         .operating_system()
         .openssh_installed()
         .internet_up())

   def files(self):
      print("Validating files:")

      (self.validator
         .deploy_key())

   def repository(self):
      print("Validating repository.json:")

      (self.validator
         .repository()
         .port())

   def ssh(self):
      print("Validating connection:")

      (self.validator
         .mirror_connection()
         .ssh_connection())

   def container(self):
      print("Validating packages:")

      (self.validator
         .pkg_directory()
         .pkg_content())
