#!/usr/bin/env python

"""
Copyright (c) Build Your Own Arch Linux Repository developers
See the file 'LICENSE' for copying permission
"""

import os
import sys
import yaml

from core.system import system
from util.process import execute
from util.process import output
from util.attr import attr


class App():
    package = []
    need_to_update = []

    def __init__(self):
        self._set_path()
        self._set_repository()
        self._set_system()
        self._set_package_in_directory()
        self._set_package_to_update()
        self._set_environment()
        self._set_runner()

    def has(self, name):
        if name == "ssh":
            for key in ["user", "port", "host", "path"]:
                if getattr(self.ssh, key) is not None:
                    return True

    def _set_system(self):
        self.system = system
        self.system.module = attr({
            "need_update": os.path.join(self.path.mirror, "to_update")
        })

    def _get_base_path(self):
        return os.path.realpath(__file__).replace("/src/core/app.py", "")

    def _set_path(self):
        root = self._get_base_path()

        self.path = attr({
            "base": root,
            "mirror": os.path.join(root, "mirror"),
            "pkg": os.path.join(root, "pkg"),
            "tmp": os.path.join(root, "tmp"),
            "log": os.path.join(root, "log"),
            "www": os.path.join(root, "bot/www")
        })

        execute(f"""
        mkdir -p {self.path.log};
        mkdir -p {self.path.tmp};
        mkdir -p {self.path.mirror};
        """)

    def _get_repository_content(self):
        path = os.path.join(self.path.base, "repository.yml")

        if os.path.isfile(path):
            with open(path, "r") as f:
                try:
                    return attr(yaml.safe_load(f))
                except:
                    return attr({})

        return attr({})

    def _set_repository(self):
        content = self._get_repository_content()

        self.ssh = attr()
        self.website = content.url
        self.database = content.database

        try:
            self.github_token = content.github.token
        except:
            self.github_token = None

        for key in [ "user", "port", "host", "path" ]:
            try:
                self.ssh[key] = content.ssh[key]
            except:
                self.ssh[key] = None

        if content.auto_update is list:
            self.auto_update = content.auto_update
        else:
            self.auto_update = []

    def _set_package_in_directory(self):
        for name in os.listdir(self.path.pkg):
            path = os.path.join(self.path.pkg, name, "package.py")
            if os.path.isfile(path):
                self.package.append(name)

        self.package.sort()

    def _set_package_to_update(self):
        content = self.system.get("need_update")

        for name in content:
            if name in self.package:
                self.need_to_update.append(name)

    def _set_environment(self):
        self.is_travis = ("TRAVIS" in os.environ and os.environ["TRAVIS"] != "")
        self.remote_path = output('git remote get-url origin') \
            .replace('https://', '') \
            .replace('http://', '') \
            .replace('git://', '')

        self.remote_user = self.remote_path.split("/")[1]

    def _set_runner(self):
        self.runner = None

        if len(sys.argv) == 2:
            self.runner = sys.argv[1]

app = App()
