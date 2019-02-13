FROM antergos/archlinux-base-devel

ARG USER_ID=1000
ADD Makefile /

RUN make provision-user
RUN make provision-packages

VOLUME /home/builder/repository
WORKDIR /home/builder/repository
USER builder

CMD make build
