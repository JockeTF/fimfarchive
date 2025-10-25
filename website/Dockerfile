FROM docker.io/library/rust:alpine AS build

RUN apk add build-base

ARG UID=34407
RUN adduser -D -u "$UID" -h /build build
WORKDIR /build
USER build

COPY --chown="$UID" . .

RUN --mount=dst="$CARGO_HOME/registry",id=s7WhgTNd,type=cache,uid="$UID" true \
 && cargo build --release


FROM scratch

COPY --from=build /build/target/release/fimfawebsite .

ARG UID=34407
ENV BIND="[::]:$UID"
USER "$UID":"$UID"

CMD ["/fimfawebsite"]
