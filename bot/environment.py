#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
from utils.constructor import constructor

class new(constructor):
    def execute(self, scripts):
        os.system("(" + scripts + ") &>/dev/null")

    def is_travis(self):
        return "TRAVIS" in os.environ and os.environ["TRAVIS"] is not ""

    def prepare_git(self):
        email = self.config("git.email")
        name = self.config("git.name")

        self.execute(
            "git config user.email '%s'; " % email +
            "git config user.name '%s';" % name
        )

    def prepare_ssh(self):
        host = self.config("ssh.host")

        self.execute(
            "eval $(ssh-agent); " +
            "chmod 600 %s/deploy_key; " % self.path_base +
            "ssh-add %s/deploy_key; " % self.path_base +
            "mkdir -p ~/.ssh; " +
            "chmod 0700 ~/.ssh; " +
            "ssh-keyscan -t rsa -H %s >> ~/.ssh/known_hosts; " % host
        )

    def prepare_pacman(self):
        database = self.config("database")

        if os.path.exists(self.path_base + "/mirror/" + database + ".db") == False:
            return

        with open("/etc/pacman.conf", "r+") as file:
            for line in file:
                if line.strip() == "[%s]" % database:
                   break
                else:
                    content = [
                        "[%s]" % database,
                        "SigLevel = Optional TrustedOnly",
                        "Server = file:///%s/mirror" % self.path_base
                    ]

                    file.write("\n".join(content))

            self.execute("sudo pacman -Sy --noconfirm")
