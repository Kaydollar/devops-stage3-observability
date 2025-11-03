# watcher/Dockerfile
FROM python:3.9-slim

# Set working directory
WORKDIR /watcher

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy watcher script
COPY watcher.py .

# Set default environment variables (can be overridden in compose)
ENV NGINX_LOG_PATH=/logs/nginx/access.log
ENV ERROR_RATE_THRESHOLD=2.0
ENV WINDOW_SIZE=200
ENV ALERT_COOLDOWN_SEC=300
ENV ACTIVE_POOL=blue
ENV SLACK_WEBHOOK_URL=""

# Run watcher
CMD ["python", "watcher.py"]

CMD ["python", "watcher.py"]
