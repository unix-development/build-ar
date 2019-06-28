#!/usr/bin/env python

"""
Copyright (c) Build Your Own Arch Linux Repository developers
See the file 'LICENSE' for copying permission
"""

from core.type import Attr


# Github upstream source
GITHUB_UPSTREAM = "https://github.com/unix-development/build-your-own-archlinux-repository"

# Bot version (<major>.<minor>.<month>.<monthly commit>)
# To get the monthly commit, you need to execute:
#
# >>> git rev-list --count HEAD --since="last month"
# 33
VERSION = "1.0.6.33"

# Contextual paths
paths = Attr()

# Config into repository.json
configs = None

# Packages in pkg directory
packages = []
