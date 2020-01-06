#!/usr/bin/env python

"""
Copyright (c) Build Your Own Arch Linux Repository developers
See the file 'LICENSE' for copying permission
"""

import os
import yaml
import json
import socket
import secrets
import platform
import requests

from core.settings import ALIAS_CONFIGS
from core.settings import IS_DEVELOPMENT
from core.settings import IS_TRAVIS
from core.settings import SSH_CONFIGS

from core.data import conf
from core.data import paths
from core.data import remote_repository
from core.type import get_attr_value
from utils.process import git_remote_path
from utils.process import has_git_changes
from utils.process import output
from utils.validator import validate


def _check_user_privileges():
    validate(
        error="This program needs to be not execute as root.",
        target="user privileges",
        valid=(os.getuid() != 0)
    )

def _check_is_docker_image():
    validate(
        error="This program needs to be executed in a docker image.",
        target="docker",
        valid=(os.environ.get("IS_DOCKER", False))
    )

def _check_internet_up():
    try:
        socket.create_connection(("www.github.com", 80))
        connected = True
    except OSError:
        connected = False

    validate(
        error="This program needs to be connected to internet.",
        target="internet",
        valid=connected
    )

def _check_deploy_key():
    valid = True
    target = "deploy_key"

    if IS_TRAVIS and os.path.isfile(os.path.join(paths.base, "deploy_key.enc")) is False:
        valid = False
        target = "deploy_key.enc"

    elif os.path.isfile(os.path.join(paths.base, "deploy_key")) is False:
        valid = False

    validate(
        error="%s could not been found." % target,
        target=target,
        valid=valid
    )

def _check_repository():
    valid = True
    target = "repository.yml"

    if IS_TRAVIS and os.path.isfile(os.path.join(paths.base, "repository.yml.enc")) is False:
        valid = False
        target = "repository.yml.enc"

    elif os.path.isfile(os.path.join(paths.base, "repository.yml")) is False:
        valid = False

    validate(
        error="%s could not been found." % target,
        target=target,
        valid=valid
    )

def _check_content():
    valid = True
    content = ALIAS_CONFIGS

    if not remote_repository():
        content = set(content) - set(SSH_CONFIGS)

    for name in content:
        if not get_attr_value(conf, name):
            valid = False
            break

    validate(
        error="%s must be defined in repository.yml" % name,
        target="content",
        valid=valid
    )

def _check_database():
    valid = True
    error_msg = ""

    if conf.db in ("core", "extra", "community"):
        valid = False
        error_msg = "Database must be different than core, community and extra."

    elif conf.db.isalnum() is False:
        valid = False
        error_msg = "Database must be an alphanumeric string."

    validate(
        error=error_msg,
        target="database",
        valid=valid
    )

def _check_port():
    validate(
        error="port must be an interger in repository.yml",
        target="port",
        valid=(type(conf.ssh_port) == int)
    )

def _check_travis_lint(content):
    error_msg = "An error occured while trying to parse your travis file.\nPlease make sure that the file is valid YAML.",

    validate(
        error=error_msg,
        target="lint",
        valid=(type(content) is dict)
    )

def _check_travis_openssl(content):
    valid = False
    error_msg = "No openssl statement could be found in your travis file.\nPlease make sure to execute: travis encrypt-file ./deploy_key --add"

    if "before_install" in content:
        for statement in content["before_install"]:
            if statement.startswith("openssl"):
                valid = True

    validate(
        error=error_msg,
        target="openssl",
        valid=valid
    )

def _check_pkg_directory():
    validate(
        error="No package was found in pkg directory.",
        target="directory",
        valid=(len(conf.packages) > 0)
    )

def _check_pkg_content():
    folders = [f.name for f in os.scandir(paths.pkg) if f.is_dir()]
    diff = set(folders) - set(conf.packages)

    validate(
        error="No package.py was found in pkg subdirectories: %s" % (", ".join(diff)),
        target="content",
        valid=(len(diff) == 0)
    )

def _check_ssh_connection():
    script = "ssh -i ./deploy_key -p %i -q %s@%s [[ -d %s ]] && echo 1 || echo 0" % (
        conf.ssh_port,
        conf.ssh_user,
        conf.ssh_host,
        conf.ssh_path
    )

    validate(
        error="ssh connection could not be established.",
        target="ssh address",
        valid=(output(script) == "1")
    )

def _check_mirror_connection():
    token = secrets.token_hex(15)
    source = os.path.join(paths.mirror, "validation_token")

    with open(source, "w") as f:
        f.write(token)
        f.close()

    os.system("rsync -aqvz -e 'ssh -i ./deploy_key -p %i' %s %s@%s:%s" % (
        conf.ssh_port, source, conf.ssh_user, conf.ssh_host, conf.ssh_path)
    )

    try:
        response = requests.get(conf.url + "/validation_token")
        valid = True if response.status_code == 200 else False
    except requests.RequestException:
        valid = False

    validate(
        error="This program can't connect to %s." % conf.url,
        target="mirror host",
        valid=valid
    )

def _check_github_token():
    valid = False
    user = git_remote_path().split("/")[1]
    response = output("curl -su %s:%s https://api.github.com/user" % (user, conf.github_token))
    content = json.loads(response)

    if "login" in content:
        valid = True

    validate(
        error="An error occured while trying to connect to your github repository with your encrypted token.\nPlease make sure that your token is working.",
        target="github token api",
        valid=valid
    )


class Validator():
    def requirements(self):
        print("Validating requirements:")

        _check_user_privileges()
        _check_is_docker_image()
        _check_internet_up()

    def files(self):
        print("Validating files:")

        _check_repository()

        if remote_repository():
            _check_deploy_key()

    def configs(self):
        print("Validating repository:")

        _check_content()
        _check_database()

        if remote_repository():
            _check_port()

    def connection(self):
        print("Validating connection:")

        if remote_repository():
            _check_ssh_connection()
            _check_mirror_connection()

        _check_github_token()

    def content(self):
        print("Validating packages:")

        _check_pkg_directory()
        _check_pkg_content()

    def travis(self):
        if IS_TRAVIS is False:
            return

        print("Validating travis:")

        with open(".travis.yml", "r") as stream:
            try:
                content = yaml.safe_load(stream)
            except yaml.YAMLError as error:
                content = error

        _check_travis_lint(content)
        _check_travis_openssl(content)


validator = Validator()
