PROGRAM = archlinux-repository
PACKAGES = python git

ID  = $(shell id -u)
PWD = $(shell pwd)

build:
	@python bot build

valid:
	@python bot validate

docker:
	@docker build \
		--build-arg USER_ID="$(ID)" \
		--tag=archlinux-repository \
		--file=./Dockerfile ./

run:
	@docker run \
		--volume="$(PWD)":/home/builder/repository \
		archlinux-repository

provision-user:
	@mkdir -p /home/builder/repository
	@useradd -u $(USER_ID) -s /bin/bash -d /home/builder -G wheel builder
	@chmod -R 777 /home/builder
	@chown -R builder /home/builder
	@echo '%wheel ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers

provision-packages:
	@yes | pacman -Sy
	@yes | pacman -S $(PACKAGES)

.PHONY: build valid docker run provision-packages provision-user
