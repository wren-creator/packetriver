# simmap: the town simulation, the map UI, and the realtime feed in one
# process. Phase 0 runs a light idle model and a debug breach/reset path;
# later phases add the ICS client loops and the physics integrators lifted
# from crosscreek/process-sim.
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 8000
# One plain gevent worker. flask-sock (simple-websocket) does its own WS
# handshake + framing, so it must NOT run under GeventWebSocketWorker - that
# worker upgrades the socket itself, and the two framers on one connection
# give the client "invalid attempt to fragment control frame" and a
# reconnect loop. `-w 1` keeps the tick / bus / ICS threads single-instance.
CMD ["gunicorn", "-k", "gevent", "-w", "1", "-b", "0.0.0.0:8000", \
     "--timeout", "120", "wsgi:app"]
