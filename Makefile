# Copyright Marc-Antoine Loignon
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

BUILDER  := python build/builder.py
CONFIG   := $(BUILDER) config
DATABASE := $(shell $(CONFIG) database)
ID       := $(shell id -u)
PWD      := $(shell pwd)

# Git repository variables
GIT_EMAIL := $(shell $(CONFIG) git.email)
GIT_NAME  := $(shell $(CONFIG) git.name)

# SSH variables
SSH_USER := $(shell $(CONFIG) ssh.user)
SSH_HOST := $(shell $(CONFIG) ssh.host)
SSH_PATH := $(shell $(CONFIG) ssh.path)
SSH_PORT := $(shell $(CONFIG) ssh.port)
SSH_URL  := $(SSH_USER)@$(SSH_HOST)

build:
	$(BUILDER) create $(DATABASE)

prepare:
	chmod 600 deploy_key
	ssh-add deploy_key
	ssh-keyscan -t rsa -H $(SSH_HOST) >> ~/.ssh/known_hosts

docker:
	docker build \
		--build-arg USER_ID="$(ID)" \
		--tag=archlinux-repository \
		--file=./build/Dockerfile ./

run:
	docker run \
		--volume="$(PWD)":/home/builder/repository \
		archlinux-repository

provision-packages:
	yes | pacman -Syu
	yes | pacman -S python git

provision-user:
	mkdir -p /home/builder/repository
	useradd -u $(USER_ID) -s /bin/bash -d /home/builder -G wheel builder
	chmod -R 777 /home/builder
	chown -R builder /home/builder
	echo '%wheel ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers

git-push:
	git config user.email '$(GIT_EMAIL)'
	git config user.name '$(GIT_NAME)'
	$(BUILDER) deploy

ssh-push:
	ssh -i deploy_key $(SSH_URL) "rm -f $(SSH_PATH)/*"
	scp repository/* $(SSH_URL):$(SSH_PATH)

.PHONY: build prepare docker run provision-packages provision-user git-push ssh-push
