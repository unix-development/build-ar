#!/usr/bin/env python

"""
Copyright (c) Build Your Own Arch Linux Repository developers
See the file 'LICENSE' for copying permission
"""

import os
import sys
import yaml
import json
import socket
import secrets
import platform
import requests

from core.data import paths
from core.data import conf
from core.data import repository
from core.type import get_attr_value
from utils.process import git_remote_path
from utils.process import is_travis
from utils.process import output
from utils.validator import validate


def check_user_privileges():
    validate(
        error="This program needs to be not execute as root.",
        target="user privileges",
        valid=os.getuid() != 0
    )

def check_is_docker_image():
    validate(
        error="This program needs to be executed in a docker image.",
        target="docker",
        valid=os.environ.get("IS_DOCKER", False)
    )

def check_operating_system():
    validate(
        error="This program needs to be executed in Arch Linux.",
        target="operating system",
        valid=platform.dist()[0] == "arch"
    )

def check_internet_up():
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

def check_deploy_key():
    valid = True
    target = "deploy_key"

    if is_travis() and os.path.isfile(os.path.join(paths.base, "deploy_key.enc")) is False:
        valid = False
        target = "deploy_key.enc"

    elif os.path.isfile(os.path.join(paths.base, "deploy_key")) is False:
        valid = False

    validate(
        error="%s could not been found." % target,
        target=target,
        valid=valid
    )

def check_repository():
    valid = True
    target = "repository.json"

    if is_travis() and os.path.isfile(os.path.join(paths.base, "repository.json.enc")) is False:
        valid = False
        target = "repository.json.enc"

    elif os.path.isfile(os.path.join(paths.base, "repository.json")) is False:
        valid = False

    validate(
        error="%s could not been found." % target,
        target=target,
        valid=valid
    )

def check_content():
    configs = {}
    expected = [
        "url",
        "database",
        "github token",
        "ssh host",
        "ssh path",
        "ssh port"
    ]

    for name in expected:
        configs[name] = get_attr_value(conf.user, name)

    valid = True
    for name in configs:
        if not configs[name]:
            valid = False
            break

    validate(
        error="%s must be defined in repository.json" % name,
        target="content",
        valid=valid
    )

def check_database():
    validate(
        error="Database must be different than core, community and extra.",
        target="database",
        valid=conf.user.database not in ["core", "extra", "community"]
    )

def check_port():
    validate(
        error="port must be an interger in repository.json",
        target="port",
        valid=type(conf.user.ssh.port) == int
    )

def check_travis_lint(content):
    validate(
        error="An error occured while trying to parse your travis file.\nPlease make sure that the file is valid YAML.",
        target="lint",
        valid=type(content) is dict
    )

def check_travis_openssl(content):
    valid = False

    if "before_install" in content:
        for statement in content["before_install"]:
            if statement.startswith("openssl"):
                valid = True

    validate(
        error="No openssl statement could be found in your travis file.\nPlease make sure to execute: travis encrypt-file ./deploy_key --add",
        target="openssl",
        valid=valid
    )

def check_pkg_directory():
    validate(
        error="No package was found in pkg directory.",
        target="directory",
        valid=len(repository) > 0
    )

def check_pkg_content():
    folders = [f.name for f in os.scandir(paths.pkg) if f.is_dir()]
    diff = set(folders) - set(repository)

    validate(
        error="No package.py was found in pkg subdirectories: %s" % (", ".join(diff)),
        target="content",
        valid=len(diff) == 0
    )

def check_pkg_testing():
    if conf.testing.environment is not True:
        return

    valid = True
    error = ""

    if conf.testing.package is None:
        valid = False
        error = "You need to define which package you want to test with this command: make package test=discord"

    elif conf.testing.package not in repository:
        valid = False
        error = "%s is not in pkg directory." % conf.testing.package

    elif output("git status " + paths.pkg + "/" + conf.testing.package + " --porcelain | sed s/^...//"):
        valid = False
        error = "You need to commit your changes before to test your package."

    validate(
        error=error,
        target="testing",
        valid=valid
    )

def check_ssh_connection():
    script = "ssh -i ./deploy_key -p %i -q %s@%s [[ -d %s ]] && echo 1 || echo 0" % (
        conf.user.ssh.port,
        conf.user.ssh.user,
        conf.user.ssh.host,
        conf.user.ssh.path
    )

    validate(
        error="ssh connection could not be established.",
        target="ssh address",
        valid=output(script) is "1"
    )

def check_mirror_connection():
    ssh = conf.user.ssh
    token = secrets.token_hex(15)
    source = os.path.join(paths.mirror, "validation_token")

    with open(source, "w") as f:
        f.write(token)
        f.close()

    os.system("rsync -aqvz -e 'ssh -i ./deploy_key -p %i' %s %s@%s:%s" % (
        ssh.port, source, ssh.user, ssh.host, ssh.path)
    )

    try:
        response = requests.get(conf.user.url + "/validation_token")
        valid = True if response.status_code == 200 else False
    except:
        valid = False

    validate(
        error="This program can't connect to %s." % conf.user.url,
        target="mirror host",
        valid=valid
    )

def check_github_token():
    valid = False
    user = git_remote_path().split("/")[1]
    response = output("curl -su %s:%s https://api.github.com/user" % (user, conf.user.github.token))
    content = json.loads(response)

    if "login" in content:
        valid = True

    validate(
        error="An error occured while trying to connect to your github repository with your encrypted token.\nPlease make sure that your token is working.",
        target="github token api",
        valid=valid
    )

def register():
    return {
        "validator.requirements": requirements,
        "validator.files": files,
        "validator.configs": configs,
        "validator.travis": travis,
        "validator.content": content,
        "validator.connection": connection
    }

def requirements():
    print("Validating requirements:")

    check_user_privileges()
    check_is_docker_image()
    check_operating_system()
    check_internet_up()

def files():
    print("Validating files:")

    check_repository()
    check_deploy_key()

def configs():
    print("Validating repository:")

    check_content()
    check_database()
    check_port()

def connection():
    print("Validating connection:")

    check_ssh_connection()
    check_mirror_connection()
    check_github_token()

def content():
    print("Validating packages:")

    check_pkg_directory()
    check_pkg_content()
    check_pkg_testing()

def travis():
    if is_travis() is False:
        return

    print("Validating travis:")

    with open(".travis.yml", "r") as stream:
        try:
            content = yaml.load(stream)
        except yaml.YAMLError as error:
            content = error

    check_travis_lint(content)
    check_travis_openssl(content)
