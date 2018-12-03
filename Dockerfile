FROM base/devel

COPY . /repository/builder
WORKDIR /repository/builder

USER builder
RUN make build
CMD make bootstrap
