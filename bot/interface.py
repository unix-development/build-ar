#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
import time

from utils.git import git_remote_path
from utils.editor import edit_file, extract
from utils.interface import get_compressed_file, get_base64

def register(container):
    container.register("interface.build", build)

def build():
    path_mirror = path("mirror")
    path_pkg = path("pkg")

    table = ""
    content = (
        "<tr>"
            "<td><a href=\"$path\">$name</a></td>"
            "<td>$version</td>"
            "<td>$date</td>"
            "<td>$description</td>"
        "</tr>"
    )

    for package in app("packages"):
        module = path_pkg + "/" + package

        try:
            open(module + "/PKGBUILD")
        except FileNotFoundError:
            continue

        description = extract(module, "pkgdesc")
        version = extract(module, "pkgver")
        name = extract(module, "pkgname")

        for location in os.listdir(path_mirror):
            if location.startswith(package + "-" + version + "-"):
                date = time.strftime("%d %h %Y",
                    time.gmtime(os.path.getmtime(path_mirror + "/" + location)))

                table += (content
                    .replace("$path", location)
                    .replace("$name", package)
                    .replace("$date", date)
                    .replace("$version", version)
                    .replace("$description", description))

    move_to_mirror()
    replace_variables(table)
    compress()


def move_to_mirror():
    os.system("cp " + path("www") + "/index.html " + path("mirror"))

def replace_variables(table):
    remote_path = 'https://' + git_remote_path().rstrip('.git')

    for line in edit_file(path("mirror") + "/index.html"):
        line = (line
            .replace("$content", table)
            .replace("$path", repo("url"))
            .replace("$database", repo("database"))
            .replace("$remote_path", remote_path)
            .replace("images/logo.png", "data:image/png;base64," + get_base64(path("www") + "/images/logo.png")))

        if line.strip() == "<link rel=\"stylesheet\" href=\"css/main.css\">":
            line = "<style type=\"text/css\">"
            line += get_compressed_file(path("www") + "/css/main.css")
            line += "</style>"

        print(line)

def compress():
    content = get_compressed_file(path("mirror") + "/index.html")

    with open(path("mirror") + "/index.html", "w") as f:
        f.write(content)
