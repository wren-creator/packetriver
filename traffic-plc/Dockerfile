# traffic-plc: the four/five intersection signal controllers for Packet River.
# Takes commands off the MQTT bus with no ACL and no auth (the deliberate
# weakness); a hardened broker (docker-compose.segmented.yml) password-gates
# pkt/traffic/#.
FROM python:3.12-alpine

WORKDIR /app
RUN pip install --no-cache-dir "paho-mqtt==2.1.0" "Flask==3.0.3"
COPY controller.py .

RUN addgroup -S tp && adduser -S tp -G tp
USER tp

EXPOSE 8095
ENV MQTT_HOST=bus MQTT_PORT=1883 ENG_PIN=0000
CMD ["python", "controller.py"]
