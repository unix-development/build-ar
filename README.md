# Arch Linux Repository
This repository provides the latest versions of softwares that I used. If you're interested to use it, you just need to add this configuration to your `/etc/pacman.conf`.

```
[lognoz]
SigLevel = Never
Server = http://mirror.lognoz.org
```

### Build your own repository
This project is an easy-to-use program that provide functionalities to check if a new version of software has been released. Synchronized with Travis CI, it's automatically build and deploy your packages into your server.

*Getting started with [build your own repository](https://github.com/lognoz/build-your-own-repository)*
