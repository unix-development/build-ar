#!/usr/bin/env python
# -*- coding:utf-8 -*-

name = "gotop"
source = "https://aur.archlinux.org/gotop-bin.git"

def pre_build():
    for line in edit_file("PKGBUILD"):
        if line.startswith("pkgname="):
            print("pkgname=gotop")
        else:
            print(line)
