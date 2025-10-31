# Runbook — Blue/Green Observability & Alerts

## Alert types
### 1) Failover detected
**Trigger**: watcher saw requests served by a different pool than previously observed (blue→green or green→blue).
**Meaning**: Primary became unavailable or Nginx switched upstream.
**Action**:
- Check Nginx logs: `docker compose logs nginx`
- Inspect which container is primary: `docker exec -it bg_nginx cat /etc/nginx/conf.d/default.conf | grep server`
- Check primary container health: `docker ps` and `docker logs app_blue` or `docker logs app_green`.
- If primary is unhealthy, investigate app container logs and restart or rollback as needed.
- If failover was expected (maintenance/upgrade), acknowledge and suppress further alerts by toggling maintenance mode.

### 2) High upstream error rate
**Trigger**: > ERROR_RATE_THRESHOLD% 5xx responses over last WINDOW_SIZE requests (default 2% over 200).
**Meaning**: Upstream(s) are returning 5xx or network problems to upstream.
**Action**:
- Check recent Nginx logs: `tail -n 200 logs/nginx/access.log` and search for upstream_status fields.
- Identify which upstream is returning errors (upstream_addr / x_app_pool).
- If primary is failing, consider switching to backup: run `./switch_pool.sh`.
- Inspect app logs for stack traces or resource exhaustion.
- If load test or deploy caused errors, rollback the release.

### 3) Recovery / Clear alert
When watcher sees healthy traffic again, no new alert is created, but operators should:
- Verify service stability for several minutes.
- If planned maintenance, turn off maintenance mode and resume normal operations.

## Maintenance mode / suppress alerts
To suppress watcher alerts during planned maintenance, temporarily set `ALERT_COOLDOWN_SEC` to a large value and/or stop `alert_watcher`:
```bash
# temporary suppression
docker compose pause alert_watcher
# or increase cooldown
sed -i 's/ALERT_COOLDOWN_SEC=.*/ALERT_COOLDOWN_SEC=3600/' .env
docker compose up -d alert_watcher

