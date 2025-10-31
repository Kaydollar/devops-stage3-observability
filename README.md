# 🌀 Blue-Green Deployment Project (with Docker and NGINX)

**Author:** Yinusa Kolawole  
**Project Title:** Automated Blue-Green Deployment with Docker and NGINX  
**Stage:** DevOps Stage 2 — Deployment Automation

---

## 📘 Overview

This project demonstrates the **Blue-Green Deployment** strategy — a technique that ensures **zero downtime** during application updates or version rollouts.

It uses **Docker** and **NGINX** to simulate two identical environments:
- **Blue Environment:** The currently live version  
- **Green Environment:** The new version ready to replace Blue

Traffic is switched between the two using **NGINX reverse proxy configuration**, ensuring seamless version transitions.

---

## 🧩 Project Architecture

**Components:**
- **Nginx Container:** Acts as a reverse proxy to route traffic to either Blue or Green.
- **Blue Container:** Represents the current stable version of the app.
- **Green Container:** Represents the updated version of the app.

## Project structure

blue-green-project/
├── nginx/
│   ├── default.conf.tmpl       # Nginx template file (used for switching between blue/green)
│
├── reload.sh                   # Script to reload the environment (blue ↔ green)
├── start.sh                    # Script to start containers
├── .env                        # Environment variables (active environment, ports, etc.)
├── .env.example                # Sample environment config
├── docker-compose.yml          # Docker Compose setup for Nginx + App containers
└── README.md                   # Documentation

# Environment Variables

Copy .env.example → .env, then update values as needed:

``` bash
# .env.example

# Blue and Green image references
BLUE_IMAGE=yimikaade/wonderful:devops-stage-two   # Blue image
GREEN_IMAGE=yimikaade/wonderful:devops-stage-two  # Green image

# Which pool is currently active
ACTIVE_POOL=blue

# Release IDs for header identification
RELEASE_ID_BLUE=blue-v1
RELEASE_ID_GREEN=green-v1

# Exposed ports
PORT_BLUE=8081
PORT_GREEN=8082
NGINX_PORT=8080
```

# Docker Compose Setup

``` bash
# docker-compose.yml
version: "3.8"

services:
  app_blue:
    image: ${BLUE_IMAGE}
    container_name: app_blue
    environment:
      - RELEASE_ID=${RELEASE_ID_BLUE}
      - APP_POOL=blue
      - PORT=${PORT:-3000}
    ports:
      - "8081:${PORT:-3000}"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:${PORT:-3000}/healthz"]
      interval: 5s
      timeout: 2s
      retries: 3

  app_green:
    image: ${GREEN_IMAGE}
    container_name: app_green
    environment:
      - RELEASE_ID=${RELEASE_ID_GREEN}
      - APP_POOL=green
      - PORT=${PORT:-3000}
    ports:
      - "8082:${PORT:-3000}"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:${PORT:-3000}/healthz"]
      interval: 5s
      timeout: 2s
      retries: 3

  nginx:
    image: nginx:stable
    container_name: bg_nginx
    depends_on:
      - app_blue
      - app_green
    ports:
      - "${NGINX_PUBLIC_PORT:-8088}:80"
    volumes:
      - ./nginx/default.conf.tmpl:/etc/nginx/templates/default.conf.tmpl:ro
      - ./nginx/start.sh:/etc/nginx/start.sh:ro
      - ./nginx/reload.sh:/etc/nginx/reload.sh:ro
    environment:
      - ACTIVE_POOL=${ACTIVE_POOL}
      - APP_PORT=${PORT:-3000}
    command: ["/bin/sh", "-c", "/etc/nginx/start.sh"]
```

# Nginx Configuration

``` bash
# default.conf.tmpl

# upstream placeholders replaced by start.sh/reload.sh
upstream app_upstream {
    server PRIMARY_HOST:PRIMARY_PORT max_fails=1 fail_timeout=3s;
    server BACKUP_HOST:BACKUP_PORT backup;
    keepalive 16;
}

server {
    listen 80;

    proxy_connect_timeout 1s;
    proxy_send_timeout 3s;
    proxy_read_timeout 5s;

    proxy_next_upstream error timeout http_500 http_502 http_503 http_504;
    proxy_next_upstream_tries 2;

    location / {
        proxy_pass http://app_upstream;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-App-Proxy "nginx-blue-green";

        proxy_pass_header X-App-Pool;
        proxy_pass_header X-Release-Id;
    }

    location /healthz {
        proxy_pass http://app_upstream/healthz;
        proxy_set_header Host $host;
    }
}
```

# Manual Start Reload Script

``` bash
# nginx/start.sh
#!/bin/sh
set -eu
TEMPLATE=/etc/nginx/templates/default.conf.tmpl
OUT=/etc/nginx/conf.d/default.conf
ACTIVE_POOL=${ACTIVE_POOL:-blue}
APP_PORT=${APP_PORT:-3000}

if [ "$ACTIVE_POOL" = "blue" ]; then
  PRIMARY_HOST="app_blue"
  BACKUP_HOST="app_green"
elif [ "$ACTIVE_POOL" = "green" ]; then
  PRIMARY_HOST="app_green"
  BACKUP_HOST="app_blue"
else
  echo "Invalid ACTIVE_POOL: '$ACTIVE_POOL'"
  exit 1
fi

sed -e "s/PRIMARY_HOST/${PRIMARY_HOST}/g" \
    -e "s/BACKUP_HOST/${BACKUP_HOST}/g" \
    -e "s/PRIMARY_PORT/${APP_PORT}/g" \
    -e "s/BACKUP_PORT/${APP_PORT}/g" \
    "$TEMPLATE" > "$OUT"

echo "Generated $OUT (PRIMARY=${PRIMARY_HOST}:${APP_PORT})"
nginx -t && nginx -g 'daemon off;'
```

### I make the script executable
``` bash
chmod +x nginx/start.sh
```

```bash
# nginx/reload.sh

#!/bin/sh
set -eu
TEMPLATE=/etc/nginx/templates/default.conf.tmpl
OUT=/etc/nginx/conf.d/default.conf
ACTIVE_POOL=${ACTIVE_POOL:-blue}
APP_PORT=${APP_PORT:-3000}

if [ "$ACTIVE_POOL" = "blue" ]; then
  PRIMARY_HOST="app_blue"
  BACKUP_HOST="app_green"
elif [ "$ACTIVE_POOL" = "green" ]; then
  PRIMARY_HOST="app_green"
  BACKUP_HOST="app_blue"
else
  echo "Invalid ACTIVE_POOL: '$ACTIVE_POOL'"
  exit 1
fi

sed -e "s/PRIMARY_HOST/${PRIMARY_HOST}/g" \
    -e "s/BACKUP_HOST/${BACKUP_HOST}/g" \
    -e "s/PRIMARY_PORT/${APP_PORT}/g" \
    -e "s/BACKUP_PORT/${APP_PORT}/g" \
    "$TEMPLATE" > "$OUT"

echo "Reloading nginx (PRIMARY=${PRIMARY_HOST}:${APP_PORT})"
nginx -t && nginx -s reload
```

## I also made it executable

``` bash
chmod +x nginx/reload.sh
```

# How to run

1. I started the Start the stack & smoke tests by Copying the `.env.example` to `.env` and (locally) pulled the required images:

``` bash
docker pull yimikaade/wonderful:devops-stage-two
```
# 2. Launch

``` bash
docker compose up -d
docker compose ps
```

# 3. Details verification
| **Component** | **URL** | **Description** |
|----------------|----------|----------------|
| **Blue** | [http://35.176.120.145:8081/version](http://35.176.120.145:8081/version) | Direct access to **Blue** environment |
| **Green** | [http://35.176.120.145:8082/version](http://35.176.120.145:8082/version) | Direct access to **Green** environment |
| **Nginx** | [http://35.176.120.145:8080/version](http://35.176.120.145:8080/version) | Routed through **Nginx** (active environment) |

## 4. Baseline Check (Blue Active)

``` bash
curl -i http://localhost:8080/version | head -n 20
# Expected: 200 and headers:
# X-App-Pool: blue
# X-Release-Id: <RELEASE_ID_BLUE>
```

# 5. Induce chaos on blue (simulator provided in app image):

``` bash
curl -X POST "http://localhost:8081/chaos/start?mode=error"
```

# 6. Immediately check proxied endpoint after chaos:

``` bash
curl -i http://localhost:8080/version | head -n 20
# Expected: 200 and headers show X-App-Pool: green and X-Release-Id: <RELEASE_ID_GREEN>
```

# 7. Loop Test, I Opened a new terminal tab and run:

``` bash
# stop chaos
curl -X POST "http://localhost:8081/chaos/stop"
```
Expect header X-App-Pool change from blue → green and all proxied requests 200

