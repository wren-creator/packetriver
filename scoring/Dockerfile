# scoring: the only component that knows the flags. Phase 0 stands up the
# schema, the health check, and stub endpoints; Phase 1 adds per-session flag
# generation + injection, submission validation, the score formula, and the
# leaderboard.
FROM python:3.12-alpine

RUN apk add --no-cache curl

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 8001
ENTRYPOINT ["./entrypoint.sh"]
