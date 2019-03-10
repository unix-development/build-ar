#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
import json
import yaml

from core.container import (
    app, container
)


def register():
    set_contextual_paths()
    set_packages()
    set_repository()
    set_is_travis()
    set_texts()

def set_texts():
    container.register("text", {
        "exception": get_text("exception"),
        "content": get_text("content")
    })

def set_is_travis():
    container.register("is_travis",
        "TRAVIS" in os.environ and os.environ["TRAVIS"] != "")

def set_contextual_paths():
    base = get_base_path()

    (container
        .register("path.base", base)
        .register("path.mirror", base + "/mirror")
        .register("path.pkg", base + "/pkg")
        .register("path.www", base + "/www"))

def set_packages():
    packages = []
    path = app("path.pkg")

    for name in os.listdir(path):
        if os.path.isfile(path + "/" + name + "/package.py"):
            packages.append(name)

    packages.sort()
    container.register("packages", packages)

def set_repository():
    with open(app("path.base") + '/repository.json') as fp:
        repository = json.load(fp)

    container.register("repository", repository)

def get_text(abstract):
    path = "{base}/bot/text/{name}.yml".format(
        base=app("path.base"),
        name=abstract
    )

    with open(path, "r") as fp:
        return yaml.load(fp)

def get_base_path():
    return os.path.realpath(__file__).replace("/bot/core/contextual.py", "")
