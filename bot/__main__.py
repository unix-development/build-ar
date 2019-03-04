#!/usr/bin/env python
# -*- coding:utf-8 -*-

from core.container import container
from core.runner import runner

container.bootstrap([
    "core.contextual",
    "environment",
    "validator",
    "interface",
    "repository"
])

runner.set("validate", [
    "validator.requirements",
    "validator.files",
    "validator.travis",
    "validator.repository",
    "environment.prepare_ssh",
    "validator.connection",
    "validator.content"
])

runner.set("build", [
    "validator.requirements",
    "validator.files",
    "validator.travis",
    "validator.repository",
    "environment.prepare_ssh",
    "validator.connection",
    "validator.content",
    "environment.prepare_git",
    "environment.prepare_pacman",
    "repository.synchronize",
    "repository.create_database",
    "interface.build",
    "repository.deploy"
])

container.register("runner", runner)
container.run()
