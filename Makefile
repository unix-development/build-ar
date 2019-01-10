PARAMETERS := database git.email git.name ssh.user ssh.host ssh.path ssh.port
PACKAGES   := python git
ID         := $(shell id -u)
PWD        := $(shell pwd)

# Return configuration value defined by user in repository.json.
config = $(shell python build/builder.py config $(1))

# Test if SSH connection can be establish and directory exist
# in the server. Returns success or fail.
is_ssh_valid = $(shell \
	ssh -i ./deploy_key \
	-p $(1) -q $(2) \
	[[ -d $(3) ]] && \
		echo 'true' || echo 'false' \
)

deploy: ssh-push git-push

valid: valid-config valid-ssh

build:
	@python build/builder.py create $(call config, database)

prepare:
	@chmod 600 deploy_key
	@ssh-add deploy_key
	@ssh-keyscan -t rsa -H $(call config, ssh.host) >> ~/.ssh/known_hosts

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

valid-config:
	@echo 'Detect configuration in repository.json:'
	@$(foreach parameter, $(PARAMETERS), \
		$(if $(call config, $(parameter)), \
			echo '  $(parameter): $(call config, $(parameter))'; , \
			$(error Error: $(parameter) failed)))

valid-ssh:
	@echo 'Test SSH connection:'
	@$(if $(filter true, $(call is_ssh_valid, \
		$(call config, ssh.port), \
		$(call config, ssh.user)@$(call config, ssh.host), \
		$(call config, ssh.path))),  \
			echo '  It can be establish', \
			$(error Error: SSH connection fail))

.PHONY: build deploy prepare docker run provision-packages provision-user \
	git-push ssh-push valid valid-config valid-ssh
