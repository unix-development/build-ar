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
from utils.process import execute_quietly


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
        execute_quietly("""
        git config --global user.email 'uvobot@lognoz.org';
        git config --global user.name 'uvobot';
        """)

    def prepare_ssh(self):
        if not remote_repository():
            return

        execute_quietly(f"""
        eval $(ssh-agent);
        chmod 600 ./deploy_key;
        ssh-add ./deploy_key;
        mkdir -p ~/.ssh;
        chmod 0700 ~/.ssh;
        ssh-keyscan -t rsa -H {conf.ssh_host} >> ~/.ssh/known_hosts;
        """)

    def prepare_pacman(self):
        path = paths.mirror + "/" + conf.db + ".db"

        execute_quietly("sudo chmod 777 /etc/pacman.conf")

        if os.path.exists(path) is False:
            return

        with open("/etc/pacman.conf", "a+") as fp:
            fp.write(textwrap.dedent(f"""
            [{conf.db}]
            SigLevel = Optional TrustedOnly
            Server = file:///{paths.mirror}
            """))

        execute_quietly(f"""
        sudo cp {path} /var/lib/pacman/sync/{conf.db}.db
        """)

    def prepare_package_testing(self):
        conf.environment = "dev"

        if len(sys.argv) > 2:
            conf.package_to_test = sys.argv[2]


environment = Environment()
