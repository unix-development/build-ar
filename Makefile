DOCKER_DEST = archlinux-repository
DOCKER_PACKAGES = python git base base-devel

docker-build:
	docker build -t $(DOCKER_DEST) .

pacman-install:
	yes | pacman -Syu
	yes | pacman -S $(DOCKER_PACKAGES)

.PHONY: docker-build
