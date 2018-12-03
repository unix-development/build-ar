FROM base/devel

COPY . /repository/builder
WORKDIR /repository/builder

RUN chmod -R 777 /repository/builder
RUN make user
RUN make build

USER builder
CMD make bootstrap
