PROGRAM = archlinux-repository-bot

ID = $(shell id -u)
PWD = $(shell pwd)
TRAVIS = $(shell printenv TRAVIS)

build:
	@python bot build

valid:
	@python bot validate

container:
	@docker build \
		--build-arg USER_ID=$(ID) \
		--build-arg TRAVIS=$(TRAVIS) \
		--tag=${PROGRAM} ./

run:
	@docker run \
		--volume="$(PWD)":/home/docker/build \
		${PROGRAM}

ssh:
	@docker run \
		--volume="$(PWD)":/home/docker/build \
		-it ${PROGRAM} bash

.PHONY: build valid container run ssh
