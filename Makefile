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

run:
	@$(call BOT, update)
	@$(call BOT, build)

package:
	@$(call BOT, package $(test))

validation:
	@$(call BOT, validation)

.PHONY: container validation update package run
