FROM base/devel

ARG USER_ID=1000
ADD Makefile /

RUN make user
RUN make packages

VOLUME /home/builder/repository
WORKDIR /home/builder/repository
USER builder

CMD make build
