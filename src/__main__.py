#!/usr/bin/env python

"""
Copyright (c) Build Your Own Arch Linux Repository developers
See the file 'LICENSE' for copying permission
"""

from core.app import app
from core.runner import runner
from environment import environment
from repository import repository
from synchronizer import synchronizer
from validator import validator


def main():
    runner.set("validation", validator.execute)

    runner.set("run", [
        validator.execute,
        environment.prepare_git,
        environment.prepare_mirror,
        environment.syncronize_database,
        synchronizer.scan,
        repository.make
    ])

    runner.execute()


if __name__ == "__main__":
   try:
      main()
   except KeyboardInterrupt:
      sys.exit(0)
