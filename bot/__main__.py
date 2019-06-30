#!/usr/bin/env python

"""
Copyright (c) Build Your Own Arch Linux Repository developers
See the file 'LICENSE' for copying permission
"""

from core.runner import runner
from core.container import container

container.bootstrap([
    "core.contextual",
    "environment",
    "validator",
    "interface",
    "repository"
])

runner.set("validation", [
    "validator.requirements",
    "validator.files",
    "validator.travis",
    "validator.content",
    "environment.prepare_ssh",
    "validator.connection",
    "validator.content"
])

runner.set("package", [
    "validator.requirements",
    "validator.files",
    "environment.prepare_package_testing",
    "validator.content",
    "environment.prepare_pacman",
    "repository.test_package",
    "repository.create_database"
])

runner.set("update", [
    "environment.prepare_git",
    "environment.pull_main_repository"
])

runner.set("build", [
    "validator.requirements",
    "validator.files",
    "validator.travis",
    "validator.content",
    "environment.prepare_ssh",
    "validator.connection",
    "validator.content",
    "environment.prepare_git",
    "environment.prepare_mirror",
    "environment.prepare_pacman",
    "environment.clean_mirror",
    "repository.synchronize",
    "repository.create_database",
    "interface.create",
    "repository.deploy"
])

container.register("runner", runner)
container.run()
