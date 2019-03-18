PROGRAM = repository-bot

ID = $(shell id -u)
PWD = $(shell pwd)

container:
	@docker build \
		--build-arg USER_ID=$(ID) \
		--build-arg TRAVIS=$(TRAVIS) \
		--build-arg TOKEN=$(GITHUB_TOKEN) \
		--tag=$(PROGRAM) ./

run:
	@docker run \
		--volume="$(PWD)":/home/bot/remote \
		--init --tty $(PROGRAM) \
		python bot build

test:
	@docker run \
		--volume="$(PWD)":/home/bot/remote \
		--init --tty $(PROGRAM) \
		python bot validate

update:
	@if [ -z "$$(git remote | grep upstream)" ]; then \
		git remote add upstream https://github.com/unix-development/build-your-own-archlinux-repository; \
	fi
	@git fetch upstream
	@git pull upstream master

.PHONY: container test update run
