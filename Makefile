DOCKER_DEST = archlinux-repository
DOCKER_PACKAGES = python git

docker-build:
	docker build -t $(DOCKER_DEST) .

build:
	yes | pacman -Syu
	yes | pacman -S $(DOCKER_PACKAGES)
	echo "%wheel ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

bootstrap:
	python bootstrap.py

prepare-ssh:
	eval "$(ssh-agent -s)"
	chmod 600 ./deploy_key
	ssh-add ./deploy_key

.PHONY: docker-build prepare-ssh build bootstrap
