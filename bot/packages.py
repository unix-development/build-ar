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

def new_package(name, self):
    return package(
       name = name,
       packages = self.packages,
       path_pkg = self.path_pkg,
       path_mirror = self.path_mirror
    )

class new(constructor):
    def build(self):
        sys.path.append(self.path_pkg)

        for name in self.packages:
            if name not in builder:
                module = new_package(name, self)

             #if module.compiled == True:
             #   return

class package(constructor):
    compiled = False

    def construct(self):
        __import__(self.name + ".package")

        self.path = self.path_pkg + "/" + self.name
        self.package = sys.modules[self.name + ".package"]

        self.add_to_builder()
        self.separator()
        self.chdir()
        self.prepare()
        self.pull()
        self.make()

    def add_to_builder(self):
        builder.append(self.name)

    def chdir(self):
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
            self.build()

        #if not self.is_builded():
        #   self.compiled = True
        #   self.commit()
        #   self.install_dependencies()

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
                exit("exeption")

            redirect = True
            module = package(
                name = name,
                packages = self.packages,
                path_pkg = self.path_pkg,
                path_mirror = self.path_mirror
            )

        if redirect == True:
            self.separator()

        os.chdir(self.path_pkg + "/" + self.name)

    def build(self):
        os.system(
            "makepkg --clean --syncdeps --skipinteg --noconfirm --nocheck --install && " \
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
