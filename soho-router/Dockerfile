# soho-router: a consumer WRT-style home router on the edge of town (Phase 5b).
# Deliberate weaknesses: WAN-side admin is reachable, the admin login is the
# shipped default, and the built-in Diagnostics packet-capture will hand you a
# decoded dump of the home LAN - where the resident (a rail engineer) signs in
# to a crew portal over plain HTTP on a loop.
FROM python:3.12-alpine

WORKDIR /app
RUN pip install --no-cache-dir "Flask==3.0.3"
COPY router.py resident.py ./

ENV PYTHONUNBUFFERED=1
ENV ADMIN_USER=admin ADMIN_PASS=admin
EXPOSE 80
CMD ["python", "router.py"]
