#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os

def register(container):
    container.register("environment.prepare_git", prepare_git)
    container.register("environment.prepare_mirror", prepare_mirror)
    container.register("environment.prepare_pacman", prepare_pacman)
    container.register("environment.prepare_ssh", prepare_ssh)

def execute(scripts):
    os.system("(" + scripts + ") &>/dev/null")

def prepare_mirror():
    execute("chmod 777 %s/mirror" % path("base"))

def prepare_git():
    email = repo("git.email")
    name = repo("git.name")

    execute(
        "git config user.email '%s'; " % email +
        "git config user.name '%s';" % name)

def prepare_ssh():
    host = repo("ssh.host")
    path_base = path("base")

    execute(
        "eval $(ssh-agent); " +
        "chmod 600 %s/deploy_key; " % path_base +
        "ssh-add %s/deploy_key; " % path_base +
        "mkdir -p ~/.ssh; " +
        "chmod 0700 ~/.ssh; " +
        "ssh-keyscan -t rsa -H %s >> ~/.ssh/known_hosts; " % host
    )

def prepare_pacman():
    database = repo("database")
    path_base = path("base")

    if os.path.exists(path_base + "/mirror/" + database + ".db"):
        with open("/etc/pacman.conf", "r+") as file:
            for line in file:
                if line.strip() == "[%s]" % database:
                   break
                else:
                    content = [
                        "[%s]" % database,
                        "SigLevel = Optional TrustedOnly",
                        "Server = file:///%s/mirror" % path_base
                    ]

                    file.write("\n".join(content))

    execute("sudo pacman -Sy --noconfirm")
