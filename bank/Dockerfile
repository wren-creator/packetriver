FROM node:20-alpine
RUN apk add --no-cache curl
WORKDIR /app
COPY package.json .
RUN npm install --omit=dev --no-audit --no-fund
COPY . .
EXPOSE 8100
CMD ["node", "server.js"]
