#!/usr/bin/env python

"""
Copyright (c) Build Your Own Arch Linux Repository developers
See the file 'LICENSE' for copying permission
"""

import os
import sys

from core.data import paths
from core.data import repository
from utils.editor import edit_file
from utils.editor import replace_ending
from utils.process import output
from utils.process import strict_execute
from utils.process import extract
from utils.process import is_travis
from utils.process import is_testing
from utils.style import title
from utils.style import bold
from utils.validator import validate


def check_module_source(package):
    validate(
        error="No %s variable is defined in %s package.py" % ("source", package.name),
        target="source",
        valid=_attribute_exists(package.module, "source")
    )

def check_module_name(package):
    valid = True
    exception = ""

    if _attribute_exists(package.module, "name") is False:
        exception = "No %s variable is defined in %s package.py" % ("name", package.name)
        valid = False

    elif package.name != package.module.name:
        exception = "The name defined in package.py is the not the same in PKGBUILD."
        valid = False

    validate(
        error=exception,
        target="name",
        valid=valid
    )

def check_build_exists():
    validate(
        error="PKGBUILD does not exists.",
        target="is exists",
        valid=os.path.isfile("PKGBUILD")
    )

def check_build_version(version):
    validate(
        error="No version variable is defined in PKGBUILD.",
        target="version",
        valid=version
    )

def check_build_name(module, name):
    valid = True
    exception = ""

    if not name:
        exception = "No name variable is defined in PKGBUILD."
        valid = False

    elif module.name not in name.split(" "):
        exception = "The name defined in package.py is the not the same in PKGBUILD."
        valid = False

    validate(
        error=exception,
        target="name",
        valid=valid
    )

def _attribute_exists(module, name):
    try:
        getattr(module, name)
        return True
    except AttributeError:
        return False

class Package():
    updated = False

    def __init__(self, name, is_dependency):
        self._module = name + ".package"
        self._location = os.path.join(paths.pkg, name)
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

        if "pre_build" in dir(self.module):
            self.module.pre_build()

        self._set_real_version()
        self._set_variables()
        self._validate_build()
        self._make()

    def _make(self):
        if self._has_new_version() or self._is_dependency:
            self.updated = True
            self._verify_dependencies()

            if len(packages_updated) > 0 and is_travis():
                return

            if is_testing() is False:
                self._commit()

            self._build()

            if is_testing():
                self._reset()
            else:
                packages_updated.extend(packages_updated + self._name.split(" "))
                set_package_checked(self.name)

    def _reset(self):
        strict_execute("""
        git reset HEAD -- . &> /dev/null;
        git checkout -- . &> /dev/null;
        git clean -fd . &> /dev/null;
        """)

    def _build(self):
        print(bold("Build package:"))

        strict_execute(f"""
        mkdir -p ./tmp; \
        makepkg \
            SRCDEST=./tmp \
            --clean \
            --install \
            --nocheck \
            --nocolor \
            --noconfirm \
            --skipinteg \
            --syncdeps; \
        """)

        if is_testing is False:
            strict_execute("mv *.pkg.tar.xz %s" % paths.mirror)

    def _commit(self):
        print(bold("Commit changes:"))

        if output("git status . --porcelain | sed s/^...//"):
            strict_execute(f"""
            git add .;
            git commit -m "Bot: Add last update into {self.name} package ~ version {self._version}";
            """)
        else:
            strict_execute(f"""
            git commit --allow-empty -m "Bot: Rebuild {self.name} package ~ version {self._version}";
            """)

    def _set_real_version(self):
        try:
            os.path.isfile("./PKGBUILD")
            output("source ./PKGBUILD; type pkgver &> /dev/null")
        except:
            return

        print(bold("Get real version:"))

        strict_execute("""
        mkdir -p ./tmp; \
        makepkg \
            SRCDEST=./tmp \
            --nobuild \
            --nodeps \
            --nocheck \
            --nocolor \
            --noconfirm \
            --skipinteg; \
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
                output("pacman -Sp '" + dependency + "' &>/dev/null")
                continue
            except:
                if dependency not in repository:
                    sys.exit("\nError: %s is not part of the official package and can't be found in pkg directory." % dependency)

                if dependency not in packages_updated:
                    redirect = True
                    repository.verify_package(dependency, True)

        if redirect is True and is_travis() is False:
            self._separator()

        os.chdir(self._location)

    def _has_new_version(self):
        if output("git status . --porcelain | sed s/^...//"):
            return True

        for f in os.listdir(app.mirror):
            if f.startswith(self.module.name + '-' + self._epoch + self._version + '-'):
                return False

        return True

    def _pull(self):
        print(bold("Clone repository:"))

        strict_execute(f"""
        git init --quiet;
        git remote add origin {self.module.source};
        git pull origin master;
        rm -rf .git;
        rm -f .gitignore;
        """)

        if os.path.isfile(".SRCINFO"):
            os.remove(".SRCINFO")

    def _set_variables(self):
        self._version = extract(self._location, "pkgver")
        self._name = extract(self._location, "pkgname")
        self._epoch = extract(self._location, "epoch")

        if self._epoch:
            self._epoch += ":"

    def _validate_config(self):
        print(bold("Validate package.py:"))

        check_module_source(self)
        check_module_name(self)

    def _validate_build(self):
        print(bold("Validate PKGBUILD:"))

        check_build_exists()
        check_build_version(self._version)
        check_build_name(self, self._name)

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
