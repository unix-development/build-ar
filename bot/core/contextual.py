#!/usr/bin/env python

"""
Copyright (c) Build Your Own Arch Linux Repository developers
See the file 'LICENSE' for copying permission
"""

import os
import json
import yaml

from datetime import datetime
from core.settings import configs
from core.settings import packages
from core.settings import paths


class Contextual(object):
    def set_contextual_paths(self):
        root = self._get_base_path()

        paths.base = root
        paths.mirror = os.path.join(root, "mirror")
        paths.pkg = os.path.join(root, "pkg")
        paths.www = os.path.join(root, "bot/www")

    def set_packages(self):
        for name in os.listdir(paths.pkg):
            if os.path.isfile(os.path.join(paths.pkg, name, "package.py")):
                packages.append(name)

        packages.sort()

        if app.is_travis is True:
            packages = self._get_packages_sorted(packages)

    def set_repository(self):
        path = os.path.join(paths.base, "repository.json")
        if os.path.isfile(path):
            with open(path) as fp:
                configs = Attr(json.load(fp))

    def set_texts(self):
        app.text = dict(
            exception = self._get_text("exception"),
            content = self._get_text("content")
        )

    def _get_text(self, abstract):
        path = f"{app.base}/bot/text/{abstract}.yml"

        with open(path, "r") as fp:
            return yaml.load(fp)

    def _get_packages_sorted(self, packages):
        path = f"{app.mirror}/packages_checked"
        if not os.path.exists(path):
            os.mknod(path)
        else:
            today = datetime.now()
            last_modification = datetime.fromtimestamp(
                os.path.getctime(path))

            if today.date() > last_modification.date():
                with open(path, "w"):
                    pass

        with open(path) as fp:
            packages_checked_today = list(
                set(fp.read().splitlines())
            )

        packages_tmp = list(
            set(packages) - set(packages_checked_today)
        )

        if len(packages_tmp) == 0:
            with open(path, 'w'):
                pass

            return packages
        else:
            packages_tmp.sort()
            return (packages_tmp + packages_checked_today)

    def _get_value(self, abstract, repository):
        value = repository
        for name in abstract.split('.'):
            if name in value:
                value = value[name]

        if value != repository:
            return repository
        else:
            return ""

    def _get_base_path(self):
        return os.path.realpath(__file__).replace("/bot/core/contextual.py", "")


def register():
    contextual = Contextual()

    contextual.set_contextual_paths()
    contextual.set_packages()
    contextual.set_repository()
    contextual.set_texts()
