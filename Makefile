DOCKER_DEST = archlinux-repository
DOCKER_PACKAGES = python git

GIT_EMAIL = "developer@lognoz.org"
GIT_NAME = "Marc-Antoine Loignon"

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

.PHONY: docker-build prepare-ssh packages build
