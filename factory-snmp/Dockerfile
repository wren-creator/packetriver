# factory-snmp: the Widget Works "line management" box. A real net-snmp agent
# with the community strings still on their shipped values (public / private),
# so anyone who can reach udp/161 can read the line state - and write it.
FROM alpine:3.20

RUN apk add --no-cache net-snmp net-snmp-tools mosquitto-clients python3

COPY snmpd.conf /etc/snmp/snmpd.conf
COPY ops.py /usr/local/bin/ops.py
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/ops.py /usr/local/bin/entrypoint.sh

ENV MQTT_HOST=bus
EXPOSE 161/udp
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
