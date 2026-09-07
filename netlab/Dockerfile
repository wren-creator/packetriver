# netlab: the Diner's open Wi-Fi, taught as a sniffable LAN standing in for
# 802.11 (Docker can't do real radio, and shipping something that deauths real
# APs would be irresponsible). One image, two roles:
#   default        -> the "AP": a cleartext rewards portal + a toy POP3 server,
#                     plus an ARP-storm watcher that feeds the Alert meter
#   ROLE=patron    -> a scripted diner patron that logs in + checks mail in
#                     cleartext every few seconds
FROM python:3.12-alpine

WORKDIR /app
RUN pip install --no-cache-dir "Flask==3.0.3" "paho-mqtt==2.1.0"
COPY ap.py patron.py entrypoint.sh ./
RUN chmod +x entrypoint.sh

ENV PYTHONUNBUFFERED=1
ENV MQTT_HOST=bus MQTT_PORT=1883 ROLE=ap
EXPOSE 80 110
ENTRYPOINT ["./entrypoint.sh"]
