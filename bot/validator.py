#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
import re
import sys
import yaml
import json
import socket
import secrets
import platform
import requests

from core.container import return_self
from utils.process import output, git_remote_path
from utils.validator import validate


class Validator():
    @return_self
    def user_privileges(self):
        validate(
            error=text("exception.validator.root"),
            target=text("content.validator.root"),
            valid=os.getuid() != 0
        )

    @return_self
    def is_docker_image(self):
        validate(
            error=text("exception.validator.docker"),
            target=text("content.validator.docker"),
            valid=os.environ.get("IS_DOCKER", False)
        )

    @return_self
    def operating_system(self):
        validate(
            error=text("exception.validator.os"),
            target=text("content.validator.os"),
            valid=platform.dist()[0] == "arch"
        )

    @return_self
    def internet_up(self):
        try:
            socket.create_connection(("www.github.com", 80))
            connected = True
        except OSError:
            connected = False

        validate(
            error=text("exception.validator.internet"),
            target=text("content.validator.internet"),
            valid=connected
        )

    @return_self
    def deploy_key(self):
        validate(
            error=text("exception.validator.deploy_key"),
            target="deploy_key",
            valid=os.path.isfile(app.base + "/deploy_key")
        )

    @return_self
    def deploy_key_encrypted(self):
        validate(
            error=text("exception.validator.deploy_key.enc"),
            target="deploy_key.enc",
            valid=os.path.isfile(app.base + "/deploy_key.enc")
        )

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
    def repository(self):
        valid = True
        repository = {
            "url": config.url,
            "database": config.database,
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
    def travis_github_token(self):
        if app.is_travis is False:
            return

        valid = False
        user = git_remote_path().split("/")[1]
        response = output("curl -su %s:${GITHUB_TOKEN} https://api.github.com/user" % user)
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
    def travis_variable(self, content):
        valid = False
        environment = None

        if "env" in content and "global" in content["env"]:
            environment = content["env"]["global"]

        if environment is not None:
            if type(environment) is list:
                for variable in environment:
                    if "secure" in variable:
                        valid = True
                        break

            elif type(environment) is dict and "secure" in environment:
                valid = True

        validate(
            error=text("exception.validator.travis.variable"),
            target=text("content.validator.travis.variable"),
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
    container.register("validator.requirements", requirements)
    container.register("validator.repository", repository)
    container.register("validator.content", content)
    container.register("validator.travis", travis)
    container.register("validator.connection", connection)
    container.register("validator.files", files)

def requirements():
    print(text("content.validator.title.requirements"))

    (validator
        .user_privileges()
        .is_docker_image()
        .operating_system()
        .internet_up())

def files():
    print(text("content.validator.title.files"))

    (validator
        .deploy_key_encrypted()
        .deploy_key())

def repository():
    print(text("content.validator.title.repository"))

    (validator
       .repository()
       .database()
       .port())

def connection():
    print(text("content.validator.title.connection"))

    (validator
        .ssh_connection()
        .mirror_connection()
        .travis_github_token())

def content():
    print(text("content.validator.title.packages"))

    (validator
        .pkg_directory()
        .pkg_content()
        .pkg_testing())

def travis():
    print(text("content.validator.title.travis"))

    with open(".travis.yml", "r") as stream:
        try:
            content = yaml.load(stream)
        except yaml.YAMLError as error:
            content = error

    (validator
        .travis_lint(content)
        .travis_variable(content)
        .travis_openssl(content))


validator = Validator()
