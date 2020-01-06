#!/usr/bin/env python

"""
Copyright (c) Build Your Own Arch Linux Repository developers
See the file 'LICENSE' for copying permission
"""

import os
import sys
import textwrap
import subprocess

from core.data import conf
from core.data import paths
from core.data import remote_repository
from utils.style import bold
from utils.process import output
from utils.process import strict_execute


class Environment(object):
    def prepare_mirror(self):
        remote = output("git ls-files " + paths.mirror + " | awk -F / '{print $2}'").split("\n")
        files = os.listdir(paths.mirror)

        for f in ["validation_token", "packages_checked"]:
            if f in files:
                files.remove(f)

        if len(files) != len(remote) or not remote_repository():
            return

        print(bold("Pull remote mirror directory files:"))

        strict_execute(f"""
        scp -i {paths.base}/deploy_key -P {conf.ssh_port} \
            {conf.ssh_user}@{conf.ssh_host}:{conf.ssh_path}/* \
            {paths.mirror}/;

        ssh -i {paths.base}/deploy_key -p {conf.ssh_port} \
            {conf.ssh_user}@{conf.ssh_host} \
            touch {conf.ssh_path}/*;
        """)

    def prepare_git(self):
        self._execute(
            "git config --global user.email 'uvobot@lognoz.org'; "
            "git config --global user.name 'uvobot';"
        )

    def prepare_ssh(self):
        if not remote_repository():
            return

        self._execute(
            "eval $(ssh-agent); "
            "chmod 600 ./deploy_key; "
            "ssh-add ./deploy_key; "
            "mkdir -p ~/.ssh; "
            "chmod 0700 ~/.ssh; "
            "ssh-keyscan -t rsa -H %s >> ~/.ssh/known_hosts; "
            % conf.ssh_host
        )

    def prepare_pacman(self):
        content = ("""
        [%s]
        SigLevel = Optional TrustedOnly
        Server = file:///%s
        """ % (conf.db, paths.mirror))

        self._execute("sudo chmod 777 /etc/pacman.conf")

        if os.path.exists(os.path.join(paths.mirror, conf.db + ".db")):
            with open("/etc/pacman.conf", "a+") as fp:
                fp.write(textwrap.dedent(content))

        self._execute("sudo pacman -Sy")

    def _in_mirror(self, packages, fp):
        for package in packages:
            if fp.startswith(package):
                return True

        return False

    def _get_mirror_packages(self):
        packages = []
        for root, dirs, files in os.walk(paths.mirror):
            for fp in files:
                if not fp.endswith(".tar.xz"):
                    continue

                packages.append(fp)

        return packages

    def _execute(self, commands):
        subprocess.run(
            commands,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True
        )


environment = Environment()
