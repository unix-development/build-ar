FROM archlinux/base

COPY . /home/travis/repository
WORKDIR /home/travis/repository

RUN pacman -Syu --noconfirm
RUN pacman -S base base-devel git make python --noconfirm
RUN echo '%wheel ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers

CMD make docker-execute
