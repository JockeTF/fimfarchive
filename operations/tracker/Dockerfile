FROM docker.io/library/debian:bookworm-slim

RUN apt-get -y update \
 && apt-get -y full-upgrade \
 && apt-get -y install opentracker \
 && rm -r /var/lib/apt/lists/*

COPY opentracker.conf whitelist.txt /etc/opentracker/

EXPOSE 6969/tcp
EXPOSE 6969/udp
USER 6969:6969

CMD ["/usr/bin/opentracker", "-f", "/etc/opentracker/opentracker.conf"]
