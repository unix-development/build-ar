#!/usr/bin/env python

"""
Copyright (c) Build Your Own Arch Linux Repository developers
See the file 'LICENSE' for copying permission
"""

class System():
    def write(self, name, parameter):
        if name == "need_update":
            path = self.module.need_update
            content = "\n".join(parameter)
        else:
            return

        with open(path, "w") as f:
            f.write(content)
            f.close()

    def get(self, name):
        if name == "need_update":
            path = self.module.need_update

        try:
            with open(path, "r") as f:
                content = f.read()

            return content.split("\n")
        except:
            return []


system = System()
