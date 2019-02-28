#!/usr/bin/env python

import mirror
import packages
import interface
import validator
import environment

from core import runner
from core import config
from core import contextual

contextual = contextual.new(
    pwd=__file__
)

config = config.new(
    path_base=contextual.path_base
)

validate = validator.new(
    config=config.get,
    path_base=contextual.path_base,
    path_pkg=contextual.path_pkg,
    path_mirror=contextual.path_mirror,
    packages=contextual.packages
)

environment = environment.new(
    config=config.get,
    path_base=contextual.path_base
)

interface = interface.new(
    config=config.get,
    packages=contextual.packages,
    path_pkg=contextual.path_pkg,
    path_www=contextual.path_www,
    path_mirror=contextual.path_mirror
)

packages = packages.new(
    config=config.get,
    packages=contextual.packages,
    path_pkg=contextual.path_pkg,
    path_mirror=contextual.path_mirror
)

mirror = mirror.new(
    config=config.get,
    is_travis=environment.is_travis,
    path_mirror=contextual.path_mirror
)

runner.new(
    validate=[
        validate.requirements,
        validate.files,
        validate.repository,
        environment.prepare_ssh,
        validate.ssh,
        validate.container
    ],
    build=[
        validate.requirements,
        validate.files,
        validate.travis,
        validate.repository,
        environment.prepare_ssh,
        validate.ssh,
        validate.container,
        environment.prepare_git,
        environment.prepare_pacman,
        packages.build,
        mirror.build,
        interface.build,
        mirror.deploy
    ]
)
