# Docker configurations
DOCKER_DEST = archlinux-repository
DOCKER_PACKAGES = python git

# Git repository configurations
GIT_EMAIL = "developer@lognoz.org"
GIT_NAME = "Marc-Antoine Loignon"

# SSH Configurations
SSH_ADDRESS = lognozc@lognoz.org
SSH_PATH = /home/lognozc/mirror.lognoz.org

docker-build:
	docker build -t $(DOCKER_DEST) .

packages:
	yes | pacman -Syu
	yes | pacman -S $(DOCKER_PACKAGES)

user:
	groupadd -g 1000 builder
	useradd -r -u 1000 -g wheel builder
	echo "%wheel ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

run:
	docker run -v "$PWD":/repository/builder $(DOCKER_DEST)

build:
	python bootstrap.py

prepare-ssh:
	chmod 600 ./deploy_key
	ssh-add ./deploy_key

git-commit:
	git config user.email ${GIT_EMAIL}
	git config user.name ${GIT_NAME}
	python deploy.py

ssh-push:
	ssh -i ./deploy_key ${SSH_ADDRESS} "rm ${SSH_PATH}*"
	scp ./build-repository/* ${SSH_ADDRESS}:${SSH_PATH}

.PHONY: docker-build prepare-ssh packages build
