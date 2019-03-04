#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
import re
import sys
import shutil
import subprocess

from utils.editor import edit_file, replace_ending, extract
from utils.terminal import output
from utils.constructor import constructor

builder = []

def execute(name, self):
    module = package(
       name=name,
       packages=self.packages,
       path_pkg=self.path_pkg,
       path_mirror=self.path_mirror,
       is_travis=self.is_travis
    )

    module.separator()
    module.prepare()
    module.pull()

    if module.make() is True:
        builder.append(name)
        return True


class new(constructor):
    def build(self):
        sys.path.append(self.path_pkg)

        for name in self.packages:
            if name not in builder:
                if execute(name, self) is True and self.is_travis() is True:
                    return


class package(constructor):
    def construct(self):
        __import__(self.name + ".package")

        self.path = self.path_pkg + "/" + self.name
        self.package = sys.modules[self.name + ".package"]

        os.chdir(self.path_pkg + "/" + self.name)

    def separator(self):
        line = "── %s " % self.name
        line += "─" * (55 - len(self.name))

        print("\n%s" % line)

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

            if len(builder) > 0 and self.is_travis() is True:
                return True

            self.build()
            self.commit()

            return True

    def commit(self):
        os.system(
            "git add . && " + \
            "git commit -m \"Bot: Add last update into " + self.package.name + " package ~ version " + self.version + "\"")

    def has_new_version(self):
        if output("git status . --porcelain | sed s/^...//") is None:
            return False

        for f in os.listdir(self.path_mirror):
            if f.startswith(self.name + '-' + self.version + '-'):
                return False

        return True

    def verify_dependencies(self):
        redirect = False
        official = []
        aur = []

        for dependency in self.read():
            try:
                output("pacman -Ssq %s | grep '^%s$'" % (dependency, dependency))
                official.append(dependency)
            except:
                aur.append(dependency)
                pass

        for name in aur:
            if name not in self.packages:
                sys.exit("\nError: %s is not part of the official package and can't be found in pkg directory." % name)

            if name not in builder:
                redirect = True
                execute(name, self)

        if redirect is True and self.is_travis() is False:
            self.separator()

        os.chdir(self.path_pkg + "/" + self.name)

    def build(self):
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
        print("Clone repository:")

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
