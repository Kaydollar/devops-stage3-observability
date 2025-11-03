#!/usr/bin/env python3
"""
watcher.py
Tails nginx JSON access log lines (one JSON object per line).
Detects failovers (pool changes) and high upstream 5xx error-rate over sliding window.
Posts alerts to Slack via webhook configured in env SLACK_WEBHOOK_URL.
"""

import os
import time
import json
import requests
from collections import deque
from datetime import datetime, timedelta

LOG_PATH = os.environ.get("NGINX_LOG_PATH", "/logs/nginx/access.log")
WEBHOOK = os.environ.get("SLACK_WEBHOOK_URL", "")
THRESHOLD_PCT = float(os.environ.get("ERROR_RATE_THRESHOLD", "2"))  # percent
WINDOW_SIZE = int(os.environ.get("WINDOW_SIZE", "200"))
ALERT_COOLDOWN = int(os.environ.get("ALERT_COOLDOWN_SEC", "300"))
ACTIVE_POOL = os.environ.get("ACTIVE_POOL", "").lower()  # initial value

# State
last_pool = None
error_window = deque(maxlen=WINDOW_SIZE)  # store booleans (is_5xx)
last_alert_time = {"failover": None, "error_rate": None}

def now_ts():
    return datetime.utcnow().isoformat() + "Z"

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
        try:
            # consider upstream_status may be "200" or "502, 200" etc.
            code = None
            if upstream_status:
                # take first numeric segment
                for part in str(upstream_status).split(","):
                    s = part.strip()
                    if s.isdigit():
                        code = int(s)
                        break
            if code is None and status:
                if str(status).isdigit():
                    code = int(status)
            if code and 500 <= int(code) < 600:
                is_upstream_5xx = True
        except Exception:
            is_upstream_5xx = False

        # append to window
        error_window.append(is_upstream_5xx)

        # check error rate
        check_and_alert_error_rate()

        # detect pool changes using x_app_pool, if present; otherwise infer from upstream_addr
        detected_pool = pool if pool else ( "green" if "green" in (upstream_addr or "") else ("blue" if "blue" in (upstream_addr or "") else None) )

        handle_pool(detected_pool, upstream_addr, upstream_status, line.strip())

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Watcher exiting")

