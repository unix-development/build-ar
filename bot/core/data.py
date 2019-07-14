#!/usr/bin/env python

"""
Copyright (c) Build Your Own Arch Linux Repository developers
See the file 'LICENSE' for copying permission
"""

from core.settings import SSH_CONFIGS
from core.type import Attr


# Contextual paths
paths = Attr()

# Configs, user preferences, data, etc.
conf = Attr()


# Return true if no update is allowed
def update_disabled(name):
    return not isinstance(conf.auto_update, list) or name not in conf.auto_update

# Return true if it's a remote repository
def remote_repository():
    for key in SSH_CONFIGS:
        if getattr(conf, key) is not None:
            return True
