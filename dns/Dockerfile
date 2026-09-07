# Packet River municipal DNS - CoreDNS, authoritative for packetriver.range,
# with zone transfer left wide open on purpose.
FROM alpine:3.20

RUN apk add --no-cache coredns

COPY Corefile /etc/coredns/Corefile
COPY db.packetriver.range.tmpl /etc/coredns/db.packetriver.range.tmpl
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

EXPOSE 53 53/udp
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
