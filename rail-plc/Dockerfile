# rail-plc: the loop-track switch + spur controller for Packet River.
# A raw-TCP "maintenance console" with default credentials and a command
# that shells out unsanitised - the deliberate weaknesses.
FROM python:3.12-alpine

WORKDIR /app
RUN pip install --no-cache-dir "paho-mqtt==2.1.0" "Flask==3.0.3"
COPY console.py .

RUN addgroup -S rp && adduser -S rp -G rp
USER rp

EXPOSE 2323 8096
ENV MQTT_HOST=bus MQTT_PORT=1883 CONSOLE_USER=maint CONSOLE_PASS=maint
CMD ["python", "console.py"]
