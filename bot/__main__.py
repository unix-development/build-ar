#!/usr/bin/env python

import os
import sys
import json
import packages
import interface
import validator
import environment

from core import runner
from core import config
from core import contextual

contextual = contextual.new(
   pwd = __file__
)

config = config.new(
   path_base = contextual.path_base
)

validate = validator.new(
   config = config.get,
   path_base = contextual.path_base
)

environment = environment.new(
   config = config.get,
   path_base = contextual.path_base
)

interface = interface.new(
   config = config.get,
   packages = contextual.packages,
   path_pkg = contextual.path_pkg,
   path_www = contextual.path_www,
   path_mirror = contextual.path_mirror
)

packages = packages.new(
   packages = contextual.packages,
   path_pkg = contextual.path_pkg,
   path_mirror = contextual.path_mirror
)

runner.new(
   validate = [
      validate.files,
      validate.repository,
      environment.prepare_ssh,
      validate.ssh
   ],
   build = [
      validate.files,
      validate.repository,
      environment.prepare_ssh,
      validate.ssh,
      packages.build,
      interface.build
   ]
)
