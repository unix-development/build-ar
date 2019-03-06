#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
import re
import sys
import shutil
import subprocess

from utils.git import git_remote_path
from utils.editor import edit_file, replace_ending, extract
from utils.terminal import output, title, bold
from utils.validator import validate

builder = []

def register(container):
    container.register("repository.synchronize", synchronize)
    container.register("repository.create_database", create_database)
    container.register("repository.deploy", deploy)

def synchronize():
    sys.path.append(path("pkg"))

    for name in app("packages"):
        if name not in builder:
            if execute(name) is True and app("is_travis") is True:
                return

def deploy():
    print(title("Deploy to host remote") + "\n")

    os.chdir(path("base"))

    os.system(
        "rsync -avz --update --copy-links --progress -e 'ssh -i ./deploy_key -p %i' %s/* %s@%s:%s" %
        (repo("ssh.port"), path("mirror"), repo("ssh.user"), repo("ssh.host"), repo("ssh.path")))

    if app("is_travis") is True:
        print(title("Deploy to git remote") + "\n")

        os.system("git push https://${GITHUB_TOKEN}@%s HEAD:master" % git_remote_path())

def create_database():
    print(title("Create database") + "\n")

    database = repo("database")
    path_mirror = path("mirror")
    os.chdir(path_mirror)

    scripts = [
        "rm -f ./%s.db" % database,
        "rm -f ./%s.old" % database,
        "rm -f ./%s.files" % database,
        "rm -f ./%s.db.tar.gz" % database,
        "rm -f ./%s.files.tar.gz" % database,
        "rm -f ./%s.files.tar.gz.old" % database,
        "repo-add --nocolor ./%s.db.tar.gz ./*.pkg.tar.xz" % database
    ]

    for script in scripts:
        os.system(script)

def execute(name):
    module = package(name)
    module.separator()
    module.prepare()
    module.validate()
    module.pull()

    if module.make() is True:
        builder.append(name)
        return True


class package():
    def __init__(self, name):
        __import__(name + ".package")

        self.name = name
        self.path_pkg = path("pkg")
        self.path_mirror = path("mirror")

        self.path = self.path_pkg + "/" + self.name
        self.package = sys.modules[self.name + ".package"]

        os.chdir(self.path_pkg + "/" + self.name)

    def is_exists_in_package(self, attribute):
        try:
            getattr(self.package, attribute)
            return True
        except AttributeError:
            return False

    def validate(self):
        print(bold("Validating package.py:"))

        error = {
            "undefined": "No %s variable is defined in " + self.name + " package.py",
            "name": "The directory name and the name variable defined in package.py is the not the same."
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
        self.set_utils()
        self.clean_directory()

    def read(self):
        command = 'echo $(source ./PKGBUILD && echo ${depends[@]} ${makedepends[@]})'
        process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True, executable='/bin/bash')
        line = process.stdout.readlines()[0]

        return line.strip().decode("UTF-8").split(" ")

    def make(self):
        self.version = extract(self.path, "pkgver")

        if "pre_build" in dir(self.package):
            self.package.pre_build()

        if self.has_new_version():
            self.verify_dependencies()

            if len(builder) > 0 and app("is_travis") is True:
                return True

            self.build()
            self.commit()

            return True

    def commit(self):
        print(bold("Commit changes:"))

        os.system(
            "git add . && " + \
            "git commit -m \"Bot: Add last update into " + self.package.name + " package ~ version " + self.version + "\"")

    def has_new_version(self):
        if output("git status . --porcelain | sed s/^...//") is None:
            return False

        for f in os.listdir(self.path_mirror):
            if f.startswith(self.package.name + '-' + self.version + '-'):
                return False

        return True

    def verify_dependencies(self):
        redirect = False
        official = []
        aur = []

        for dependency in self.read():
            try:
                output("pacman -T '%s'" % dependency)
                aur.append(dependency)
            except:
                official.append(dependency)
                pass

        for name in aur:
            if name not in app("packages"):
                sys.exit("\nError: %s is not part of the official package and can't be found in pkg directory." % name)

            if name not in builder:
                redirect = True
                execute(name, self)

        if redirect is True and app("is_travis") is False:
            self.separator()

        os.chdir(self.path_pkg + "/" + self.name)

    def build(self):
        print(bold("Build package:"))

        os.system(
            "makepkg \
                --clean \
                --install \
                --nocheck \
                --nocolor \
                --noconfirm \
                --skipinteg \
                --syncdeps; " \
            "mv *.pkg.tar.xz " + self.path_mirror);

    def pull(self):
        print(bold("Clone repository:"))

        os.system(
            "git init --quiet; "
            "git remote add origin " + self.package.source + "; "
            "git pull origin master; "
            "rm -rf .git;")

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
