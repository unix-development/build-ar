#!/usr/bin/env python

"""
Copyright (c) Build Your Own Arch Linux Repository developers
See the file 'LICENSE' for copying permission
"""

import os
import sys
import shutil
import subprocess
import multiprocessing

from core.settings import UPSTREAM_REPOSITORY
from core.settings import IS_DEVELOPMENT
from core.settings import IS_TRAVIS

from imp import load_source
from core.data import conf
from core.data import paths
from core.data import update_disabled
from core.data import remote_repository
from utils.process import extract
from utils.process import git_remote_path
from utils.process import has_git_changes
from utils.process import output
from utils.process import strict_execute
from utils.style import title
from utils.style import bold


manager = multiprocessing.Manager()
outdated = manager.list()


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

    def create_database(self):
        os.chdir(paths.mirror)

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
            name = package["name"]
            version = package["version"]

            strict_execute(f"""
            repo-add \
                --nocolor \
                --remove \
                {paths.mirror}/{conf.db}.db.tar.gz \
                {paths.mirror}/{name}-{version}-*.pkg.tar.xz
            """)

    def deploy(self):
        if output("git branch -r --contains $(git log --pretty=format:'%h' -n 1) | sed s/^...//"):
            return

        if remote_repository() and len(conf.updated) > 0:
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

    def synchronize(self):
        sys.path.append(paths.pkg)

        print("Check packages status:")

        pool = multiprocessing.Pool()
        results = pool.imap_unordered(self._check_package_status, conf.packages)
        pool.close()

        for result in results:
            if result is True and IS_TRAVIS:
                pool.terminate()
                break

        pool.join()

        for name in outdated:
            self.build_package(name)

    def test_package(self):
        self.build_package(conf.package_to_test, True)

    def build_package(self, name, is_dependency=False):
        package = Package(name, is_dependency)
        package.build()

    def _check_package_status(self, name):
        package = Package(name)

        processes = [
            package.clean_directory,
            package.is_user_config_valid,
            package.pull_repository,
            package.pre_build,
            package.set_real_version,
            package.set_variables,
            package.is_build_valid
        ]

        for process in processes:
            process()

            if len(package.errors) > 0:
                package._print_errors()
                return

        if package.has_new_version():
            outdated.append(name)
            print(f"  [ - ] {package.name}")
            return True
        else:
            package.set_package_checked()
            print(f"  [ ✓ ] {package.name}")

    def _execute(self, commands):
        subprocess.run(
            commands,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True
        )


class Package():
    def __init__(self, name, is_dependency=False):
        self.errors = []

        self.name = name
        self.path = os.path.join(paths.pkg, name)
        self.module = load_source(name + ".package", os.path.join(self.path, "package.py"))
        self.is_dependency = is_dependency

    def build(self):
        if self.is_dependency:
            self.clean_directory()
            self.is_user_config_valid()
            self.pull_repository()
            self.pre_build()
            self.set_real_version()
            self.set_variables()
            self.is_build_valid()

        self.separator()
        self.set_variables()
        self.verify_dependencies()

        if self._make():
            self.clean_directory()
            self.pull_repository()
            self.pre_build()
            self.set_real_version()
            self._commit()
            self._set_package_updated()
            self.set_package_checked()

    def is_user_config_valid(self):
        self._check_module_source()
        self._check_module_name()

        if len(self.errors) > 0:
            return False
        else:
            return True

    def is_build_valid(self):
        self._check_build_exists()
        self._check_build_version()
        self._check_build_name()

        if len(self.errors) > 0:
            return False
        else:
            return True

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

    def has_new_version(self):
        if has_git_changes(self.path):
            return True

        for f in os.listdir(paths.mirror):
            if f.startswith(self.module.name + '-' + self._epoch + self._version + '-'):
                return False

        return True

    def set_variables(self):
        self._version = None
        self._name = None
        self._epoch = None

        if os.path.isfile(self.path + "/PKGBUILD"):
            self._version = extract(self.path, "pkgver")
            self._name = extract(self.path, "pkgname")
            self._epoch = extract(self.path, "epoch")

            if self._epoch:
                self._epoch += ":"

    def pre_build(self):
        if "pre_build" not in dir(self.module):
            return

        command = f"""
        import sys;

        sys.path.insert(0, "{paths.base}/bot");
        from utils.editor import edit_file;
        sys.path.insert(0, "{self.path}");

        import package;
        package.edit_file = edit_file;
        package.pre_build();
        """

        command = " ".join(command.replace("\n", "").split())
        exit_code = self._execute(f"python -c '{command}'", False)

        if exit_code > 0:
            self.errors.append("An error append when executing pre_build function into package.py")

    def pull_repository(self):
        self._execute(f"""
        git init --quiet;
        git remote add origin {self.module.source};
        git pull origin master;
        rm -rf .git;
        rm -f .gitignore;
        """)

    def set_package_checked(self):
        if conf.environment == "prod":
            with open(f"{paths.mirror}/packages_checked", "a+") as f:
                f.write(self.name + "\n")

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
            self.errors.append("An error append when executing makepkg")

    def verify_dependencies(self):
        redirect = False

        self.depends = extract(self.path, "depends")
        self.makedepends = extract(self.path, "makedepends")
        self._dependencies = (self.depends + " " + self.makedepends).strip()

        if self._dependencies == "":
            return

        for dependency in self._dependencies.split(" "):
            try:
                output("pacman -Sp '" + dependency + "' &>/dev/null")
                continue
            except:
                redirect = False

                if dependency not in conf.packages:
                    dependency = dependency.split(">")[0].split("<")[0]

                    if output("git ls-remote https://aur.archlinux.org/%s.git" % dependency):
                        redirect = True
                        self._add_to_pkg(dependency)
                    else:
                        sys.exit("\nError: %s is not part of the official package and can't be found in pkg directory." % dependency)

                if redirect or dependency not in conf.updated:
                    if (len(conf.updated) > 0 and IS_TRAVIS):
                        return

                    print("Install missing dependencies before to build it.")

                    redirect = True
                    repository.build_package(dependency, True)

        if redirect is True and IS_TRAVIS is False:
            self.separator()

    def _add_to_pkg(self, dependency):
        directory = os.path.join(paths.pkg, dependency)

        conf.packages.append(dependency)

        self._execute(f"mkdir -p ../{dependency};")

        with open(f"{directory}/package.py", "w") as f:
            f.write("%s\n%s\n\n%s\n%s" % (
                "#!/usr/bin/env python",
                "# -*- coding:utf-8 -*-",
                ("name = \"%s\"" % dependency),
                ("source = \"https://aur.archlinux.org/%s.git\"" % dependency)
            ))

    def _set_package_updated(self):
        for name in self._name.split(" "):
            conf.updated.append({
                "name": name,
                "version": self._epoch + self._version
            })

    def _commit(self):
        if conf.environment != "prod":
            return

        print(bold("Commit changes:"))

        if has_git_changes(self.path):
            self._execute(f"""
            git add {self.path};
            git commit -m "Bot: Add last update into {self.name} package ~ version {self._version}";
            """, True)
        else:
            self._execute(f"""
            git commit --allow-empty -m "Bot: Rebuild {self.name} package ~ version {self._version}";
            """, True)

    def _make(self):
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

        shutil.rmtree(path)

        if conf.environment == "prod" and exit_code == 0:
            self._execute("mv *.pkg.tar.xz %s" % paths.mirror)

        return exit_code == 0

    def separator(self):
        print(title(self.name))

    def _check_module_source(self):
        if not _attribute_exists(self.module, "source"):
            self.errors.append("No source variable is defined in package.py")

    def _check_module_name(self):
        if _attribute_exists(self.module, "name") is False:
            self.errors.append("No name variable is defined in package.py")

        elif self.name != self.module.name:
            self.errors.append("The name defined in package.py is the not the same in PKGBUILD.")

    def _check_build_exists(self):
        if not os.path.isfile(self.path + "/PKGBUILD"):
            self.errors.append("PKGBUILD does not exists.")

    def _check_build_version(self):
        if not self._version:
            self.errors.append("No version variable is defined in PKGBUILD.")

    def _check_build_name(self):
        if not self._name:
            self.errors.append("No name variable is defined in PKGBUILD.")

        elif self.name not in self._name.split(" "):
            self.errors.append("The name defined in package.py is the not the same in PKGBUILD.")

    def _print_errors(self):
        errors = "\n".join([str(error) for error in self.errors])
        print(f"  [ x ] {self.name}\n==> ERROR:\n" + errors + "\n")

    def _execute(self, process, show_output=False):
        if show_output:
            return subprocess.call(process, shell=True, cwd=self.path)
        else:
            return subprocess.call(process, shell=True, cwd=self.path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def _attribute_exists(module, name):
    try:
        getattr(module, name)
        return True
    except AttributeError:
        return False


repository = Repository()
