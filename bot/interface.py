#!/usr/bin/env python

"""
Copyright (c) Build Your Own Arch Linux Repository developers
See the file 'LICENSE' for copying permission
"""

import os
import sys
import base64
import subprocess

from core.settings import IS_DEVELOPMENT
from core.settings import IS_TRAVIS

from datetime import datetime
from core.data import conf
from core.data import paths
from core.data import update_disabled
from core.data import remote_repository
from utils.style import title
from utils.editor import edit_file
from utils.process import extract
from utils.process import git_remote_path
from utils.process import has_git_changes
from utils.process import output
from utils.process import strict_execute
from utils.process import execute_quietly


class Interface():
    html_table_tbody = ""
    html_table_tr = """
    <tr>
        <td><a href="$path">$name</a></td>
        <td>$version</td>
        <td>$date</td>
        <td>$description</td>
    </tr>
    """

    markdown_table_tbody = ""
    markdown_table_tr = "*$name*<br>$description | $version | $date\n"

    def create(self):
        if IS_DEVELOPMENT:
            return

        packages = output("pacman -Slq %s | sort" % conf.db)

        if packages.startswith("error: repository"):
            return
        else:
            packages = packages.split("\n")

        for name in packages:
            schema = self._get_schema(name)
            description = schema["description"]
            version = schema["version"]
            date = schema["date"]
            path = self._get_file_location(name, version)

            for prefix in ["html", "markdown"]:
                tr = getattr(self, prefix + "_table_tr")
                tr = tr.replace("$path", path)
                tr = tr.replace("$name", name)
                tr = tr.replace("$date", date)
                tr = tr.replace("$version", version)

                if prefix == "markdown":
                    description = description.replace("\\", "\\\\")
                    description = description.replace("*", "\*")
                    description = description.replace("_", "\_")
                    description = description.replace("|", "\|")

                tr = tr.replace("$description", description)

                tbody = getattr(self, prefix + "_table_tbody")
                setattr(self, prefix + "_table_tbody", tbody + tr)

        # Create html mirror
        if remote_repository():
            self._move_to_mirror()
            self._replace_html_variables()
            self._compress()

        # Creade README.md
        if update_disabled("readme"):
            return

        self._move_to_root()
        self._replace_markdown_variables()
        self._commit_readme()

    def _commit_readme(self):
        path = paths.base + "/README.md"
        packages = []

        if (has_git_changes(path) is False or len(conf.updated) == 0):
            return

        print(title("Build README.md and mirror page:") + "\n")

        for package in conf.updated:
            packages.append(package["name"])

        commit_msg = "Doc: Bump " + ", ".join(packages) + " in packages information table"
        strict_execute(f"""
        git add {path};
        git commit -m "{commit_msg}";
        """)

    def _get_schema(self, name):
        schema = {}
        is_package = False
        lines = output("pacman -Si %s" % name).split("\n")
        keys = {
            "repository": "Repository",
            "description": "Description",
            "version": "Version",
            "date": "Build Date",
        }

        for line in lines:
            if is_package is False:
                if line.startswith(keys["repository"]) and  self._strip_key(line) == conf.db:
                    is_package = True
            else:
                for key in keys:
                    if line.startswith(keys[key]):
                        schema[key] = self._strip_key(line)

                        if key == "date":
                            parameters = schema[key].split(" ")
                            schema[key] = parameters[1] + " " + parameters[2] + " " + parameters[3]

                if line == "":
                    is_package = False

        return schema

    def _strip_key(self, value):
        return ":".join(value.split(":")[1:]).strip()

    def _get_file_location(self, name, version):
        path = name + "-" + version

        for location in os.listdir(paths.mirror):
            if location.startswith(path):
                return location

        return ""

    def _move_to_mirror(self):
        os.system(f"cp {paths.www}/template.html {paths.mirror}/index.html")

    def _move_to_root(self):
        os.system(f"cp {paths.www}/template.md {paths.base}/README.md")

    def _replace_markdown_variables(self):
        remote_path = self._get_remote_path()

        if not remote_repository():
            conf.url = "file:///path/to/repository"

        for line in edit_file(paths.base + "/README.md"):
            line = line.replace("$remote_path", remote_path)
            line = line.replace("$content", self.markdown_table_tbody)
            line = line.replace("$database_capitalize", conf.db.capitalize())
            line = line.replace("$database", conf.db)

            if not IS_TRAVIS and line.startswith("[<img src=\"https://img.shields.io/travis/"):
                line = ""

            line = line.replace("$path", conf.url)

            print(line)

    def _replace_html_variables(self):
        remote_path = 'https://' + git_remote_path().rstrip('.git')

        for line in edit_file(paths.mirror + "/index.html"):
            line = line.replace("$content", self.html_table_tbody)
            line = line.replace("$path", conf.url)
            line = line.replace("$database", conf.db)
            line = line.replace("$remote_path", remote_path)
            line = line.replace("images/logo.png", "data:image/png;base64," + get_base64(paths.www + "/images/logo.png"))
            line = line.replace("images/background.png", "data:image/png;base64," + get_base64(paths.www + "/images/background.png"))

            if line.strip() == "<link rel=\"stylesheet\" href=\"css/main.css\">":
                line = "<style type=\"text/css\">"
                line += get_compressed_file(paths.www + "/css/main.css")
                line += "</style>"

            print(line)

    def _compress(self):
        content = get_compressed_file(paths.mirror + "/index.html")

        with open(paths.mirror + "/index.html", "w") as f:
            f.write(content)

    def _get_remote_path(self):
        remote_path = git_remote_path()
        host = remote_path[:remote_path.find("/") + 1]
        return remote_path.rstrip('.git').strip(host)

    def _execute(self, commands):
        subprocess.run(
            commands,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True
        )


def get_base64(path):
    with open(path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf8')

def get_compressed_file(path):
    with open(path) as f:
        return " ".join(f.read().split())


interface = Interface()
