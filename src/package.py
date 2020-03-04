#!/usr/bin/env python

"""
Copyright (c) Build Your Own Arch Linux Repository developers
See the file 'LICENSE' for copying permission
"""

import os
import shutil
import subprocess

from imp import load_source
from core.app import app
from util.process import execute
from util.process import output
from util.process import extract


def _attribute_exists(module, name):
    try:
        getattr(module, name)
        return True
    except AttributeError:
        return False


class Package():
    error = []
    status = "success"

    def __init__(self, **parameter):
        self.name = parameter["name"]
        self.is_dependency = parameter["is_dependency"]
        self.path = os.path.join(app.path.pkg, self.name)

        # If it's a status check, prepare the environment.
        if parameter["is_status_checking"]:
            self._prepare_checking_environment()

        # Synchronize package.py
        self.module = load_source(self.name + ".package", os.path.join(self.path, "package.py"))

    def clean_directory(self):
        files = os.listdir(self.path)
        keep_files = []

        if _attribute_exists(self.module, "keep_files") and type(self.module.keep_files) is list:
            keep_files = self.module.keep_files

        for f in files:
            path = os.path.join(self.path, f)
            if os.path.isdir(path):
                shutil.rmtree(path)
            elif os.path.isfile(path) and f != "package.py" and f not in keep_files:
                os.remove(path)

    def validate_configuration(self):
        self._check_module_source()
        self._check_module_name()

    def pull_repository(self):
        self._execute(f"""
        git init --quiet;
        git remote add origin {self.module.source};
        git pull origin master;
        rm -rf .git;
        rm -f .gitignore;
        """)

    def set_real_version(self):
        path = os.path.join(self.path, "tmp")

        try:
            os.path.isfile(self.path + "/PKGBUILD")
            output("source " + self.path + "/PKGBUILD; type pkgver &> /dev/null")
        except:
            return

        exit_code = self._execute(f"""
        mkdir -p ./tmp;
        cp -r `ls | grep -v tmp` ./tmp;
        makepkg \
            SRCDEST=./tmp \
            --nobuild \
            --nodeps \
            --nocheck \
            --nocolor \
            --noconfirm \
            --skipinteg;
        """)

        shutil.rmtree(path)

        if exit_code > 0:
            self.status = "error"
            self.error.append("An error append when executing makepkg")

    def set_variable(self):
        self._version = None
        self._name = None
        self._epoch = None

        if os.path.isfile(self.path + "/PKGBUILD"):
            self._version = extract(self.path, "pkgver")
            self._name = extract(self.path, "pkgname")
            self._epoch = extract(self.path, "epoch")

            if self._epoch:
                self._epoch += ":"

    def validate_build(self):
        self._check_build_exists()
        self._check_build_version()
        self._check_build_name()

    def need_update(self):
        if len(self.error) > 0:
            return False

        for f in os.listdir(app.path.mirror):
            if f.startswith(self.module.name + '-' + self._epoch + self._version + '-'):
                return False

        return True

    def _check_build_exists(self):
        if not os.path.isfile(self.path + "/PKGBUILD"):
            self.status = "error"
            self.error.append("PKGBUILD does not exists.")

    def _check_build_version(self):
        if not self._version:
            self.status = "error"
            self.error.append("No version variable is defined in PKGBUILD.")

    def _check_build_name(self):
        if not self._name:
            self.status = "error"
            self.error.append("No name variable is defined in PKGBUILD.")

    def _check_module_source(self):
        if not _attribute_exists(self.module, "source"):
            self.status = "error"
            self.error.append("No source variable is defined in package.py")

    def _check_module_name(self):
        if _attribute_exists(self.module, "name") is False:
            self.status = "error"
            self.error.append("No name variable is defined in package.py")

    def _prepare_checking_environment(self):
        temporary_source = os.path.join(app.path.tmp, self.name)
        execute(f"cp -rf {self.path} {temporary_source}")
        self.path = temporary_source

    def _execute(self, command):
        return subprocess.call(
            command,
            shell=True,
            cwd=self.path,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
