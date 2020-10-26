#!/usr/bin/env python

"""
Copyright (c) Build Your Own Arch Linux Repository developers
See the file 'LICENSE' for copying permission
"""

import re
import os
import sys
import base64

from core.app import app
from datetime import datetime
from util.process import output
from util.editor import edit_file
from util.process import git_remote_path


class Interface():
    """
    Main interface class used to create mirror page.
    """
    repository_content = {}

    def create(self):
        """
        Creating html mirror page and the readme file.
        """
        if not (packages := self._packages_in_database()): return

        for package in packages:
            self.repository_content[package] = self._parse_package_content(package)

        # Generate web page for mirror.
        self._move_to_mirror()
        self._replace_variables("web")
        self._compress_index()

        # Generate README.md file.
        self._move_to_root()
        self._replace_variables("readme")


    def _compress_index(self):
        """
        Compressing html mirror page.
        """
        with open(app.path.mirror + "/index.html") as f:
            content = f.read()

        with open(app.path.mirror + "/index.html", "w") as f:
            f.write(" ".join(content.split()))

    def _parse_package_content(self, package):
        """
        Parsing package informations.
        """
        content = {}
        detail = output(f"pacman -Si {package}").split("\n")

        for line in detail:
            statement = line.split(":")
            variable = statement[0].strip().lower()
            value = ":".join(statement[1:]).strip()

            if variable == "build date":
                date = datetime.strptime(value, "%a %d %b %Y %I:%M:%S %p UTC")
                timestamp = datetime.timestamp(date)
                content["date"] = date.strftime("%d %B %Y")
                content["timestamp"] = str(timestamp)

            if variable == "version":
                version = re.sub("[^0-9.]", "", value)
                version = '{0:.3}'.format(version)
                content["version"] = value
                content["version-simplify"] = version

            else:
                content[variable] = value

        content["path"] = self._get_file_location(content)

        return content

    def _get_file_location(self, content):
        path = content["name"] + "-" + content["version"]

        for location in os.listdir(app.path.mirror):
            if location.startswith(path):
                return location

        return ""

    def _packages_in_database(self):
        """
        Scanning packages defined in repository.
        """
        packages = output(f"pacman -Slq {app.database} | sort")
        if not packages.startswith("error: repository"):
            return packages.split("\n")

    def _move_to_root(self):
        """
        Moving markdown template to root directory.
        """
        os.system(f"cp {app.path.www}/template.md {app.path.base}/_readme.md")

    def _move_to_mirror(self):
        """
        Moving html template to mirror directory.
        """
        os.system(f"cp {app.path.www}/template.html {app.path.mirror}/index.html")

    def _get_content(self, path):
        """
        Getting html template by path.
        """
        with open(app.path.www + path) as f:
            return f.read()

    def _get_fetched_package(self, type_template):
        """
        Getting html packages for table.
        """
        content = ""

        if type_template == "web":
            tr_template = self._get_content("/include/tr.html")
        else:
            tr_template = self._get_content("/include/tr.md")

        for package in self.repository_content:
            parameters = self.repository_content[package]

            tr = tr_template
            tr = tr.replace("$name", package)
            tr = tr.replace("$date", parameters["date"])
            tr = tr.replace("$timestamp", parameters["timestamp"])
            tr = tr.replace("$url", parameters["url"])
            tr = tr.replace("$version-simplify", parameters["version-simplify"])
            tr = tr.replace("$version", parameters["version"])
            tr = tr.replace("$description", parameters["description"])
            tr = tr.replace("$path", parameters["path"])

            content += tr

        return content

    def _replace_variables(self, type_template):
        """
        Replacing variables in template.
        """
        remote_path = git_remote_path().rstrip(".git")
        content = self._get_fetched_package(type_template)
        logo = "data:image/png;base64," + self._get_base64("/images/logo.png")
        background = "data:image/png;base64," + self._get_base64("/images/background.png")

        if type_template == "readme":
            path = app.path.base + "/_readme.md"
            host = remote_path[:remote_path.find("/") + 1]
            remote_path = remote_path.replace(host, "")
        else:
            remote_path = "https://" + remote_path
            path = app.path.mirror + "/index.html"

        for line in edit_file(path):
            line = line.replace("$path", app.website)
            line = line.replace("$database_capitalize", app.database.capitalize())
            line = line.replace("$database", app.database)
            line = line.replace("$remote_path", remote_path)
            line = line.replace("$content", content)
            line = line.replace("images/logo.png", logo)
            line = line.replace("images/background.png", background)

            if line.strip() == "<link rel=\"stylesheet\" href=\"dist/main.css\">":
                line = "<style type=\"text/css\">"
                line += self._get_content("/dist/main.css")
                line += "</style>"

            if line.strip() == "<script src=\"dist/main.js\"></script>":
                line = "<script>"
                line += self._get_content("/dist/main.js")
                line += "</script>"

            print(line)

    def _get_base64(self, path):
        """
        Getting base64 content image.
        """
        with open(app.path.www + path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf8')


interface = Interface()
