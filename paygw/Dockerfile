FROM python:3.12-alpine
RUN apk add --no-cache curl && pip install --no-cache-dir Flask==3.0.3
WORKDIR /app
COPY . .
EXPOSE 8500
CMD ["python", "-u", "app.py"]
