FROM base/devel

COPY . /repository/builder
WORKDIR /repository/builder

RUN groupadd -g 999 builder
RUN useradd -r -u 999 -g builder builder
RUN make build

USER builder
CMD make bootstrap
