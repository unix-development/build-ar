PARAMETERS := database git.email git.name ssh.user ssh.host ssh.path ssh.port
PACKAGES   := python git
ID         := $(shell id -u)
PWD        := $(shell pwd)

# Return configuration value defined by user in repository.json.
config = $(shell python build/builder.py config $(1))

deploy: ssh-push git-push

build:
	@python build/builder.py create $(call config, database)

prepare:
	@python build/assert.py repository
	@chmod 600 deploy_key
	@ssh-add deploy_key
	@ssh-keyscan -t rsa -H $(call config, ssh.host) >> ~/.ssh/known_hosts
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

provision-packages:
	@yes | pacman -Syu
	@yes | pacman -S $(PACKAGES)

provision-user:
	@mkdir -p /home/builder/repository
	@useradd -u $(USER_ID) -s /bin/bash -d /home/builder -G wheel builder
	@chmod -R 777 /home/builder
	@chown -R builder /home/builder
	@echo '%wheel ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers

git-push:
	@git config user.email '$(call config, git.email)'
	@git config user.name '$(call config, git.name)'
	@python build/builder.py deploy

ssh-push:
	@rm -f repository/*.old
	@rm -f repository/*.files
	@rm -f repository/*.files.tar.gz
	@ssh -i deploy_key $(call config, ssh.user)@$(call config, ssh.host) \
		'rm -rf $(call config, ssh.path)/*'
	@rsync -avz --copy-links --progress -e 'ssh -p $(call config, ssh.port)' \
		repository/ $(call config, ssh.user)@$(call config, ssh.host):$(call config, ssh.path)

.PHONY: build deploy prepare docker run provision-packages provision-user \
	git-push ssh-push valid valid-config valid-ssh
