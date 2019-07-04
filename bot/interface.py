#!/usr/bin/env python

"""
Copyright (c) Build Your Own Arch Linux Repository developers
See the file 'LICENSE' for copying permission
"""

import os
import base64

from datetime import datetime
from core.data import conf
from core.data import paths
from utils.editor import edit_file
from utils.process import git_remote_path
from utils.process import output
from utils.process import extract


class Interface():
    table = ""
    content = """
    <tr>
        <td><a href="$path">$name</a></td>
        <td>$version</td>
        <td>$date</td>
        <td>$description</td>
    </tr>
    """

    def create(self):
        conf.packages.sort()

        for package in conf.packages:
            module = paths.pkg + "/" + package

            try:
                open(module + "/PKGBUILD")
            except FileNotFoundError:
                continue

            schema = self.get_schema(module)
            date = self.get_last_change(module)
            version = schema["version"]
            description = schema["description"]

            for name in schema["name"].split(" "):
                build = self.get_package_file(name, schema)

                if build:
                    description = self.get_description(package, name, description)

                    self.table += (self.content
                        .replace("$path", build)
                        .replace("$name", name)
                        .replace("$date", date)
                        .replace("$version", version)
                        .replace("$description", description)
                    )

        self.move_to_mirror()
        self.replace_variables()
        self.compress()

    def get_last_change(self, path):
        last_change = output("git log -1 --format='%at' -- " + path)
        timestamp = datetime.fromtimestamp(int(last_change))
        return timestamp.strftime("%d %h %Y")

    def get_schema(self, path):
        if not os.path.isfile(path + "/PKGBUILD"):
            return

        epoch = extract(path, "epoch")

        if epoch:
            epoch += ":"

        return dict(
            description=extract(path, "pkgdesc"),
            version=extract(path, "pkgver"),
            name=extract(path, "pkgname"),
            epoch=epoch
        )

    def get_package_file(self, name, schema):
        path = name + "-" + schema["epoch"] + schema["version"] + "-"

        for location in os.listdir(paths.mirror):
            if location.startswith(path):
                return location

    def get_description(self, package, name, default):
        search = False
        description = default

        for line in open(f"{paths.pkg}/{package}/PKGBUILD"):
            line = line.strip()
            if line.startswith("package_" + name + "()"):
                search = True
            elif line.startswith("pkgdesc=") and search:
                description = line.replace("pkgdesc=", "")[1:-1]
                break

        return description

    def move_to_mirror(self):
        os.system(f"cp {paths.www}/index.html {paths.mirror}")

    def replace_variables(self):
        remote_path = 'https://' + git_remote_path().rstrip('.git')

        for line in edit_file(paths.mirror + "/index.html"):
            line = (line
                .replace("$content", self.table)
                .replace("$path", conf.url)
                .replace("$database", conf.db)
                .replace("$remote_path", remote_path)
                .replace("images/logo.png", "data:image/png;base64," + get_base64(paths.www + "/images/logo.png"))
                .replace("images/background.png", "data:image/png;base64," + get_base64(paths.www + "/images/background.png")))

            if line.strip() == "<link rel=\"stylesheet\" href=\"css/main.css\">":
                line = "<style type=\"text/css\">"
                line += get_compressed_file(paths.www + "/css/main.css")
                line += "</style>"

            print(line)

    def compress(self):
        content = get_compressed_file(paths.mirror + "/index.html")

        with open(paths.mirror + "/index.html", "w") as f:
            f.write(content)


def get_base64(path):
    with open(path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf8')

def get_compressed_file(path):
    with open(path) as f:
        return " ".join(f.read().split())


interface = Interface()
