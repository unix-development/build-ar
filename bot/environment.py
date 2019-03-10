#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
import textwrap
import subprocess

from core.container import (
    app, config, container
)


def register():
    (container
        .register("environment.prepare_git", prepare_git)
        .register("environment.prepare_mirror", prepare_mirror)
        .register("environment.prepare_pacman", prepare_pacman)
        .register("environment.prepare_ssh", prepare_ssh))

def prepare_mirror():
    execute("chmod 777 %s" % app("path.mirror"))

def prepare_git():
    execute(
        "git config user.email '%s'; " % config("git.email") +
        "git config user.name '%s';" % config("git.name")
    )

def prepare_ssh():
    execute(
        "eval $(ssh-agent); " +
        "chmod 600 ./deploy_key; " +
        "ssh-add ./deploy_key; " +
        "mkdir -p ~/.ssh; " +
        "chmod 0700 ~/.ssh; " +
        "ssh-keyscan -t rsa -H %s >> ~/.ssh/known_hosts; "
        % config("ssh.host")
    )

def prepare_pacman():
    path = "{mirror}/{database}.db".format(
        database=config("database"),
        mirror=app("path.mirror")
    )

    content = ("""
        [{database}]
        SigLevel = Optional TrustedOnly
        Server = file:///{mirror}
        """.format(
            database=config("database"),
            mirror=app("path.mirror")
        )
    )

    if os.path.exists(path):
        with open("/etc/pacman.conf", "a+") as fp:
            fp.write(textwrap.dedent(content))

    execute("sudo pacman -Sy")

def execute(commands):
    subprocess.run(
        commands,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True
    )
