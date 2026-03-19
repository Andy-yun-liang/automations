FROM python:3.12-slim

RUN apt-get update && apt-get install -y git inotify-tools && rm -rf /var/lib/apt/lists/* \
 && useradd -u 1000 -m controlplane

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
