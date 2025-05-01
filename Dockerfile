FROM docker.io/library/archlinux:latest

RUN --mount=type=cache,target=/var/cache/pacman/pkg true \
 && pacman -Syu --noconfirm git python uv

ARG UID=45421
RUN useradd -u $UID -d /app app
WORKDIR /app
USER app

ENV UV_LINK_MODE=copy UV_NO_SYNC=1
COPY --chown=$UID pyproject.toml ./
RUN --mount=type=cache,target=.cache,uid=$UID,gid=$UID,mode=0700 true \
 && uv sync --extra lz4 --no-install-project
COPY --chown=$UID . .
