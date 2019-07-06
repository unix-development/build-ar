define bot
	@docker run \
		--volume="$(shell pwd)":/home/bot/remote \
		--init --tty build-your-own-archlinux-repository \
		python bot $(1)
endef


.PHONY: all
all: container run

.PHONY: container
container:
	@docker build --pull \
		--build-arg USER_ID=$(shell id -u) \
		--build-arg TRAVIS=$(TRAVIS) \
		--tag=build-your-own-archlinux-repository ./

.PHONY: package
package:
	$(call bot, package $(test))

.PHONY: run
run: update
	$(call bot, build)

.PHONY: update
update:
	$(call bot, update)

.PHONY: validation
validation:
	$(call bot, validation)
