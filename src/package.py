#!/usr/bin/env python

"""
Copyright (c) Build Your Own Arch Linux Repository developers
See the file 'LICENSE' for copying permission
"""

import os
import sys
import shutil
import subprocess

from imp import load_source
from core.app import app
from util.process import execute
from util.process import output
from util.process import extract
from util.style import red


def _attribute_exists(module, name):
    """
    Checking if an attribute exists in module.
    """
    try:
        getattr(module, name)
        return True
    except AttributeError:
        return False


class Package():
    """
    Main package class used to build new version.
    """
    def __init__(self, **parameter):
        """
        Setting package parameters.
        """
        self.error = []
        self.name = parameter["name"]
        self.is_dependency = parameter["is_dependency"]
        self.path = os.path.join(app.path.pkg, self.name)

        # If it's a status check, prepare the environment.
        if parameter["is_status_checking"]:
            self._prepare_checking_environment()

        # Synchronize package.py
        self.module = load_source(self.name + ".package", os.path.join(self.path, "package.py"))

    def clean_directory(self):
        """
        Deleting all useless files to verify if there is any difference
        between the git repository pulled and the last commit.
        """
        files = os.listdir(self.path)
        keep_files = []

        if _attribute_exists(self.module, "keep_files") and type(self.module.keep_files) is list:
            keep_files = self.module.keep_files

        for f in files:
            path = os.path.join(self.path, f)
            if os.path.isdir(path):
                self._delete_directory(path)
            elif os.path.isfile(path) and f != "package.py" and f not in keep_files:
                os.remove(path)

    def validate_configuration(self):
        """
        Checking if the module configuration is valid.
        """
        self._check_module_source()
        self._check_module_name()

    def pull_repository(self):
        """
        Pulling git repository source.
        """
        self._execute(f"""
        git init --quiet;
        git remote add origin {self.module.source};
        git pull origin master;
        rm -rf .git;
        rm -f .gitignore;
        """)

    def set_real_version(self):
        """
        Setting the real PKGBUILD version by recompiling package.
        """
        path = os.path.join(self.path, "tmp")

        try:
            os.path.isfile(self.path + "/PKGBUILD")
            output("source " + self.path + "/PKGBUILD; type pkgver &> /dev/null")
        except:
            return

        makedepends = extract(self.path, "makedepends")
        if makedepends:
            self._execute(f"""
            sudo pacman --noconfirm -S {makedepends}
            """)

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

        self._delete_directory(path)

        if exit_code > 0:
            self.error.append("An error append when executing makepkg")

    def set_variable(self):
        """
        Setting variables define in PKGBUILD.
        """
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
        """
        Checking if the build is valid.
        """
        self._check_build_exists()
        if not self.has_error():
            self._check_build_version()
            self._check_build_name()

    def need_update(self):
        """
        Checking if package need to be updated.
        """
        if len(self.error) > 0:
            return False

        for f in os.listdir(app.path.mirror):
            if f.startswith(self.module.name + '-' + self._epoch + self._version + '-'):
                return False

        return True

    def has_error(self):
        """
        Checking if there is any errors.
        """
        if len(self.error) > 0:
            return True
        return False

    def verify_dependencies(self):
        """
        Checking what dependencies needs to ensure.
        """
        depends = extract(self.path, "depends")
        makedepends = extract(self.path, "makedepends")
        dependencies = (depends + " " + makedepends).strip()
        dependencies_to_ensure = []

        if dependencies == "":
            return

        for dependency in dependencies.split(" "):
            dependency = dependency.split(">")[0].split("<")[0]
            in_repository = self._is_dependency_in_repository(dependency)
            if not in_repository:
                dependencies_to_ensure.append(dependency)

        return dependencies_to_ensure

    def _is_dependency_in_repository(self, dependency):
        """
        Checking if the dependency is part of the official repository or
        if it exists in AUR.
        """
        try:
            output("pacman -Sp '" + dependency + "' &>/dev/null")
        except:
            if dependency in app.package:
                return True

            if output("git ls-remote https://aur.archlinux.org/%s.git" % dependency):
                return False
            else:
                self.error(f"""
                {dependency} is not part of the official package
                and can't be found in pkg directory.
                """)

        return True

    def _check_build_exists(self):
        """
        Checking if the PKGBUILD exists.
        """
        if not os.path.isfile(self.path + "/PKGBUILD"):
            self.error.append("PKGBUILD does not exists.")

    def _check_build_version(self):
        """
        Checking if the version is define in PKGBUILD.
        """
        if not self._version:
            self.error.append("No version variable is defined in PKGBUILD.")

    def _check_build_name(self):
        """
        Checking if the name is define in PKGBUILD.
        """
        if not self._name:
            self.error.append("No name variable is defined in PKGBUILD.")

    def _check_module_source(self):
        """
        Checking if the module source is define in package.
        """
        if not _attribute_exists(self.module, "source"):
            self.error.append("No source variable is defined in package.py")

    def _check_module_name(self):
        """
        Checking if the module name is define in package.
        """
        if _attribute_exists(self.module, "name") is False:
            self.error.append("No name variable is defined in package.py")

    def _prepare_checking_environment(self):
        """
        Preparing testing environment by creating temporary source.
        """
        temporary_source = os.path.join(app.path.tmp, self.name)
        execute(f"cp -rf {self.path} {temporary_source}")
        self.path = temporary_source

    def make(self):
        """
        Building the package with the command makepkg.
        """
        path = os.path.join(self.path, "tmp")
        errors = {
            1: "Unknown cause of failure.",
            2: "Error in configuration file.",
            3: "User specified an invalid option",
            4: "Error in user-supplied function in PKGBUILD.",
            5: "Failed to create a viable package.",
            6: "A source or auxiliary file specified in the PKGBUILD is missing.",
            7: "The PKGDIR is missing.",
            8: "Failed to install dependencies.",
            9: "Failed to remove dependencies.",
            10: "User attempted to run makepkg as root.",
            11: "User lacks permissions to build or install to a given location.",
            12: "Error parsing PKGBUILD.",
            13: "A package has already been built.",
            14: "The package failed to install.",
            15: "Programs necessary to run makepkg are missing.",
            16: "Specified GPG key does not exist."
        }

        exit_code = self._execute(f"""
        mkdir -p ./tmp;
        cp -r `ls | grep -v tmp` ./tmp;
        makepkg \
            SRCDEST=./tmp \
            --clean \
            --install \
            --nocheck \
            --nocolor \
            --noconfirm \
            --skipinteg \
            --syncdeps;
        """, True)

        self._delete_directory(path)

        if exit_code == 0:
            self._execute("mv *.pkg.tar.xz %s" % app.path.mirror)
        else:
            print(red(f"Build: {errors[exit_code]}"))

        return exit_code == 0

    def _execute(self, command, show_output=False):
        """
        Executing subprocess command. The second argument expect to recive
        true if you want to show subprocess output.
        """
        if show_output:
            return subprocess.call(
                command,
                shell=True,
                cwd=self.path
            )
        else:
            return subprocess.call(
                command,
                shell=True,
                cwd=self.path,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

    def _delete_directory(self, path):
        """
        Deleting the given directory.
        """
        self._execute(f"rm -rf {path}")
