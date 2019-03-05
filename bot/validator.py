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

class validator():
    @fluent
    def user_privileges(self):
        validate(
            error="This program needs to be not execute as root.",
            target="user privileges",
            valid=os.getuid() != 0
        )

    @fluent
    def is_docker_image(self):
        validate(
            error="This program needs to be executed in a docker image.",
            target="docker",
            valid=os.environ.get("IS_DOCKER", False)
        )

    @fluent
    def operating_system(self):
        validate(
            error="This program needs to be executed in Arch Linux.",
            target="operating system",
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
            error="This program needs to be connected to internet.",
            target="internet",
            valid=connected
        )

    @fluent
    def deploy_key(self):
        validate(
            error="deploy_key could not been found.",
            target="deploy_key",
            valid=os.path.isfile(path("base") + "/deploy_key")
        )

    @fluent
    def deploy_key_encrypted(self):
        validate(
            error="deploy_key.enc could not been found.",
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
            error="ssh connection could not be established.",
            target="ssh address",
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
            error="This program can't connect to %s." % url,
            target="mirror host",
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
            error="%s must be defined in repository.json" % name,
            target="content",
            valid=valid
        )

    @fluent
    def port(self):
        validate(
            error="port must be an interger in repository.json",
            target="port",
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
            error="An error occured while trying to connect to your github repository with your encrypted token.\nPlease make sure that your token is working.",
            target="github token api",
            valid=valid
        )

    @fluent
    def travis_lint(self, content):
        validate(
            error="An error occured while trying to parse your travis file.\nPlease make sure that the file is valid YAML.",
            target="lint",
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
            error="No openssl statement could be found in your travis file.\nPlease make sure to execute: travis encrypt-file ./deploy_key --add",
            target="openssl",
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
            error="No encrypted environement variable could be found in your travis file.\nPlease make sure to execute: travis encrypt GITHUB_TOKEN=\"secretkey\" --add",
            target="github token",
            valid=valid
        )

    @fluent
    def pkg_directory(self):
        validate(
            error="No package was found in pkg directory.",
            target="directory",
            valid=len(app("packages")) > 0
        )

    @fluent
    def pkg_content(self):
        folders = [f.name for f in os.scandir(path("pkg")) if f.is_dir()]
        diff = set(folders) - set(app("packages"))

        validate(
            error="No package.py was found in pkg subdirectories: " + ", ".join(diff),
            target="content",
            valid=len(diff) == 0
        )


def requirements():
    print("Validating requirements:")

    (validator()
        .user_privileges()
        .is_docker_image()
        .operating_system()
        .internet_up())

def files():
    print("Validating files:")

    (validator()
        .deploy_key_encrypted()
        .deploy_key())

def repository():
   print("Validating repository:")

   (validator()
       .repository()
       .port())

def connection():
    print("Validating connection:")

    (validator()
        .ssh_connection()
        .mirror_connection()
        .travis_github_token())

def content():
    print("Validating packages:")

    (validator()
        .pkg_directory()
        .pkg_content())

def travis():
    print("Validating travis:")

    with open(".travis.yml", "r") as stream:
        try:
            content = yaml.load(stream)
        except yaml.YAMLError as error:
            content = error

    (validator()
        .travis_lint(content)
        .travis_variable(content)
        .travis_openssl(content))
