#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
import re
import sys
import time
import shutil
import subprocess

from datetime import datetime
from core.container import return_self
from utils.editor import edit_file, replace_ending
from utils.process import output, strict_execute, git_remote_path, extract
from utils.style import title, bold
from utils.validator import validate


class Repository():
    def __init__(self):
        self.packages_updated = []

    def synchronize(self):
        sys.path.append(app.pkg)

        for name in app.packages:
            if self.verify_package(name):
                if app.is_travis: return

    def verify_package(self, name, is_dependency = False):
        package = Package(name, is_dependency)
        package.run()

        if package.updated:
            return True

    def create_database(self):
        if len(self.packages_updated) == 0: return

        print(title(text("content.repository.database")) + "\n")

        strict_execute("""
        rm -f {path}/{database}.old;
        rm -f {path}/{database}.files;
        rm -f {path}/{database}.files.tar.gz;
        rm -f {path}/{database}.files.tar.gz.old;
        """.format(
            database=config.database,
            path=app.mirror
        ))

        for package in self.packages_updated:
            strict_execute(f"""
            repo-add --nocolor \
                {app.mirror}/{config.database}.db.tar.gz \
                {app.mirror}/{package}-*.pkg.tar.xz
            """)

    def deploy(self):
        if len(self.packages_updated) == 0: return

        print(title(text("content.repository.deploy.ssh")) + "\n")

        strict_execute(f"""
        rsync \
            --archive \
            --compress \
            --copy-links \
            --delete \
            --recursive \
            --update \
            --verbose \
            --progress -e 'ssh -i {app.base}/deploy_key -p {config.ssh.port}' \
            {app.mirror}/ \
            {config.ssh.user}@{config.ssh.host}:{config.ssh.path}
        """)

        if app.is_travis:
            print(title(text("content.repository.deploy.git")) + "\n")
            strict_execute("git push https://${GITHUB_TOKEN}@%s HEAD:master" % git_remote_path())

    def set_package_checked(self, name):
        with open(f"{app.mirror}/packages_checked", "a+") as f:
            f.write(name + "\n")


class Validator():
    @return_self
    def module_source(self, package):
        validate(
            error=text("exception.repository.config.undefined") % ("source", package.name),
            target="source",
            valid=self._attribute_exists(package.module, "source")
        )

    @return_self
    def module_name(self, package):
        valid = True
        exception = ""

        if self._attribute_exists(package.module, "name") is False:
            exception = text("exception.repository.config.undefined") % ("name", package.name)
            valid = False
        elif package.name != package.module.name:
            exception = text("exception.repository.config.different.name")
            valid = False

        validate(
            error=exception,
            target="name",
            valid=valid
        )

    @return_self
    def build_exists(self):
        validate(
            error=text("exception.repository.build.not.exists"),
            target="is exists",
            valid=os.path.isfile("PKGBUILD")
        )

    @return_self
    def build_version(self, version):
        validate(
            error=text("exception.repository.build.undefined") % "version",
            target="version",
            valid=version
        )

    @return_self
    def build_name(self, module, name):
        valid = True
        exception = ""

        if not name:
            exception = text("exception.repository.build.undefined") % "name",
            valid = False
        elif module.name not in name.split(" "):
            exception = text("exception.repository.build.different.name")
            valid = False

        validate(
            error=exception,
            target="name",
            valid=valid
        )

    def _attribute_exists(self, module, name):
        try:
            getattr(module, name)
            return True
        except AttributeError:
            return False



class Package():
    updated = False

    def __init__(self, name, is_dependency):
        self._module = f"{name}.package"
        self._location = f"{app.pkg}/{name}"
        self._is_dependency = is_dependency

        __import__(self._module)
        os.chdir(self._location)

        self.name = name
        self.module = sys.modules[self._module]

    def run(self):
        self._separator()
        self._set_utils()
        self._clean_directory()
        self._validate_config()
        self._pull()
        self._set_real_version()

        if "pre_build" in dir(self.module):
            self.module.pre_build()

        self._set_variables()
        self._validate_build()
        self._make()

    def _make(self):
        if self._has_new_version() or self._is_dependency:
            self.updated = True
            self._verify_dependencies()

            if len(repository.packages_updated) > 0 and app.is_travis:
                return

            self._commit()
            self._build()

            repository.packages_updated += self._name.split(" ")

        repository.set_package_checked(self.name)

    def _build(self):
        print(bold(text("content.repository.build")))

        strict_execute(f"""
        makepkg \
            --clean \
            --install \
            --nocheck \
            --nocolor \
            --noconfirm \
            --skipinteg \
            --syncdeps;
        mv *.pkg.tar.xz {app.mirror}
        """);

    def _commit(self):
        if output("git status . --porcelain | sed s/^...//") and app.is_travis:
            print(bold(text("content.repository.commit")))

            strict_execute(f"""
            git add .;
            git commit -m "Bot: Add last update into {self.name} package ~ version {self._version}";
            """)

    def _set_real_version(self):
        try:
            os.path.isfile("./PKGBUILD")
            output("source ./PKGBUILD; type pkgver &> /dev/null")
        except:
            return

        print(bold(text("content.repository.get.version")))

        strict_execute("""
        mkdir -p ./tmp; \
        makepkg \
            --nobuild \
            --nodeps \
            --nocheck \
            --nocolor \
            --noconfirm \
            --skipinteg \
            SRCDEST=./tmp; \
        rm -rf ./tmp;
        """)

    def _verify_dependencies(self):
        redirect = False

        self.depends = extract(self._location, "depends")
        self.makedepends = extract(self._location, "makedepends")
        self._dependencies = (self.depends + " " + self.makedepends).strip()

        if self._dependencies == "":
            return

        for dependency in self._dependencies.split(" "):
            try:
                output("pacman -Sp " + dependency + " &>/dev/null")
                continue
            except:
                if dependency not in app.packages:
                    sys.exit("\n" + text("exception.repository.dependency") % dependency)

                if dependency not in repository.packages_updated:
                    redirect = True
                    repository.verify_package(dependency, True)

        if redirect is True and app.is_travis is False:
            self._separator()

        os.chdir(self._location)

    def _has_new_version(self):
        if output("git status . --porcelain | sed s/^...//"):
            return True

        for f in os.listdir(app.mirror):
            if f.startswith(self.module.name + '-' + self._version + '-'):
                return False

        return True

    def _pull(self):
        print(bold(text("content.repository.pull")))

        strict_execute(f"""
        git init --quiet;
        git remote add origin {self.module.source};
        git pull origin master;
        rm -rf .git;
        """)

        if os.path.isfile(".SRCINFO"):
            os.remove(".SRCINFO")

    def _set_variables(self):
        self._version = extract(self._location, "pkgver")
        self._name = extract(self._location, "pkgname")

    def _validate_config(self):
        print(bold(text("content.repository.validate.config")))

        (validator
            .module_source(self)
            .module_name(self))

    def _validate_build(self):
        print(bold(text("content.repository.validate.build")))

        (validator
            .build_exists()
            .build_version(self._version)
            .build_name(self, self._name))

    def _separator(self):
        print(title(self.name))

    def _clean_directory(self):
        files = os.listdir(".")
        for f in files:
            if os.path.isdir(f):
                os.system("rm -rf " + f)
            elif os.path.isfile(f) and f != "package.py":
                os.remove(f)

    def _set_utils(self):
        self.module.edit_file = edit_file
        self.module.replace_ending = replace_ending


repository = Repository()
validator = Validator()

def register():
    container.register("repository.synchronize", repository.synchronize)
    container.register("repository.create_database", repository.create_database)
    container.register("repository.deploy", repository.deploy)
