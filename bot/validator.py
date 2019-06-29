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

from core.container import return_self
from core.container import container
from core.data import paths
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

class Validator():

    @return_self
    def ssh_connection(self):
        script = "ssh -i ./deploy_key -p %i -q %s@%s [[ -d %s ]] && echo 1 || echo 0" % (
            config.ssh.port,
            config.ssh.user,
            config.ssh.host,
            config.ssh.path
        )

        validate(
            error=text("exception.validator.ssh.connection"),
            target=text("content.validator.ssh.connection"),
            valid=output(script) is "1"
        )

    @return_self
    def mirror_connection(self):
        ssh = config.ssh
        token = secrets.token_hex(15)
        source = f"{app.mirror}/validation_token"

        with open(source, "w") as f:
            f.write(token)
            f.close()

        os.system("rsync -aqvz -e 'ssh -i ./deploy_key -p %i' %s %s@%s:%s" % (
            ssh.port, source, ssh.user, ssh.host, ssh.path)
        )

        try:
            response = requests.get(config.url + "/validation_token")
            valid = True if response.status_code == 200 else False
        except:
            valid = False

        validate(
            error=text("exception.validator.mirror.connection") % config.url,
            target=text("content.validator.mirror.connection"),
            valid=valid
        )

    @return_self
    def content(self):
        valid = True
        repository = {
            "url": config.url,
            "database": config.database,
            "github token": config.github.token,
            "ssh host": config.ssh.host,
            "ssh path": config.ssh.path,
            "ssh port": config.ssh.port
        }

        for name in repository:
            if not repository[name]:
                valid = False
                break

        validate(
            error=text("exception.validator.repository") % name,
            target=text("content.validator.repository"),
            valid=valid
        )

    @return_self
    def database(self):
        validate(
            error=text("exception.validator.database"),
            target=text("content.validator.database"),
            valid=config.database not in [ "core", "extra", "community" ]
        )

    @return_self
    def port(self):
        validate(
            error=text("exception.validator.ssh.port"),
            target=text("content.validator.ssh.port"),
            valid=type(config.ssh.port) == int
        )

    @return_self
    def github_token(self):
        valid = False
        user = git_remote_path().split("/")[1]
        response = output(f"curl -su {user}:{config.github.token} https://api.github.com/user")
        content = json.loads(response)

        if "login" in content:
            valid = True

        validate(
            error=text("exception.validator.travis.github.token"),
            target=text("content.validator.travis.github.token"),
            valid=valid
        )

    @return_self
    def travis_lint(self, content):
        validate(
            error=text("exception.validator.travis.lint"),
            target=text("content.validator.travis.lint"),
            valid=type(content) is dict
        )

    @return_self
    def travis_openssl(self, content):
        valid = False

        if "before_install" in content:
            for statement in content["before_install"]:
                if statement.startswith("openssl"):
                    valid = True

        validate(
            error=text("exception.validator.travis.openssl"),
            target=text("content.validator.travis.openssl"),
            valid=valid
        )

    @return_self
    def pkg_directory(self):
        validate(
            error=text("exception.validator.pkg.directory"),
            target=text("content.validator.pkg.directory"),
            valid=len(app.packages) > 0
        )

    @return_self
    def pkg_content(self):
        folders = [f.name for f in os.scandir(app.pkg) if f.is_dir()]
        diff = set(folders) - set(app.packages)

        validate(
            error=text("exception.validator.pkg.content") % (", ".join(diff)),
            target=text("content.validator.pkg.content"),
            valid=len(diff) == 0
        )

    @return_self
    def pkg_testing(self):
        if app.testing.environment is not True:
            return

        valid = True
        error = ""

        if app.testing.package is None:
            valid = False
            error = text("exception.validator.pkg.testing.argument")

        elif app.testing.package not in app.packages:
            valid = False
            error = text("exception.validator.pkg.testing.package") % app.testing.package

        validate(
            error=error,
            target=text("content.validator.pkg.testing"),
            valid=valid
        )


def register():
    return {
        "validator.requirements": requirements,
        "validator.files": files,
        "validator.repository": repository,
        "validator.content": content,
        "validator.travis": travis,
        "validator.connection": connection,
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

#def repository():
#    print("Validating repository:")
#
#    (validator
#       .content()
#       .database()
#       .port())
#
#def connection():
#    print("Validating connection:")
#
#    (validator
#        .ssh_connection()
#        .mirror_connection()
#        .github_token())
#
#def content():
#    print("Validating packages:")
#
#    (validator
#        .pkg_directory()
#        .pkg_content()
#        .pkg_testing())
#
#def travis():
#    if is_travis() is False:
#        return
#
#    print("Validating travis:")
#
#    with open(".travis.yml", "r") as stream:
#        try:
#            content = yaml.load(stream)
#        except yaml.YAMLError as error:
#            content = error
#
#    (validator
#        .travis_lint(content)
#        .travis_openssl(content))


validator = Validator()
