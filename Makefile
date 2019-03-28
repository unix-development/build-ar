PROGRAM = repository-bot

ID = $(shell id -u)
PWD = $(shell pwd)

SETTING = \
	--volume="$(PWD)":/home/bot/remote \
	--init --tty $(PROGRAM)

container:
	@docker build \
		--build-arg USER_ID=$(ID) \
		--build-arg TRAVIS=$(TRAVIS) \
		--build-arg TOKEN=$(GITHUB_TOKEN) \
		--tag=$(PROGRAM) ./

run: update
	@docker run $(SETTING) \
		python bot build

package:
	@docker run $(SETTING) \
		python bot package $(test)

update:
	@docker run $(SETTING) \
		python bot update

validation:
	@docker run $(SETTING) \
		python bot validation

.PHONY: container validation update package run
