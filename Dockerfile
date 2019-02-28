FROM unixdevelopment/archlinux

ARG USER_ID
ARG TRAVIS

ENV IS_DOCKER=Yes
ENV TRAVIS=$TRAVIS
ENV USER_ID=$USER_ID

VOLUME /home/docker/build
WORKDIR /home/docker/build
USER docker

ADD Makefile /
CMD make build
