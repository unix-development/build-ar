#!/usr/bin/env python

"""
Copyright (c) Build Your Own Arch Linux Repository developers
See the file 'LICENSE' for copying permission
"""

from core.app import app
from core.runner import runner
from environment import environment
from validator import validator

def main():
    runner.set("validation", [
        validator.execute
    ])

    for execute in runner.get():
        execute()


if __name__ == "__main__":
    main()
