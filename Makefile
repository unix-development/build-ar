PROGRAM = archlinux-repository
PACKAGES = python git

ID  = $(shell id -u)
PWD = $(shell pwd)

ifneq ($(shell if which python &> /dev/null; then echo 1; fi), )
	CONFIG    = $(shell python build/builder.py config $(1))
	DATABASE  = $(call CONFIG, database)
	GIT_EMAIL = $(call CONFIG, git.email)
	GIT_NAME  = $(call CONFIG, git.name)
	SSH_HOST  = $(call CONFIG, ssh.host)
	SSH_PATH  = $(call CONFIG, ssh.path)
	SSH_PORT  = $(call CONFIG, ssh.port)
	SSH_USER  = $(call CONFIG, ssh.user)
endif

build:
	@python build/builder.py create $(DATABASE)

prepare:
	@python build/assert.py repository
	@chmod 600 deploy_key
	@ssh-add deploy_key
	@ssh-keyscan -t rsa -H $(SSH_HOST) >> ~/.ssh/known_hosts
	@python build/assert.py ssh

docker:
	@docker build \
		--build-arg USER_ID="$(ID)" \
		--tag=archlinux-repository \
		--file=./build/Dockerfile ./

run:
	@docker run \
		--volume="$(PWD)":/home/builder/repository \
		archlinux-repository

deploy:
	@rm -f repository/*.old
	@rm -f repository/*.files
	@rm -f repository/*.files.tar.gz
	@git config user.email '$(GIT_EMAIL)'
	@git config user.name '$(GIT_NAME)'
	@rsync -avz --update --copy-links --progress -e 'ssh -p $(SSH_PORT)' \
		repository/ $(SSH_USER)@$(SSH_HOST):$(SSH_PATH)
	@python build/builder.py deploy

provision-packages:
	@yes | pacman -Syu
	@yes | pacman -S $(PACKAGES)

provision-user:
	@mkdir -p /home/builder/repository
	@useradd -u $(USER_ID) -s /bin/bash -d /home/builder -G wheel builder
	@chmod -R 777 /home/builder
	@chown -R builder /home/builder
	@echo '%wheel ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers

.PHONY: build deploy prepare docker run provision-packages provision-user
