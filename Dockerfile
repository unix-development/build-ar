FROM unixdevelopment/archlinux

ARG TOKEN
ARG TRAVIS
ARG USER_ID

ENV IS_DOCKER = Yes
ENV GITHUB_TOKEN = $TOKEN
ENV TRAVIS = $TRAVIS

RUN mkdir \
    --parents /home/bot

RUN useradd \
    --uid $USER_ID \
    --shell /bin/bash \
    --home-dir /home/bot \
    --groups wheel bot

RUN chown \
    --recursive bot /home/bot

VOLUME /home/bot/remote
WORKDIR /home/bot/remote
USER bot

ADD Makefile /
CMD make build
