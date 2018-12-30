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

PARAMETERS := database git.email git.name ssh.user ssh.host ssh.path ssh.port
PACKAGES   := python git
ID         := $(shell id -u)
PWD        := $(shell pwd)

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
	yes | pacman -S $(PACKAGES)

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
