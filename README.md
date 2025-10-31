# DevOps Stage 3 – Observability & Alerts for Blue/Green Deployment

This project extends the **Stage 2 Blue/Green Deployment** setup by adding **observability and actionable alerts**.
We use **Nginx access logs**, a **Python log watcher**, and **Slack notifications** to monitor and alert on application failovers or elevated error rates.

---

## 🧩 Architecture Overview

**Components:**

* **Nginx** – Routes requests between Blue and Green pools and writes detailed logs.
* **App Blue / App Green** – Two instances of the same app (only one is active).
* **Watcher (Python sidecar)** – Tails Nginx logs, parses events, and posts alerts to Slack.
* **Slack** – Receives alerts for failovers or high error rates.

**Flow Summary:**

1. Nginx logs every request including pool, release ID, and upstream status.
2. The Python watcher continuously reads the log file.
3. If a **failover** or **high error rate (> threshold)** occurs, a **Slack alert** is triggered.
4. Operators use the **runbook.md** to respond appropriately.

---

## ⚙️ Setup Instructions

### 1. Clone Repository

```bash
git clone https://github.com/Kaydollar/devops-stage3-observability.git
cd devops-stage3-observability
```

### 2. Configure Environment

Copy the example environment file and update variables:

```bash
cp .env.example .env
```

Fill in the values:

```
ACTIVE_POOL=blue
SLACK_WEBHOOK_URL=<your_slack_webhook_url>
ERROR_RATE_THRESHOLD=2
WINDOW_SIZE=200
ALERT_COOLDOWN_SEC=300
```

> ⚠️ **Important:** Do NOT commit `.env` with your real Slack webhook to GitHub.

---

```bash
mkdir -p logs/nginx
```

### 3. Build & Run

Start the stack:

```bash
docker compose up --build
```

This runs:

* `app_blue`
* `app_green`
* `bg_nginx` (reverse proxy)
* `alert_watcher` (Python service)

Nginx logs are stored in a shared volume accessible by the watcher.

---

## 🧪 Testing & Verification

### 🔄 1. Simulate Failover

Toggle between pools:

```bash
./switch_pool.sh
```

Expected:

* Nginx reloads.
* Slack receives a **Failover Detected** alert.

![alt text](<1. High Upstream error.png>)

### ⚠️ 2. Simulate Error Rate

You can simulate failed requests by temporarily breaking one backend (e.g., stopping `app_blue`):

```bash
docker stop app_blue
```

Expected:

* The watcher detects elevated 5xx responses.
* Slack receives a **High Error Rate Alert**.

![alt text](<2. Stage 3.png>)

After testing, restart the container:

```bash
docker start app_blue
```

### Step 3: Capture JSON Nginx Logs
These logs prove that your Nginx is recording pool, release, upstream status, latency, and upstream address in structured JSON.

- Steps:
1. Check the logs inside the Nginx container:

```bash
docker exec -it bg_nginx tail -n 10 /var/log/nginx/access.log
```

![alt text](<Stage 3... 3.png>)

---

## 📁 Project Structure

```
devops-stage3-observability/
│
├── nginx/
│   ├── nginx.conf.template     # Custom log format & upstream config
│   └── logs/                   # Shared Nginx logs
│
├── watcher/
│   ├── watcher.py              # Python log-watcher
│   └── requirements.txt        # Python dependencies
│
├── .env.example                # Environment variables (no secrets)
├── docker-compose.yml          # Multi-service setup
├── switch_pool.sh              # Blue↔Green toggle script
├── runbook.md                  # Operator guide
└── README.md                   # Documentation (this file)
```

---

## 📸 Verification Proofs

| Screenshot | Description                                                                        |
| ---------- | ---------------------------------------------------------------------------------- |
| ![]() 1      | Slack Alert – Failover Event                                                       |
| 🖼️ 2      | Slack Alert – High Error Rate                                                      |
| 🖼️ 3      | Nginx log snippet showing structured fields (pool, release, upstream status, etc.) |

---

## 📘 Runbook Summary

* **Failover Detected:** Check if the previously active pool is healthy; confirm the new one is stable.
* **High Error Rate:** Inspect upstream container logs, ensure backend app responds normally.
* **Recovery:** Once error rate normalizes, system resumes normal state.
* **Maintenance Mode:** Use environment flag to suppress alerts during planned toggles.

See `runbook.md` for full operator instructions.

## Quick start
1. Copy example env:
   ```bash
   cp .env.example .env

   # edit .env and add SLACK_WEBHOOK_URL

2.  Ensure you have logs/nginx dir:

```bash
mkdir -p logs/nginx
```

3. Build & start all services:

```bash
docker compose up -d --build
```

Verify

Apps: docker ps — app_blue, app_green should be Up (healthy).

Nginx: curl -s http://localhost:8080/version

Check logs: tail -n 50 logs/nginx/access.log

Testing — Failover (chaos drill)

1.  Ensure active pool current: ./switch_pool.sh --status

2. Force primary failure (example: stop primary container):

- If active is blue:
```bash
docker stop app_blue
```
- Now send traffic:
```bash
for i in $(seq 1 50); do curl -s http://localhost:8080/version >/dev/null; done
```

3. Restart the stopped container:
```bash
docker start app_blue
```

Testing — Error-rate alert

Option A (quick method): Temporarily point Nginx upstream to a failing backend:

1. Edit .env, set ACTIVE_POOL to a non-existing service, or create a simple container that responds 500 and switch PRIMARY_HOST to that container temporarily.

2. Recreate nginx: docker compose up -d --force-recreate nginx

3. Flood requests:
```bash
for i in $(seq 1 500); do curl -s http://localhost:8080/somepath >/dev/null; done
```

4. Watch Slack for error-rate alert.
## Logs and verification
- Access logs: tail -f logs/nginx/access.log (each line is JSON; confirm fields x_app_pool, upstream_status, upstream_addr, request_time).

- Alerts: check Slack channel for messages.

## Files of interest
- nginx/default.conf.tmpl — Nginx template (structured JSON logs).

- nginx/start.sh, nginx/reload.sh — config rendering and reload scripts.

- switch_pool.sh — toggle ACTIVE_POOL and recreate Nginx (with Slack notifications).

- watcher/ — log watcher Docker image and code.

- runbook.md — operator guidance.

---

### ✅ Stage 3 Acceptance Criteria

* Nginx logs include pool, release, upstream status, and latency.
* Watcher posts Slack alerts for failover and error-rate breaches.
* Alerts are deduplicated and respect cooldowns.
* Runbook is clear and actionable.

---

**Author:** Yinusa Kolawole (Kaydollar)
**Stage:** DevOps Internship – Stage 3 (Observability & Alerts)
