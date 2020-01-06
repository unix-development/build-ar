#!/usr/bin/env python

"""
Copyright (c) Build Your Own Arch Linux Repository developers
See the file 'LICENSE' uor copying permission
"""

from environment import environment
from interface import interface
from repository import repository
from validator import validator

from core.contextual import get_base_path
from core.contextual import set_configs
from core.contextual import set_paths
from core.contextual import set_directories
from core.contextual import set_repository
from core.runner import runner


def set_contextual():
    base = get_base_path()
    set_paths(base)
    set_directories()
    set_repository()
    set_configs()

def main():
    set_contextual()

    runner.set("validation", [
        validator.requirements,
        validator.files,
        validator.travis,
        validator.content,
        validator.configs,
        environment.prepare_ssh,
        validator.connection
    ])

    runner.set("build", [
        validator.requirements,
        validator.files,
        validator.travis,
        validator.content,
        validator.configs,
        environment.prepare_ssh,
        validator.connection,
        environment.prepare_git,
        environment.prepare_mirror,
        environment.prepare_pacman,
        repository.clean_database,
        repository.synchronize,
        repository.create_database,
        interface.create,
        repository.deploy
    ])

    runner.set("update", [
        environment.prepare_git,
        repository.pull_main_repository
    ])

    runner.set("test", [
        repository.test_package
    ])

    for execute in runner.get():
        execute()


if __name__ == "__main__":
    main()
