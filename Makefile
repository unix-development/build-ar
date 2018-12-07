# Docker configurations
DOCKER_DEST = archlinux-repository
DOCKER_PACKAGES = python git

# Git repository configurations
GIT_EMAIL = "developer@lognoz.org"
GIT_NAME = "Marc-Antoine Loignon"

# SSH configurations
SSH_USER = lognozc
SSH_HOST = lognoz.org
SSH_PATH = /home/lognozc/mirror.lognoz.org

# Variables
PWD = $(shell pwd)
ID = $(shell id -u)

all: docker-build docker-run deploy-git deploy-ssh

build:
	python ./bootstrap.py

ssh:
	chmod 600 ./deploy_key
	ssh-add ./deploy_key
	ssh-keyscan -t rsa -H lognoz.org >> ~/.ssh/known_hosts

docker-build:
	docker build --build-arg USER_ID="$(ID)" -t "$(DOCKER_DEST)" .

docker-run:
	docker run -v "$(PWD)":/home/builder/repository $(DOCKER_DEST)

provision-packages:
	yes | pacman -Syu
	yes | pacman -S $(DOCKER_PACKAGES)

provision-user:
	mkdir -p /home/builder/repository
	useradd -u $(USER_ID) -s /bin/bash -d /home/builder -G wheel builder
	chmod -R 777 /home/builder
	chown -R builder /home/builder
	echo '%wheel ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers

deploy-git:
	git config user.email ${GIT_EMAIL}
	git config user.name ${GIT_NAME}
	python deploy.py

deploy-ssh:
	ssh -i ./deploy_key ${SSH_USER}@${SSH_HOST} "rm -f ${SSH_PATH}/*"
	scp ./build-repository/* ${SSH_USER}@${SSH_HOST}:${SSH_PATH}
