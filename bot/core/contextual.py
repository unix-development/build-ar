#!/usr/bin/env python

"""
Copyright (c) Build Your Own Arch Linux Repository developers
See the file 'LICENSE' for copying permission
"""

import os
import json

from utils.process import is_travis
from core.data import conf
from core.data import repository
from core.data import paths
from core.type import Dict


def set_contextual_paths(root):
    paths.base = root
    paths.mirror = os.path.join(root, "mirror")
    paths.pkg = os.path.join(root, "pkg")
    paths.www = os.path.join(root, "bot/www")

def base_path():
    return os.path.realpath(__file__).replace("/bot/core/contextual.py", "")

def set_repository():
    matches = []
    for name in os.listdir(paths.pkg):
        if os.path.isfile(os.path.join(paths.pkg, name, "package.py")):
            matches.append(name)

    matches.sort()

    if is_travis() is True:
        matches = get_sorted_packages(matches)

    repository.extend(matches)

def get_sorted_packages(matches):
    path = os.path.join(paths.mirror, "packages_checked")

    if not os.path.exists(path):
        os.mknod(path)

    with open(path) as fp:
        checked = fp.read().splitlines()

    not_checked = list(set(matches) - set(checked))
    if len(not_checked) == 0:
        with open(path, 'w'):
            pass
    else:
        not_checked.sort()

    return (not_checked + checked)

def set_configs():
    path = os.path.join(paths.base, "repository.json")
    if os.path.isfile(path):
        with open(path) as fp:
            conf.user = Dict(json.load(fp))

def register():
    set_contextual_paths(base_path())
    set_repository()
    set_configs()
