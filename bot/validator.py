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
import functools

from utils.git import git_remote_path
from utils.terminal import output
from utils.validator import validate

def register(container):
    container.register("validator.requirements", requirements)
    container.register("validator.repository", repository)
    container.register("validator.content", content)
    container.register("validator.travis", travis)
    container.register("validator.connection", connection)
    container.register("validator.files", files)

def fluent(func):
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        self = args[0]
        func(*args, **kwargs)
        return self

    return wrapped

class Validator():
    @fluent
    def user_privileges(self):
        validate(
            error=_("exception.validator.root"),
            target=_("content.validator.root"),
            valid=os.getuid() != 0
        )

    @fluent
    def is_docker_image(self):
        validate(
            error=_("exception.validator.docker"),
            target=_("content.validator.docker"),
            valid=os.environ.get("IS_DOCKER", False)
        )

    @fluent
    def operating_system(self):
        validate(
            error=_("exception.validator.os"),
            target=_("content.validator.os"),
            valid=platform.dist()[0] == "arch"
        )

    @fluent
    def internet_up(self):
        try:
            socket.create_connection(("www.github.com", 80))
            connected = True
        except OSError:
            connected = False

        validate(
            error=_("exception.validator.internet"),
            target=_("content.validator.internet"),
            valid=connected
        )

    @fluent
    def deploy_key(self):
        validate(
            error=_("exception.validator.deploy_key"),
            target="deploy_key",
            valid=os.path.isfile(path("base") + "/deploy_key")
        )

    @fluent
    def deploy_key_encrypted(self):
        validate(
            error=_("exception.validator.deploy_key.enc"),
            target="deploy_key.enc",
            valid=os.path.isfile(path("base") + "/deploy_key.enc")
        )

    @fluent
    def ssh_connection(self):
        script = "ssh -i ./deploy_key -p %i -q %s@%s [[ -d %s ]] && echo 1 || echo 0" % (
            repo("ssh.port"),
            repo("ssh.user"),
            repo("ssh.host"),
            repo("ssh.path")
        )

        validate(
            error=_("exception.validator.ssh.connection"),
            target=_("content.validator.ssh.connection"),
            valid=output(script) is "1"
        )

    @fluent
    def mirror_connection(self):
        url = repo("url")
        token = secrets.token_hex(15)
        source = path("mirror") + "/validation_token"

        with open(source, "w") as f:
            f.write(token)
            f.close()

        os.system("rsync -aqvz -e 'ssh -i ./deploy_key -p %i' %s %s@%s:%s" % (
            repo("ssh.port"), source, repo("ssh.user"), repo("ssh.host"), repo("ssh.path")))

        try:
            response = requests.get(url + "/validation_token")
            valid = True if response.status_code == 200 else False
        except:
            valid = False

        validate(
            error=_("exception.validator.mirror.connection") % url,
            target=_("content.validator.mirror.connection"),
            valid=valid
        )

    @fluent
    def repository(self):
        valid = True

        for name in ["database", "git.email", "git.name", "ssh.host", "ssh.path", "ssh.port", "url"]:
            if not repo(name):
                valid = False
                break

        name = name.replace(".", " ")

        validate(
            error=_("exception.validator.repository") % name,
            target=_("content.validator.repository"),
            valid=valid
        )

    @fluent
    def port(self):
        validate(
            error=_("exception.validator.ssh.port"),
            target=_("content.validator.ssh.port"),
            valid=type(repo("ssh.port")) == int
        )

    @fluent
    def travis_github_token(self):
        if app("is_travis") is False:
            return

        valid = False
        user = git_remote_path().split("/")[1]
        response = output("curl -su %s:${GITHUB_TOKEN} https://api.github.com/user" % user)
        content = json.loads(response)

        if "login" in content:
            valid = True

        validate(
            error=_("exception.validator.travis.github.token"),
            target=_("content.validator.travis.github.token"),
            valid=valid
        )

    @fluent
    def travis_lint(self, content):
        validate(
            error=_("exception.validator.travis.lint"),
            target=_("content.validator.travis.lint"),
            valid=type(content) is dict
        )

    @fluent
    def travis_openssl(self, content):
        valid = False

        if "before_install" in content:
            for statement in content["before_install"]:
                if statement.startswith("openssl"):
                    valid = True

        validate(
            error=_("exception.validator.travis.openssl"),
            target=_("content.validator.travis.openssl"),
            valid=valid
        )

    @fluent
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
            error=_("exception.validator.travis.variable"),
            target=_("content.validator.travis.variable"),
            valid=valid
        )

    @fluent
    def pkg_directory(self):
        validate(
            error=_("exception.validator.pkg.directory"),
            target=_("content.validator.pkg.directory"),
            valid=len(app("packages")) > 0
        )

    @fluent
    def pkg_content(self):
        folders = [f.name for f in os.scandir(path("pkg")) if f.is_dir()]
        diff = set(folders) - set(app("packages"))

        validate(
            error=_("exception.validator.pkg.content") % (", ".join(diff)),
            target=_("content.validator.pkg.content"),
            valid=len(diff) == 0
        )


def requirements():
    print(_("content.validator.title.requirements"))

    (validator
        .user_privileges()
        .is_docker_image()
        .operating_system()
        .internet_up())

def files():
    print(_("content.validator.title.files"))

    (validator
        .deploy_key_encrypted()
        .deploy_key())

def repository():
    print(_("content.validator.title.repository"))

    (validator
       .repository()
       .port())

def connection():
    print(_("content.validator.title.connection"))

    (validator
        .ssh_connection()
        .mirror_connection()
        .travis_github_token())

def content():
    print(_("content.validator.title.packages"))

    (validator
        .pkg_directory()
        .pkg_content())

def travis():
    print(_("content.validator.title.travis"))

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
