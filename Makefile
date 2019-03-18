PROGRAM = repository-bot

ID = $(shell id -u)
PWD = $(shell pwd)
BOT = \
	docker run \
		--volume="$(PWD)":/home/bot/remote \
		--init --tty $(PROGRAM) \
		python bot $(1)

container:
	@docker build \
		--build-arg USER_ID=$(ID) \
		--build-arg TRAVIS=$(TRAVIS) \
		--build-arg TOKEN=$(GITHUB_TOKEN) \
		--tag=$(PROGRAM) ./

update:
	@if [ -z "$$(git remote | grep upstream)" ]; then \
		git remote add upstream https://github.com/unix-development/build-your-own-archlinux-repository; \
	fi
	@git fetch upstream
	@git pull upstream master

run:
	@$(call BOT, build)

package:
	@$(call BOT, package $(test))

getting-started:
	@$(call BOT, getting-started)

.PHONY: container getting-started update package run
