#!/usr/bin/env python

"""
Copyright (c) Build Your Own Arch Linux Repository developers
See the file 'LICENSE' for copying permission
"""

import os
import sys
import time
import textwrap
import subprocess

from core.app import app
from util.process import execute
from util.process import output
from util.style import bold


class Environment():
    """
    Main environment class used to prepare ssh, git and mirror.
    """
    is_pacman_initialized = False

    def prepare_ssh(self):
        """
        Preparing ssh before to interact with the remote.
        """
        execute(f"""
        eval $(ssh-agent);
        chmod 600 ./deploy_key;
        ssh-add ./deploy_key;
        mkdir -p ~/.ssh;
        chmod 0700 ~/.ssh;
        ssh-keyscan -t rsa -H {app.ssh.host} >> ~/.ssh/known_hosts;
        """)

        with open("/home/bot/.ssh/config", "w") as f:
            f.write(f"""
            LogLevel ERROR
            Host {app.ssh.host}
                HostName {app.ssh.host}
                User {app.ssh.user}
                Port {app.ssh.port}
                IdentityFile {app.path.base}/deploy_key
            """)
            f.close()

    def prepare_git(self):
        """
        Preparing git by setting user name and email. Uvobot is used
        to commit repository changes.
        """
        execute("""
        git config --global user.email 'uvobot@lognoz.org';
        git config --global user.name 'uvobot';
        """)

    def prepare_mirror(self):
        """
        Preparing mirror by verifing if we can pull files online.
        """
        black_list = [ "validation_token", "packages_checked" ]
        staged = output("git ls-files " + app.path.mirror).strip()
        in_directory = os.listdir(app.path.mirror)

        if staged != "":
            black_list = staged.split("\n") + black_list

        for f in black_list:
            if f in in_directory:
                in_directory.remove(f)

        if not app.has("ssh") or in_directory != []:
            return

        print(bold("Updating local mirror directory... "))

        command = (f"""
        rsync \
            --update \
            --progress \
            {app.ssh.user}@{app.ssh.host}:{app.ssh.path}/libc* \
            {app.path.mirror}/
        """)

        os.system(command)

    def syncronize_database(self):
        """
        Adding database to pacman.conf and syncronize custom database.
        """
        path = app.path.mirror + "/" + app.database + ".db"

        if not self.is_pacman_initialized:
            execute("sudo chmod 777 /etc/pacman.conf")

            if os.path.exists(path) is False:
                return

            with open("/etc/pacman.conf", "a+") as fp:
                fp.write(textwrap.dedent(f"""
                [{app.database}]
                SigLevel = Optional TrustedOnly
                Server = file://{app.path.mirror}
                """))

            self.is_pacman_initialized = True

        execute(f"""
        sudo cp {path} /var/lib/pacman/sync/
        """)


environment = Environment()
