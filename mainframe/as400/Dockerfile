# The Packet River AS/400 (IBM i) - a TN5250 green-screen host. Vendored from
# web3270's mock-lpar (GPL-3.0). No npm deps: node builtins + the local rpg/
# interpreter only.
FROM node:20-alpine

WORKDIR /app
COPY package.json mock-as400.js ./
COPY rpg ./rpg

RUN addgroup -S as400 && adduser -S as400 -G as400
USER as400

EXPOSE 3272
ENV MOCK_AS400_PORT=3272 \
    MOCK_AS400_SYSID=PACKETRIV \
    LOG_LEVEL=info

CMD ["node", "mock-as400.js"]
