#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
import re
import sys
import time
import shutil
import subprocess

from datetime import datetime
from utils.git import git_remote_path
from utils.editor import edit_file, replace_ending, extract
from utils.terminal import output, title, bold, execute
from utils.validator import validate

def register(container):
    repository.set_packages()
    container.register("repository.synchronize", repository.synchronize)
    container.register("repository.create_database", repository.create_database)
    container.register("repository.deploy", repository.deploy)


class Repository():
    packages_to_check = []
    packages_updated = []

    def set_packages(self):
        packages_already_checked = []
        packages_list = app("packages")
        status_path = path("mirror") + "/packages_checked"

        if app("is_travis") is False:
            self.packages_to_check = packages_list
            return

        if not os.path.exists(status_path):
            os.mknod(status_path)
        else:
            today = datetime.now()
            last_modification = datetime.fromtimestamp(
                os.path.getctime(status_path))

            if today.date() > last_modification.date():
                with open(status_path, "w"): pass

        with open(status_path) as f:
            for cnt, line in enumerate(f):
                packages_already_checked.append(line.strip())

        self.packages_to_check = list(
            set(packages_list) - set(packages_already_checked))

        if len(self.packages_to_check) == 0:
            self.packages_to_check = packages_list
            with open(status_path, 'w'): pass
        else:
            self.packages_to_check.sort()
            self.packages_to_check = self.packages_to_check + packages_already_checked

    def append_to_packages_checked(self, name):
        with open(path("mirror") + "/packages_checked", "a+") as f:
            f.write(name + "\n")

    def synchronize(self):
        sys.path.append(path("pkg"))

        for name in self.packages_to_check:
            if self.update_package(name):
                self.packages_updated.append(name)

                if app("is_travis"): return

    def update_package(self, name, is_dependency = False):
        package = Package(name, is_dependency)
        package.separator()
        package.prepare()
        package.check_config()
        package.pull()
        package.check_build()
        package.make()

        self.append_to_packages_checked(name)

        if package.updated:
            self.packages_updated.append(name)
            return True

    def deploy(self):
        if len(self.packages_updated) == 0: return

        print(title("Deploy to host remote") + "\n")

        os.chdir(path("base"))

        execute([
            "rsync \
                -avz \
                --update \
                --copy-links \
                --progress -e 'ssh -i ./deploy_key -p %i' \
                %s/* %s@%s:%s" % (
                repo("ssh.port"),
                path("mirror"),
                repo("ssh.user"),
                repo("ssh.host"),
                repo("ssh.path")
            )
        ])

        if app("is_travis"):
            print(title("Deploy to git remote") + "\n")

            execute([
                "git push https://${GITHUB_TOKEN}@%s HEAD:master" % git_remote_path()
            ])

    def create_database(self):
        if len(self.packages_updated) == 0: return

        print(title("Create database") + "\n")

        database = repo("database")
        path_mirror = path("mirror")
        os.chdir(path_mirror)

        execute([
            "rm -f ./%s.old" % database,
            "rm -f ./%s.files" % database,
            "rm -f ./%s.files.tar.gz" % database,
            "rm -f ./%s.files.tar.gz.old" % database,
            "repo-add --nocolor ./%s.db.tar.gz ./*.pkg.tar.xz" % database
        ])


class Package():
    updated = False

    def __init__(self, name, is_dependency):
        __import__(name + ".package")

        self.name = name
        self.is_dependency = is_dependency
        self.path_pkg = path("pkg")
        self.path_mirror = path("mirror")

        self.path = self.path_pkg + "/" + self.name
        self.package = sys.modules[self.name + ".package"]

        os.chdir(self.path_pkg + "/" + self.name)

    def is_exists_in_package(self, name):
        try:
            getattr(self.package, name)
            return True
        except AttributeError:
            return False

    def check_build(self):
        print(bold("Validating PKGBUILD:"))

        error = {
            "not_exists": "PKGBUILD does not exists.",
            "undefined": "No %s variable is defined in PKGBUILD",
            "name": "The name defined in package.py is the not the same in PKGBUILD."
        }

        validate(
            error=error["not_exists"],
            target="is exists",
            valid=os.path.isfile("PKGBUILD")
        )

        validate(
            error=error["undefined"] % "pkgver",
            target="version",
            valid=self._version
        )

        valid = True
        exception = ""

        if not self._name:
            exception = error["undefined"] % "pkgname"
            valid = False

        elif self.name not in self._name.split(" "):
            exception = error["name"]
            valid = False

        validate(
            error=exception,
            target="name",
            valid=valid
        )

    def check_config(self):
        print(bold("Validating package.py:"))

        error = {
            "undefined": "No %s variable is defined in " + self.name + " package.py",
            "name": "The directory name and the name defined in package.py is the not the same."
        }

        validate(
            error=error["undefined"] % "source",
            target="source",
            valid=self.is_exists_in_package("source")
        )

        valid = True
        exception = ""

        if self.is_exists_in_package("name") is False:
            exception = error["undefined"] % "name"
            valid = False
        elif self.name != self.package.name:
            exception = error["name"]
            valid = False

        validate(
            error=exception,
            target="name",
            valid=valid
        )

    def separator(self):
        print(title(self.name))

    def prepare(self):
        self.set_values()
        self.set_utils()
        self.clean_directory()

    def set_values(self):
        self._version = extract(self.path, "pkgver")
        self._name = extract(self.path, "pkgname")
        self._depends = extract(self.path, "depends").split(" ")
        self._makedepends = extract(self.path, "makedepends").split(" ")

    def read(self):
        command = "echo $(source ./PKGBUILD && echo ${depends[@]} ${makedepends[@]})"
        process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True, executable='/bin/bash')
        line = process.stdout.readlines()[0]

        return line.strip().decode("UTF-8").split(" ")

    def remove_overwriting_function(self):
        try:
            output("source ./PKGBUILD; type pkgver &> /dev/null")

            search = False
            for line in edit_file("PKGBUILD"):
                if line.startswith("pkgver()"):
                    search = True
                    continue
                elif search is True:
                    if line.startswith("}"):
                        search = False
                    continue

                print(line)
        except:
            pass

    def make(self):
        self.remove_overwriting_function()

        if "pre_build" in dir(self.package):
            self.package.pre_build()

        if self.has_new_version() or self.is_dependency:
            self.updated = True
            self.verify_dependencies()

            if len(repository.packages_updated) > 0 and \
               app("is_travis"): return

            self.commit()
            self.build()

    def commit(self):
        if output("git status . --porcelain | sed s/^...//") and app("is_travis"):
            print(bold("Commit changes:"))

            execute([
                "git add .",
                "git commit -m \"Bot: Add last update into " + self.package.name + " package ~ version " + self._version + "\""
            ])

    def has_new_version(self):
        if output("git status . --porcelain | sed s/^...//"):
            return True

        for f in os.listdir(self.path_mirror):
            if f.startswith(self.package.name + '-' + self._version + '-'):
                return False

        return True

    def verify_dependencies(self):
        redirect = False
        for dependency in self.read():
            try:
                output("pacman -Sp " + dependency + " &>/dev/null")
                continue
            except:
                if dependency not in app("packages"):
                    sys.exit("\nError: %s is not part of the official package and can't be found in pkg directory." % dependency)

                if dependency not in repository.packages_updated:
                    redirect = True
                    repository.update_package(dependency, True)

        if redirect is True and app("is_travis") is False:
            self.separator()

        os.chdir(self.path_pkg + "/" + self.name)

    def build(self):
        print(bold("Build package:"))

        execute([
            "makepkg \
                --clean \
                --install \
                --nocheck \
                --nocolor \
                --noconfirm \
                --skipinteg \
                --syncdeps",
            "mv *.pkg.tar.xz " + self.path_mirror
        ]);

    def pull(self):
        print(bold("Clone repository:"))

        execute([
            "git init --quiet",
            "git remote add origin " + self.package.source,
            "git pull origin master",
            "rm -rf .git"
        ])

        if os.path.isfile(".SRCINFO"):
            os.remove(".SRCINFO")

    def clean_directory(self):
        files = os.listdir(".")
        for f in files:
            if os.path.isdir(f):
                os.system("rm -rf " + f)
            elif os.path.isfile(f) and f != "package.py":
                os.remove(f)

    def set_utils(self):
        self.package.edit_file = edit_file
        self.package.replace_ending = replace_ending


repository = Repository()
