#!/usr/bin/env python

"""
Copyright (c) Build Your Own Arch Linux Repository developers
See the file 'LICENSE' for copying permission
"""


from core.app import app

from util.process import execute


class Environment():
    def prepare_ssh(self):
        execute(f"""
        eval $(ssh-agent);
        chmod 600 ./deploy_key;
        ssh-add ./deploy_key;
        mkdir -p ~/.ssh;
        chmod 0700 ~/.ssh;
        ssh-keyscan -t rsa -H {app.ssh.host} >> ~/.ssh/known_hosts;
        """)

        with open("/home/bot/.ssh/config", "w") as f:
            f.write(f"""
            LogLevel ERROR
            Host {app.ssh.host}
                HostName {app.ssh.host}
                User {app.ssh.user}
                Port {app.ssh.port}
                IdentityFile {app.path.base}/deploy_key
            """)
            f.close()


environment = Environment()
