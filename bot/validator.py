#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
import re
import sys
import yaml
import socket
import secrets
import platform
import requests

from utils.terminal import output
from utils.validator import validate
from utils.constructor import constructor, fluent

class validator(constructor):
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
            valid=os.path.isfile(self.path_base + "/deploy_key")
        )

    @fluent
    def deploy_key_encrypted(self):
        validate(
            error="deploy_key.enc could not been found.",
            target="deploy_key.enc",
            valid=os.path.isfile(self.path_base + "/deploy_key.enc")
        )

    @fluent
    def ssh_connection(self):
        script = "ssh -i ./deploy_key -p %i -q %s@%s [[ -d %s ]] && echo 1 || echo 0" % (
            self.config("ssh.port"),
            self.config("ssh.user"),
            self.config("ssh.host"),
            self.config("ssh.path")
        )

        validate(
            error="ssh connection could not be established.",
            target="ssh address",
            valid=output(script) is "1"
        )

    @fluent
    def mirror_connection(self):
        for name in ["port", "user", "host", "path"]:
            globals()[name] = self.config("ssh." + name)

        url = self.config("url")
        token = secrets.token_hex(15)
        source = self.path_mirror + "/validation_token"

        with open(source, "w") as f:
            f.write(token)
            f.close()

        os.system(
            "rsync -aqvz -e 'ssh -i ./deploy_key -p %i' %s %s@%s:%s" %
            (port, source, user, host, path))

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
            if not self.config(name):
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
            valid=type(self.config("ssh.port")) == int
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
            valid=len(self.packages) > 0
        )

    @fluent
    def pkg_content(self):
        folders = [f.name for f in os.scandir(self.path_pkg) if f.is_dir()]
        diff = set(folders) - set(self.packages)

        validate(
            error="No package.py was found in pkg subdirectories: " + ", ".join(diff),
            target="content",
            valid=len(diff) == 0
        )


class new(constructor):
    def construct(self):
        self.validator = validator(
            config=self.config,
            packages=self.packages,
            path_pkg=self.path_pkg,
            path_base=self.path_base,
            path_mirror=self.path_mirror
        )

    def requirements(self):
        print("Validating requirements:")

        (self.validator
            .user_privileges()
            .is_docker_image()
            .operating_system()
            .internet_up())

    def travis(self):
        print("Validating travis:")

        with open(".travis.yml", "r") as stream:
            try:
                content = yaml.load(stream)
            except yaml.YAMLError as error:
                content = error

        (self.validator
            .travis_lint(content)
            .travis_variable(content)
            .travis_openssl(content))

    def files(self):
        print("Validating files:")

        (self.validator
            .deploy_key_encrypted()
            .deploy_key())

    def repository(self):
        print("Validating repository:")

        (self.validator
            .repository()
            .port())

    def connection(self):
        print("Validating connection:")

        (self.validator
            .ssh_connection()
            .mirror_connection())

    def container(self):
        print("Validating packages:")

        (self.validator
            .pkg_directory()
            .pkg_content())
