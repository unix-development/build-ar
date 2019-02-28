PROGRAM = archlinux-repository-bot

ID  = $(shell id -u)
PWD = $(shell pwd)

build:
	@python bot build

valid:
	@python bot validate

container:
	@docker build \
		--build-arg USER_ID="$(ID)" \
		--tag=${PROGRAM} ./

run:
	@docker run \
		--volume="$(PWD)":/home/docker \
		${PROGRAM}

.PHONY: build valid container run
