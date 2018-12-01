DOCKER_DEST = archlinux-repository

docker-build:
	docker build -t $(DOCKER_DEST) .

.PHONY: docker-build
