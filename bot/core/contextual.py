#!/usr/bin/env python

"""
Copyright (c) Build Your Own Arch Linux Repository developers
See the file 'LICENSE' for copying permission
"""

import os
import yaml

from core.data import conf
from core.data import paths
from core.settings import ALIAS_CONFIGS
from core.settings import ALLOWED_CONFIGS
from utils.process import strict_execute


def set_paths(root):
    paths.base = root
    paths.mirror = os.path.join(root, "mirror")
    paths.log = os.path.join(root, "log")
    paths.pkg = os.path.join(root, "pkg")
    paths.tmp = os.path.join(root, "tmp")
    paths.www = os.path.join(root, "bot/www")

def set_directories():
    strict_execute(f"""
    mkdir -p {paths.log};
    mkdir -p {paths.tmp};
    mkdir -p {paths.mirror};
    """)

def get_base_path():
    return os.path.realpath(__file__).replace("/bot/core/contextual.py", "")

def set_repository():
    matches = []

    for name in os.listdir(paths.pkg):
        path = os.path.join(paths.pkg, name, "package.py")

        if os.path.isfile(path):
            matches.append(name)

    matches.sort()
    conf.packages = get_sorted_packages(matches)

def get_sorted_packages(matches):
    path = os.path.join(paths.mirror, "packages_checked")

    if not os.path.exists(path):
        os.mknod(path)

    with open(path) as fp:
        checked = fp.read().splitlines()
        checked = list(dict.fromkeys(checked))
        deleted = list(set(checked) - set(matches))

        i = 0
        while(i < len(deleted)):
            checked.remove(deleted[i])
            i = i + 1

    not_checked = list(set(matches) - set(checked))

    if len(not_checked) == 0:
        with open(path, "w"):
            pass

        return matches
    else:
        not_checked.sort()
        return (not_checked + checked)

def set_configs():
    conf.updated = []
    conf.package_to_test = None
    conf.environment = "prod"

    content = None
    path = os.path.join(paths.base, "repository.yml")

    if os.path.isfile(path):
        with open(path, "r") as fp:
            try:
                content = yaml.safe_load(fp)
            except:
                content = None

    for i, name in enumerate(ALLOWED_CONFIGS):
        value = content

        for j in name.split("."):
            try:
                value = value[j]
            except Exception:
                value = None

        conf[ALIAS_CONFIGS[i]] = value
