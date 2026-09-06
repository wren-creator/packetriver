# gateway: the single way into Packet River. Routes the vulnerable mini-sites
# by Host: header (added in later phases) and reverse-proxies the map UI, the
# WebSocket feed, and the scoring API. Its JSON access log lands on a shared
# volume for the Alert-Level tailer (Phase 4).
FROM nginx:alpine

RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
