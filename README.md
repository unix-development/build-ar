# Build-Ar — Build Your Own Arch Linux Repository
This project is an easy-to-use program that provides functionalities to build a
custom repository for Arch Linux. This bot will automatically check if a new
version of software has been released, build packages and deploy them into a
server.

## Usage
**Important: Make sure you have Docker on your system before following the next steps.**

1. Fork this [repository](https://github.com/unix-development/build-ar)
   by clicking on the fork button at the top of the page.

2. To build the docker container you will need to run:

   ```
   $ make container
   ```

3. Create an SSH key to deploy on your server. Change directory and generate a
   new key with ***no passphrase***. You must include it in the
   `authorized_keys` file in your server.

   ```
   $ cd ~/.ssh
   $ ssh-keygen -t rsa -b 4096 -C "repository"
   ```

   Copy your private key into your project and rename it `deploy_key`:
   ```
   $ cp ~/.ssh/id_rsa ~/path/to/your/project
   ```

   To make sure your key is correctly enabled into your server, just run:
   ```
   $ ssh -i ./deploy_key user@yourdomaine.org
   ```

   You can validate your configuration running this at any time by running this:

   ```
   $ make validation
   ```

4. To keep your Github repository up to date, you will need to generate a new
   personal access token. The bot will use it to commit new versions of your
   packages.

   Go to [GitHub personal access tokens
   page](https://github.com/settings/tokens) and click on generate a new token
   button. Select the checkbox that give the full control over your
   repositories and click on generate token. Make sure to have a copy of your
   new personal access token now because you won’t be able to see it again!

5. Create and define your repository configuration into `repository.yml` by using
   [sample.yml](sample.yml) file. You can paste your personal access token into Github 
   token parameters.
   ```yaml
   github:
     token: aed564c9e6f2a4fcadcad11af3334f6e
   ```

   If you want to prevent auto update, you can remove these lines from your
   repository.yml.
   ```yaml
   auto-update:
     - bot
     - readme
   ```

   If you prefers to use your repository in local system, you will need to
   remove these lines or it will trigger errors. Be careful about SSH path
   because the bot will remove files in chosen directory before deploying
   packages and database.
   ```yaml
   url: https://mirror.yourdomain.org
   ssh:
     port: 22
     user: user
     host: yourdomain.org
     path: /path/to/your/repository
   ```

6. Add packages that you want to be in your repository. It needs to have a Git
   repository in order to verify if there are any updates. If you want to add
   the latest version of a package, you should create its directory in `pkg`.
   Let's have a look at an example with dwm:

   ```
   $ cd packages
   $ mkdir dwm
   ```

   You now can create `package.py` in the new dwm directory. It will contain
   package information. To make sure it will correctly build, have `name` and
   `source` defined.

   ```python
   #!/usr/bin/env python

   name = 'dwm'
   source = 'https://aur.archlinux.org/dwm.git'
   ```

   If you want to change some configurations before being build by the bot,
   you can create a `pre_build` function. In that example, I just add a
   dependency to my `PKGBUILD`.

   ```python
   #!/usr/bin/env python

   name = 'dwm'
   source = 'https://aur.archlinux.org/dwm.git'

   def pre_build():
      for line in edit_file('PKGBUILD'):
         if line.startswith('depends=('):
            print(line.replace(')', " 'adobe-source-code-pro-fonts')"))
         else:
            print(line)
   ```

   You can test your package build by running this:

   ```
   $ make test
   ```

7. When you're ready, let the bot do its job with this command:
   ```
	$ make run
   ```

8. To use Pacman, you need to add this configuration to your
    `/etc/pacman.conf`.

    ```
    [custom]
    SigLevel = Optional TrustedOnly
    Server = http://mirror.yourdomain.org
    ```

## Use Travis CI to execute cron job

1. Go to [travis-ci.org](https://travis-ci.org) and sign up with your GitHub
   account. Click on your name at the upper right corner to open your profile.
   Toggle the switch on your fork project. Click on settings button to
   configure a cron job [<sup>[1]</sup>](#footnote-01) that will build and
   deploy your repository.

2. Install Travis-ci on your system. This tool is written in Ruby and is published as a gem. You need to install
   the gem with this command:

   ```
   $ gem install travis
   ```

3. Log you in Travis by running this:

   ```
   $ travis login
   ```
4. Encrypt your deploy key:
   ```
   $ travis encrypt-file ./deploy_key --add
   ```

   Once you notice that a couple of lines were added into your `.travis.yml`,
   you will be able to deploy your packages into your server.
   ```yaml
   before_install:
   - openssl aes-256-cbc -K $encrypted_77965d5bdd4d_key -iv $encrypted_77965d5bdd4d_iv
     -in deploy_key.enc -out ./deploy_key -d
   ```
5. Encrypt your repository configuration:
   ```
   $ travis encrypt-file ./repository.yml --add
   ```

6. Let Travis-ci do its job! After committing and pushing your changes, you
   will notice that if your Travis-ci repository is being build. When it's
   complete, you can check your Github fork and you are supposed to see new
   commit changes in packages that you just added and files should be on your
   server.

## Keep your fork up to date
Make sure to always be up to date by running this:

```
$ make update
```

## Footnotes
<sup id="footnote-01">1</sup> https://docs.travis-ci.com/user/cron-jobs </br>
<sup id="footnote-02">2</sup> https://docs.travis-ci.com/user/encryption-keys/
