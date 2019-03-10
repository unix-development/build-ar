#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
import textwrap
import subprocess

from core.container import container, get, config

def register():
    (container
        .register("environment.prepare_git", prepare_git)
        .register("environment.prepare_mirror", prepare_mirror)
        .register("environment.prepare_pacman", prepare_pacman)
        .register("environment.prepare_ssh", prepare_ssh))

def execute(commands):
    subprocess.Popen(commands, stderr=subprocess.PIPE, shell=True)

def prepare_mirror():
    execute("chmod 777" + get("path.mirror"))

def prepare_git():
    execute("""
    git config user.email '{email}';
    git config user.name '{name}';
    """.format(
        email=config("git.email"),
        name=config("git.name")
    ))

def prepare_ssh():
    execute("""
    eval $(ssh-agent);
    chmod 600 {base}/deploy_key;
    ssh-add {base}/deploy_key;
    mkdir -p ~/.ssh;
    chmod 0700 ~/.ssh;
    ssh-keyscan -t rsa -H {host} >> ~/.ssh/known_hosts;
    """.format(
        base=get("path.base"),
        host=config("ssh.host")
    ))

def prepare_pacman():
    database = config("database")
    mirror = get("path.mirror")

    if os.path.exists(mirror + "/" + database + ".db"):
        with open("/etc/pacman.conf", "a+") as fp:
            fp.write(textwrap.dedent("""
            [{database}]
            SigLevel = Optional TrustedOnly
            Server = file:///{mirror}
            """.format(
                database=database,
                mirror=mirror
            )))

    execute("sudo pacman -Sy")
