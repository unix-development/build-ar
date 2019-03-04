#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
import json

def register(container):
    set_contextual_paths(container)
    set_packages(container)
    set_repository(container)
    set_is_travis(container)

def get_base_path():
    return os.path.realpath(__file__).replace("/bot/core/contextual.py", "")

def set_is_travis(container):
    is_travis = "TRAVIS" in os.environ and os.environ["TRAVIS"] is not ""

    container.register("is_travis", is_travis)

def set_contextual_paths(container):
    path_base = get_base_path()

    container.register("path.base", path_base)
    container.register("path.mirror", path_base + "/mirror")
    container.register("path.www", path_base + "/www")
    container.register("path.pkg", path_base + "/pkg")

def set_packages(container):
    packages = []
    path_pkg = path("pkg")

    for name in os.listdir(path_pkg):
        if os.path.isfile(path_pkg + '/' + name + '/package.py'):
            packages.append(name)

    packages.sort()
    container.register("packages", packages)

def set_repository(container):
    with open(path("base") + '/repository.json') as f:
        repository = json.load(f)

    container.register("repository", repository)
