DOCKER_DEST = archlinux-repository
DOCKER_PACKAGES = python git

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

.PHONY: docker-build prepare-ssh packages build
