FROM archlinux/base

RUN pacman -Syu --noconfirm
RUN pacman -S base base-devel git make python --noconfirm
RUN mkdir -p /home/travis/repository
RUN echo '%wheel ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers

VOLUME /home/travis/repository
WORKDIR /home/travis/repository

CMD python /home/travis/bootstrap.py
