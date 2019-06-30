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
from utils.process import output
from utils.process import git_remote_path
from utils.process import strict_execute


class Environment(object):
    upstream = "github.com/unix-development/build-your-own-archlinux-repository"

    def pull_main_repository(self):
        if git_remote_path() == self.upstream:
            return

        print("Updating repository bot:")

        try:
            output("git remote | grep upstream")
        except:
            self._execute(f"git remote add upstream https://{self.upstream}")

        self._execute(
            "git fetch upstream; "
            "git pull --no-ff --no-commit -X theirs upstream master; "
            "git reset HEAD README.md; "
            "git checkout -- README.md; "
            "git commit -m 'Core: Pull main repository project';"
        )

        print("  [ ✓ ] up to date")

    def prepare_mirror(self):
        remote = output("git ls-files " + paths.mirror + " | awk -F / '{print $2}'").split("\n")
        local = os.listdir(paths.mirror)
        ssh = conf.user.ssh

        local.remove("validation_token")
        local.remove("packages_checked")

        if len(local) != len(remote):
            return

        print("\nPull remote mirror directory files:")

        strict_execute(f"""
        scp -i {paths.base}/deploy_key -P {ssh.port} \
            {ssh.user}@{ssh.host}:{ssh.path}/* \
            {paths.mirror}/
        """)

    def prepare_git(self):
        self._execute(
            "git config --global user.email 'uvobot@lognoz.org'; "
            "git config --global user.name 'uvobot';"
        )

    def prepare_ssh(self):
        self._execute(
            "eval $(ssh-agent); "
            "chmod 600 ./deploy_key; "
            "ssh-add ./deploy_key; "
            "mkdir -p ~/.ssh; "
            "chmod 0700 ~/.ssh; "
            "ssh-keyscan -t rsa -H %s >> ~/.ssh/known_hosts; "
            % conf.user.ssh.host
        )

    def prepare_pacman(self):
        content = ("""
        [%s]
        SigLevel = Optional TrustedOnly
        Server = file:///%s
        """ % (conf.user.database, paths.mirror))

        if os.path.exists(os.path.join(paths.mirror, conf.user.database + ".db")):
            with open("/etc/pacman.conf", "a+") as fp:
                fp.write(textwrap.dedent(content))

        self._execute("sudo pacman -Sy")

    def prepare_package_testing(self):
        conf.testing.environment = True
        conf.testing.package = None

        if len(sys.argv) > 2:
            conf.testing.package = sys.argv[2]

    def clean_mirror(self):
        if not os.path.exists(f"{paths.mirror}/{conf.user.database}.db"):
            return

        database = output(f"pacman -Sl {conf.user.database}")
        files = self._get_mirror_packages()
        packages = []

        for package in database.split("\n"):
            split = package.split(" ")
            packages.append(split[1] + "-" + split[2] + "-")

        for fp in files:
            if self._in_mirror(packages, fp) is False:
                os.remove(paths.mirror + "/" + fp)

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


def register():
    environment = Environment()

    return {
        "environment.clean_mirror": environment.clean_mirror,
        "environment.prepare_git": environment.prepare_git,
        "environment.prepare_mirror": environment.prepare_mirror,
        "environment.prepare_package_testing": environment.prepare_package_testing,
        "environment.prepare_pacman": environment.prepare_pacman,
        "environment.prepare_ssh": environment.prepare_ssh,
        "environment.pull_main_repository": environment.pull_main_repository
    }
