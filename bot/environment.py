#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
import sys
import textwrap
import subprocess

from utils.process import output, git_remote_path, strict_execute


class Environment(object):
    upstream = "github.com/unix-development/build-your-own-archlinux-repository"

    def pull_main_repository(self):
        if git_remote_path() == self.upstream: return

        print(text("content.environment.pull.repository"))

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

        print("  [ ✓ ] " + text("content.environment.up.to.date"))

    def prepare_mirror(self):
        sources = output("git ls-files " + app.mirror + " | awk -F / '{print $2}'").split("\n")

        if len(os.listdir(app.mirror)) != len(sources) + 1:
            return

        print(text("content.environment.prepare.mirror"))

        strict_execute(f"""
        scp -i {app.base}/deploy_key -P {config.ssh.port} \
            {config.ssh.user}@{config.ssh.host}:{config.ssh.path}/* \
            {app.mirror}/
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
            % config.ssh.host
        )

    def prepare_pacman(self):
        content = (f"""
        [{config.database}]
        SigLevel = Optional TrustedOnly
        Server = file:///{app.mirror}
        """)

        if os.path.exists(f"{app.mirror}/{config.database}.db"):
            with open("/etc/pacman.conf", "a+") as fp:
                fp.write(textwrap.dedent(content))

        self._execute("sudo pacman -Sy")

    def prepare_package_testing(self):
        app.testing.environment = True
        app.testing.package = None

        if len(sys.argv) > 2:
            app.testing.package = sys.argv[2]

    def clean_mirror(self):
        if not os.path.exists(f"{app.mirror}/{config.database}.db"):
            return

        database = output(f"pacman -Sl {config.database}")
        files = self._get_mirror_packages()
        packages = []

        for package in database.split("\n"):
            split = package.split(" ")
            packages.append(split[1] + "-" + split[2] + "-")

        for fp in files:
            if self._in_mirror(packages, fp) is False:
                os.remove(app.mirror + "/" + fp)

    def _in_mirror(self, packages, fp):
        for package in packages:
            if fp.startswith(package):
                return True

        return False

    def _get_mirror_packages(self):
        packages = []
        for root, dirs, files in os.walk(app.mirror):
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

    container.register("environment.clean_mirror", environment.clean_mirror)
    container.register("environment.prepare_git", environment.prepare_git)
    container.register("environment.prepare_mirror", environment.prepare_mirror)
    container.register("environment.prepare_package_testing", environment.prepare_package_testing)
    container.register("environment.prepare_pacman", environment.prepare_pacman)
    container.register("environment.prepare_ssh", environment.prepare_ssh)
    container.register("environment.pull_main_repository", environment.pull_main_repository)
