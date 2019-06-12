# Build Your Own Arch Linux Repository
This project is an easy-to-use program that provides functionalities to build a custom repository for Arch Linux. *Travis-ci* is used as a continuous integration service to automatically check if a new version of software has been released, build packages and deploy them into a server.

## Usage
You can build an unofficial repository by yourself with the following procedure:

#### 1. Fork the repository
Fork the [Repository Bot](https://github.com/unix-development/build-your-own-archlinux-repository) by clicking on the fork button at the top of the page.

#### 2. Integrate your fork into Travis-ci
Go to [travis-ci.org](https://travis-ci.org) and sign up with your GitHub account. Click on your name at the upper right corner to open your profile. Toggle the switch on your fork project. Click on settings button to configure a cron job [<sup>[1]</sup>](#footnote-01) that will build and deploy your repository.

#### 3. Install Travis-ci on your system
This tool is written in Ruby and is published as a gem. You need to install the gem with this command:

```
$ gem install travis
```

#### 4. Login to Travis
The login command will, well, log you in.

```
$ travis login
```

#### 5. Build Docker container
To build the container you will need to run:

```
$ make container
```

#### 6. Create an SSH key to deploy on your server
Change directory and generate a new key with ***no passphrase***.</br>
You must include it in the `authorized_keys` file in your server.

```
$ cd ~/.ssh
$ ssh-keygen -t rsa -b 4096 -C "travis-ci"
```

Copy your private key into your project and rename it `deploy_key`:
```
$ cp ~/.ssh/id_rsa ~/path/to/your/project
```

To make sure your key is correctly enabled into your server, just run:
```
$ ssh -i ./deploy_key user@yourdomaine.org
```

Encrypt your deploy key:
```
$ travis encrypt-file ./deploy_key --add
```

Once you notice that a couple of lines were added into your `.travis.yml`, you will be able to deploy your packages into your server.
```yaml
before_install:
- openssl aes-256-cbc -K $encrypted_77965d5bdd4d_key -iv $encrypted_77965d5bdd4d_iv
  -in deploy_key.enc -out ./deploy_key -d
```

You can validate your configuration running this at any time by running this:

```
$ make validation
```

#### 7. Create a personal access token
To keep your Github repository up to date, you will need to generate a new personal access token. Travis-ci will use it to commit new versions of your packages.

Go to [GitHub personal access tokens page](https://github.com/settings/tokens) and click on generate a new token button. Select the checkbox that give the full control over your repositories and click on generate token. Make sure to have a copy of your new personal access token now because you won’t be able to see it again!

#### 8. Configure your repository
Create and define your repository configuration into `repository.json`. You can paste your personal access token into token parameters.

*Be careful about SSH path because Travis-ci will remove files in choosen directory before deploying builded packages and database.*

```json
{
   "database": "custom",
   "url": "https://mirror.yourdomain.org",
   "github": {
      "token": "aed564c9e6f2a4fcadcad11af3334f6e"
   },
   "ssh": {
      "port": 22,
      "user": "user",
      "host": "yourdomain.org",
      "path": "/path/to/your/repository"
    }
}
```

Encrypt your repository configuration:
```
$ travis encrypt-file ./repository.json --add
```

#### 9. Add packages that you want to be in your repository
To add a new package, it needs to have a Git repository in order to verify if there are any updates. If you want to add the latest version of a package, you should create its directory in `pkg`. Let's have a look at an example with dwm:

```
$ cd packages
$ mkdir dwm
```

You now can create `package.py` in the new dwm directory. It will contain package information. To make sure it will correctly build, have `name` and `source` defined.

```python
#!/usr/bin/env python

name = 'dwm'
source = 'https://aur.archlinux.org/dwm.git'
```

If you want to change some configurations before being build by Travis-ci, you can create a `pre_build` function. In that example, I just add a dependency to my `PKGBUILD`.

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
$ make package test=dwm
```

#### 10. Let Travis-ci do its job
After committing and pushing your changes, you will notice that if your Travis-ci repository is being build. When it's complete, you can check your Github fork and you are supposed to see new commit changes in packages that you just added and files should be on your server.

#### 11. Add to Pacman
To use Pacman, you need to add this configuration to your `/etc/pacman.conf`.

```
[custom]
SigLevel = Optional TrustedOnly
Server = http://mirror.yourdomain.org
```

## Keep your fork up to date
Make sure to always be up to date by running this:

```
$ make update
```

## Footnotes
<sup id="footnote-01">1</sup> https://docs.travis-ci.com/user/cron-jobs </br>
<sup id="footnote-02">2</sup> https://docs.travis-ci.com/user/encryption-keys/
