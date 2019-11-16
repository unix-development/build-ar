#!/usr/bin/env python

"""
Copyright (c) Build Your Own Arch Linux Repository developers
See the file 'LICENSE' for copying permission
"""

import os
import base64

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
                path = self.get_package_file(name, schema)

                if path:
                    description = self.get_description(package, name, description)

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
            self.move_to_mirror()
            self.replace_html_variables()
            self.compress()

        # Creade README.md
        if update_disabled("readme"):
            return

        self.move_to_root()
        self.replace_markdown_variables()
        self.commit_readme()

    def get_last_change(self, path):
        last_change = output("git log -1 --format='%at' -- " + path)
        timestamp = datetime.fromtimestamp(int(last_change))
        return timestamp.strftime("%d %h %Y")

    def commit_readme(self):
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
        os.system(f"cp {paths.www}/template.html {paths.mirror}/index.html")

    def move_to_root(self):
        os.system(f"cp {paths.www}/template.md {paths.base}/README.md")

    def replace_markdown_variables(self):
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

    def replace_html_variables(self):
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

    def compress(self):
        content = get_compressed_file(paths.mirror + "/index.html")

        with open(paths.mirror + "/index.html", "w") as f:
            f.write(content)

    def _get_remote_path(self):
        remote_path = git_remote_path()
        host = remote_path[:remote_path.find("/") + 1]
        return remote_path.rstrip('.git').strip(host)


def get_base64(path):
    with open(path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf8')

def get_compressed_file(path):
    with open(path) as f:
        return " ".join(f.read().split())


interface = Interface()
