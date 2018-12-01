FROM archlinux/base

COPY . /home/travis/repository
WORKDIR /home/travis/repository

RUN yes | pacman -Syu
RUN yes | pacman -S base base-devel git python
RUN echo '%wheel ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers

CMD make docker-execute
