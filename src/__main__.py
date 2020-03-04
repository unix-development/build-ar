#!/usr/bin/env python

"""
Copyright (c) Build Your Own Arch Linux Repository developers
See the file 'LICENSE' for copying permission
"""

from core.app import app
from core.runner import runner
from environment import environment
from validator import validator
from synchronizer import synchronizer

def main():
    runner.set("validation", validator.execute)

    runner.set("run", [
        #validator.execute,
        #environment.prepare_git,
        #environment.prepare_mirror,
        #environment.prepare_pacman,
        synchronizer.scan,
    ])

    runner.execute()


if __name__ == "__main__":
    main()
