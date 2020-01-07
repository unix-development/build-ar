# Use bash syntax
SHELL := /bin/bash

.PHONY: all
all: container run

.PHONY: test-docker
test-docker:
	@if [[ "$(shell docker images -q build-your-own-archlinux-repository)" = "" ]]; then \
		echo "Before to use Docker container, you must install it. Please execute the command 'make container'."; \
		exit 1; \
	fi

.PHONY: container
container:
	@docker build --pull \
		--build-arg USER_ID=$(shell id -u) \
		--build-arg TRAVIS=$(TRAVIS) \
		--tag=build-your-own-archlinux-repository ./

.PHONY: test
test: test-docker
	@docker run \
		--volume="$(shell pwd)":/home/bot/remote \
		--init --interactive --tty build-your-own-archlinux-repository \
		python bot test

.PHONY: run
run: test-docker update
	@docker run \
		--volume="$(shell pwd)":/home/bot/remote \
		--init --tty build-your-own-archlinux-repository \
		python bot build

.PHONY: update
update: test-docker
	@docker run \
		--volume="$(shell pwd)":/home/bot/remote \
		--init --tty build-your-own-archlinux-repository \
		python bot update

.PHONY: validation
validation: test-docker
	@docker run \
		--volume="$(shell pwd)":/home/bot/remote \
		--init --tty build-your-own-archlinux-repository \
		python bot validation
