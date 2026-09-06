# field-plc: the water + power soft-PLCs (Modbus/TCP) and their operator HMI.
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /plc
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 502 503 8093
CMD ["python", "-u", "run.py"]
