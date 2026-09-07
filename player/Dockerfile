# player: the boxed-in attacker workstation. Real open-source tools, no route
# off the lab. Attack the town from here, or set PKT_LIGHT=1 and use your own
# shell against the published ports instead.
FROM python:3.12-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      sqlmap nmap curl jq iproute2 ca-certificates less git ncat mosquitto-clients dnsutils \
      tcpdump dsniff \
 && rm -rf /var/lib/apt/lists/*

# ttyd isn't in Debian trixie; grab the upstream static binary
RUN curl -fsSL -o /usr/local/bin/ttyd \
      "https://github.com/tsl0922/ttyd/releases/download/1.7.7/ttyd.$(uname -m)" \
 && chmod +x /usr/local/bin/ttyd

RUN pip install --no-cache-dir pymodbus==3.6.9 git-dumper==1.0.8

COPY scripts/ /opt/pktr/scripts/
COPY pktr-connect /usr/local/bin/pktr-connect
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh /usr/local/bin/pktr-connect /opt/pktr/scripts/*.sh 2>/dev/null || true

WORKDIR /opt/pktr
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
