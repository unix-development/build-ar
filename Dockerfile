FROM base/devel

COPY . /repository/builder
WORKDIR /repository/builder

RUN groupadd -g 1000 builder
RUN useradd -r -u 1000 -g wheel builder
RUN make build

USER builder
CMD make bootstrap
