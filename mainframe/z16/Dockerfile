# The Packet River IBM z16 (z/OS) - a TN3270E green-screen host. Vendored from
# web3270's mock-lpar (GPL-3.0). No npm deps: node builtins only. mock-lpar.js
# reads jcl/programs/*.jcl at startup, so the JCL members ship in the image too.
FROM node:20-alpine

WORKDIR /app
COPY package.json mock-lpar.js ./
COPY jcl ./jcl

RUN addgroup -S z16 && adduser -S z16 -G z16
USER z16

EXPOSE 3270
ENV MOCK_PORT=3270 \
    MOCK_SYSID=PACKETZ16 \
    MOCK_LU=PKTRLU01 \
    MOCK_ESM=RACF \
    LOG_LEVEL=info

CMD ["node", "mock-lpar.js"]
