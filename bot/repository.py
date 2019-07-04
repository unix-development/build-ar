#!/usr/bin/env python

"""
Copyright (c) Build Your Own Arch Linux Repository developers
See the file 'LICENSE' for copying permission
"""

import sys
import subprocess

from core.data import conf
from core.data import paths
from core.data import repository
from utils.editor import edit_file
from utils.editor import replace_ending
from utils.process import output
from utils.process import strict_execute
from utils.process import git_remote_path
from utils.process import extract
from utils.process import is_travis
from utils.process import is_testing
from utils.style import title
from utils.style import bold
from utils.validator import validate


packages_updated = []

def synchronize():
    sys.path.append(app.pkg)

    for name in app.packages:
        if self.verify_package(name):
            if app.is_travis: return

def test_package():
    sys.path.append(paths.pkg)
    verify_package(conf.testing.package, True)

def verify_package(name, is_dependency=False):
    package = Package(name, is_dependency)
    package.run()

    if package.updated:
        return True

def create_database():
    if len(packages_updated) == 0:
        return

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

    for package in packages_updated:
        strict_execute(f"""
        repo-add \
            --nocolor \
            --remove \
            {app.mirror}/{config.database}.db.tar.gz \
            {app.mirror}/{package}-*.pkg.tar.xz
        """)

def deploy():
    if len(packages_updated) == 0:
        return

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

    print(title(text("content.repository.deploy.git")) + "\n")

    try:
        subprocess.check_call("git push https://%s@%s HEAD:master &> /dev/null" % (
            config.github.token, git_remote_path()), shell=True)
    except:
        sys.exit("Error: Failed to push some refs to 'https://%s'" % git_remote_path())

def set_package_checked(name):
    with open(f"{paths.mirror}/packages_checked", "a+") as f:
        f.write(name + "\n")

