#!/usr/bin/env python

import os
import sys
import json
import validator
import environment

from core import config
from core import contextual

contextual = contextual.init(
   pwd = __file__
)

config = config.init(
   path_base = contextual.path_base
)

validate = validator.init(
   config = config,
   contextual = contextual
)

environment = environment.init(
   config = config,
   contextual = contextual
)

if __name__ == "__main__":
   if os.getuid() == 0:
      sys.exit("This file needs to be not execute as root.")

   validate.files()
   validate.repository()
   environment.prepare_ssh()
   validate.ssh()
