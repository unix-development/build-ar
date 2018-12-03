FROM base/devel

COPY . /repository/builder
WORKDIR /repository/builder

RUN make build
CMD make bootstrap
