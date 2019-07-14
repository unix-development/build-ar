#!/usr/bin/env python

"""
Copyright (c) Build Your Own Arch Linux Repository developers
See the file 'LICENSE' for copying permission
"""

import os
import sys
import subprocess


from core.settings import UPSTREAM_REPOSITORY
from core.settings import IS_DEVELOPMENT
from core.settings import IS_TRAVIS

from imp import load_source
from core.data import conf
from core.data import paths
from core.data import update_disabled
from core.data import remote_repository
from utils.editor import edit_file
from utils.editor import replace_ending
from utils.process import extract
from utils.process import git_remote_path
from utils.process import has_git_changes
from utils.process import output
from utils.process import strict_execute
from utils.style import title
from utils.style import bold
from utils.validator import validate


class Repository():
    def pull_main_repository(self):
        if IS_DEVELOPMENT or update_disabled("bot"):
            return

        print("Updating repository bot:")

        try:
            output("git remote | grep upstream")
        except:
            self._execute(f"git remote add upstream {UPSTREAM_REPOSITORY}")

        self._execute(
            "git fetch upstream; "
            "git pull --no-ff --no-commit -X theirs upstream master; "
            "git reset HEAD README.md; "
            "git checkout -- README.md; "
            "git commit -m 'Core: Pull main repository project';"
        )

        print("  [ ✓ ] up to date")

    def synchronize(self):
        sys.path.append(paths.pkg)

        for name in conf.packages:
            if self.verify_package(name):
                if IS_TRAVIS:
                    return

    def test_package(self):
        sys.path.append(paths.pkg)
        self.verify_package(conf.package_to_test, True)

    def verify_package(self, name, is_dependency=False):
        package = Package(name, is_dependency)
        package.run()

        if conf.updated:
            return True

    def create_database(self):
        if len(conf.updated) == 0:
            return

        print(title("Create database") + "\n")

        strict_execute("""
        rm -f {path}/{database}.old;
        rm -f {path}/{database}.files;
        rm -f {path}/{database}.files.tar.gz;
        rm -f {path}/{database}.files.tar.gz.old;
        """.format(
            database=conf.db,
            path=paths.mirror
        ))

        for package in conf.updated:
            strict_execute(f"""
            repo-add \
                --nocolor \
                {paths.mirror}/{conf.db}.db.tar.gz \
                {paths.mirror}/{package}-*.pkg.tar.xz
            """)

    def deploy(self):
        if len(conf.updated) == 0:
            return

        if output("git show -s --format=%s") is not "Core: Pull main repository project":
            return

        if remote_repository():
            self._deploy_ssh()

        self._deploy_git()

    def _deploy_git(self):
        print(title("Deploy to git remote") + "\n")

        try:
            subprocess.check_call("git push https://%s@%s HEAD:master &> /dev/null" % (
                conf.github_token, git_remote_path()), shell=True)
        except:
            sys.exit("Error: Failed to push some refs to 'https://%s'" % git_remote_path())

    def _deploy_ssh(self):
        print(title("Deploy to host remote") + "\n")

        strict_execute(f"""
        rsync \
            --archive \
            --compress \
            --copy-links \
            --delete \
            --recursive \
            --update \
            --verbose \
            --progress -e 'ssh -i {paths.base}/deploy_key -p {conf.ssh_port}' \
            {paths.mirror}/ \
            {conf.ssh_user}@{conf.ssh_host}:{conf.ssh_path}
        """)

    def _execute(self, commands):
        subprocess.run(
            commands,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True
        )


class Package():
    updated = False

    def __init__(self, name, is_dependency):
        self._module = name + ".package"
        self._location = os.path.join(paths.pkg, name)
        self._is_dependency = is_dependency

        os.chdir(self._location)

        self.name = name
        self.module = load_source(self._module, os.path.join(self._location, "package.py"))

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

            if len(conf.updated) > 0 and IS_TRAVIS:
                return

            self._build()
            self._commit()
            self._set_package_updated()

        self._set_package_checked()

    def _set_package_updated(self):
        conf.updated.extend(self._name.split(" "))

    def _set_package_checked(self):
        if conf.environment is "prod":
            with open(f"{paths.mirror}/packages_checked", "a+") as f:
                f.write(self.name + "\n")

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
        rm -rf ./tmp;
        """)

        if conf.environment is "prod":
            strict_execute("mv *.pkg.tar.xz %s" % paths.mirror)

    def _commit(self):
        if conf.environment is not "prod":
            return

        print(bold("Commit changes:"))

        if has_git_changes("."):
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
                if dependency not in conf.packages:
                    sys.exit("\nError: %s is not part of the official package and can't be found in pkg directory." % dependency)

                if dependency not in conf.updated:
                    redirect = True
                    repository.verify_package(dependency, True)

        if redirect is True and IS_TRAVIS is False:
            self._separator()

        os.chdir(self._location)

    def _has_new_version(self):
        if has_git_changes("."):
            return True

        for f in os.listdir(paths.mirror):
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

        self._check_module_source()
        self._check_module_name()

    def _validate_build(self):
        print(bold("Validate PKGBUILD:"))

        self._check_build_exists()
        self._check_build_version()
        self._check_build_name()

    def _check_module_source(self):
        validate(
            error="No %s variable is defined in %s package.py" % ("source", self.name),
            target="source",
            valid=_attribute_exists(self.module, "source")
        )

    def _check_module_name(self):
        valid = True
        exception = ""

        if _attribute_exists(self.module, "name") is False:
            exception = "No %s variable is defined in %s package.py" % ("name", self.name)
            valid = False

        elif self.name != self.module.name:
            exception = "The name defined in package.py is the not the same in PKGBUILD."
            valid = False

        validate(
            error=exception,
            target="name",
            valid=valid
        )

    def _check_build_exists(self):
        validate(
            error="PKGBUILD does not exists.",
            target="is exists",
            valid=os.path.isfile("PKGBUILD")
        )

    def _check_build_version(self):
        validate(
            error="No version variable is defined in PKGBUILD.",
            target="version",
            valid=self._version
        )

    def _check_build_name(self):
        valid = True
        exception = ""

        if not self._name:
            exception = "No name variable is defined in PKGBUILD."
            valid = False

        elif self.name not in self._name.split(" "):
            exception = "The name defined in package.py is the not the same in PKGBUILD."
            valid = False

        validate(
            error=exception,
            target="name",
            valid=valid
        )

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


def _attribute_exists(module, name):
    try:
        getattr(module, name)
        return True
    except AttributeError:
        return False


repository = Repository()
