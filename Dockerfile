FROM unixdevelopment/archlinux

ENV IS_DOCKER Yes

VOLUME /home/docker
WORKDIR /home/docker
USER docker

ADD Makefile /
CMD make build
