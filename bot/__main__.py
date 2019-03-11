
#!/usr/bin/env python
# -*- coding:utf-8 -*-

from core.runner import runner
from core.container import container

import core.contextual
import environment
import interface
import repository
import validator

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
    "interface.create",
    "repository.deploy"
])

container.register("runner", runner)
container.run()
