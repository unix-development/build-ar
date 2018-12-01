DOCKER_DEST = archlinux-repository
DOCKER_PACKAGES = python git base base-devel

docker-build:
	docker build -t $(DOCKER_DEST) .

.PHONY: docker-build
