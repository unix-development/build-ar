#!/usr/bin/env python

import os
from utils.constructor import constructor

class new(constructor):
    def construct(self):
        self.set_paths_location()
        self.set_packages()

    def set_packages(self):
        packages = []
        for name in os.listdir(self.path_pkg):
            if os.path.isfile(self.path_pkg + '/' + name + '/package.py'):
                packages.append(name)

        packages.sort()
        self.packages = packages

    def set_paths_location(self):
        # Base directory
        self.path_base = os.path.realpath(self.pwd).replace("/bot/__main__.py", "")

        # Mirror directory
        self.path_mirror = self.path_base + "/mirror"

        # Html directory
        self.path_www = self.path_base + "/www"

        # Packages directory
        self.path_pkg = self.path_base + "/pkg"
