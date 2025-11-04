#!/usr/bin/env python3
import os
import time
import json
import requests
from collections import deque

# === Config ===
LOG_PATH = os.getenv("NGINX_LOG_PATH", "/logs/nginx/access.log")
ERROR_RATE_THRESHOLD = float(os.getenv("ERROR_RATE_THRESHOLD", 2.0))
WINDOW_SIZE = int(os.getenv("WINDOW_SIZE", 200))
ALERT_COOLDOWN_SEC = int(os.getenv("ALERT_COOLDOWN_SEC", 300))
ACTIVE_POOL = os.getenv("ACTIVE_POOL", "blue")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

# === State ===
recent_status = deque(maxlen=WINDOW_SIZE)
last_alert_time = 0
last_seen_pool = ACTIVE_POOL


<<<<<<< HEAD
def post_slack(text):
    if not WEBHOOK:
        print(f"[{now_ts()}] No SLACK_WEBHOOK_URL set; would post: {text}")
        return
    payload = {"text": text}
    try:
        r = requests.post(WEBHOOK, json=payload, timeout=5)
        r.raise_for_status()
        print(f"[{now_ts()}] Posted to Slack: {text}")
    except Exception as e:
        print(f"[{now_ts()}] Error posting to Slack: {e}")

def check_and_alert_error_rate():
    if len(error_window) < max(1, int(WINDOW_SIZE/10)):  # don't alert too early
        return
    total = len(error_window)
    errors = sum(1 for v in error_window if v)
    pct = (errors / total) * 100
    if pct >= THRESHOLD_PCT:
        last = last_alert_time.get("error_rate")
        if not last or (datetime.utcnow() - last).total_seconds() > ALERT_COOLDOWN:
            msg = f":warning: High upstream error rate: {pct:.1f}% 5xx over last {total} requests (threshold {THRESHOLD_PCT}%)."
            post_slack(msg)
            last_alert_time["error_rate"] = datetime.utcnow()
        else:
            print(f"[{now_ts()}] Error-rate alert suppressed due to cooldown ({pct:.1f}%).")

def handle_pool(pool, upstream_addr, upstream_status, raw):
    global last_pool
    if last_pool is None:
        last_pool = pool
        return

    if pool and pool != last_pool:
        last = last_alert_time.get("failover")
        if not last or (datetime.utcnow() - last).total_seconds() > ALERT_COOLDOWN:
            msg = f":rotating_light: Failover detected: {last_pool} → {pool} at {now_ts()}\nUpstream: {upstream_addr}\nUpstream status: {upstream_status}\nLog sample: {raw}"
            post_slack(msg)
            last_alert_time["failover"] = datetime.utcnow()
        else:
            print(f"[{now_ts()}] Failover alert suppressed due to cooldown ({last_pool} → {pool}).")
        last_pool = pool

def parse_line(line):
    try:
        data = json.loads(line)
        # fields according to nginx log_format
        pool = (data.get("x_app_pool") or "").lower()
        release = data.get("x_release_id", "")
        upstream_status = data.get("upstream_status", "")
        upstream_addr = data.get("upstream_addr", "")
        status = data.get("status", "")
        return pool, release, upstream_status, upstream_addr, status, data
    except Exception as e:
        print(f"[{now_ts()}] JSON parse error: {e} -- line: {line.strip()}")
        return None, None, None, None, None, None

from collections import deque

def tail_file(path):
    # Wait until file exists
    while not os.path.exists(path):
        print(f"[{now_ts()}] Waiting for log file {path}")
        time.sleep(1)

    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
        # Only keep the last WINDOW_SIZE lines
        last_lines = deque(fh, maxlen=WINDOW_SIZE)
        for line in last_lines:
            yield line

        # Then keep following new lines
        while True:
            line = fh.readline()
            if not line:
                time.sleep(0.2)
                continue
            yield line

def main():
    print(f"[{now_ts()}] Watcher starting. Log: {LOG_PATH} threshold={THRESHOLD_PCT}% window={WINDOW_SIZE}")
    for line in tail_file(LOG_PATH):
        pool, release, upstream_status, upstream_addr, status, data = parse_line(line)
        if data is None:
            continue

        # is upstream 5xx?
        is_upstream_5xx = False
=======
def send_alert(message, level="error"):
    """Send alert to Slack or print to console."""
    emoji = "🚨" if level == "error" else "🟢"
    payload = {"text": f"{emoji} {message}"}
    if SLACK_WEBHOOK_URL:
>>>>>>> c6ebc8a (Updated my working files)
        try:
            requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=5)
        except Exception as e:
            print(f"⚠️ Failed to send Slack alert: {e}")
    else:
        print(f"{emoji} {message}")


def analyze_error_rate():
    """Compute rolling error rate as a percentage."""
    if not recent_status:
        return 0
    errors = sum(1 for code in recent_status if code >= 500)
    return (errors / len(recent_status)) * 100


def monitor_logs():
    global last_alert_time, last_seen_pool
    print(f"👀 Watching Nginx log file: {LOG_PATH}")
    print(f"🔧 ACTIVE_POOL = {ACTIVE_POOL}, WINDOW_SIZE = {WINDOW_SIZE}, ERROR_THRESHOLD = {ERROR_RATE_THRESHOLD}%")

    # Wait for log file to appear
    while not os.path.exists(LOG_PATH):
        print(f"Waiting for {LOG_PATH} ...")
        time.sleep(3)

    with open(LOG_PATH, "r") as f:
        f.seek(0, os.SEEK_END)
        while True:
            line = f.readline()
            if not line:
                time.sleep(1)
                continue

            try:
                log = json.loads(line.strip())
            except json.JSONDecodeError:
                # ignore non-JSON lines (classic logs, partial writes)
                continue

            status = int(log.get("status", 0))
            pool = log.get("x_app_pool", "unknown")
            recent_status.append(status)

            # Detect failover / pool switch
            if pool != last_seen_pool and (time.time() - last_alert_time > ALERT_COOLDOWN_SEC):
                send_alert(f"Failover detected: pool switched {last_seen_pool} → {pool}", level="error")
                last_seen_pool = pool
                last_alert_time = time.time()

            # Detect upstream errors
            error_rate = analyze_error_rate()
            now = time.time()
            if error_rate > ERROR_RATE_THRESHOLD and (now - last_alert_time > ALERT_COOLDOWN_SEC):
                send_alert(f"High upstream error rate: {error_rate:.2f}% on pool *{pool}*", level="error")
                last_alert_time = now

            # Recovery notification
            elif error_rate < 1.0 and (now - last_alert_time > 30):
                send_alert(f"Upstream pool *{pool}* recovered, error rate back to {error_rate:.2f}%", level="info")


if __name__ == "__main__":
    monitor_logs()

