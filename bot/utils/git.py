#!/usr/bin/env python
# -*- coding:utf-8 -*-

from utils.terminal import output

def git_remote_path():
    return output('git remote get-url origin') \
        .replace('https://', '') \
        .replace('http://', '') \
        .replace('git://', '')
