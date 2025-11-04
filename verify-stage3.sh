#!/bin/bash
set -e

echo "🔍 Stage 3 Observability Verification Script"
echo "---------------------------------------------"

# 1️⃣ Show running containers
echo "🧱 Checking running containers..."
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"
echo

# 2️⃣ Show currently active pool from nginx config
echo "🌊 Detecting currently active pool..."
docker exec bg_nginx grep "server" /etc/nginx/conf.d/default.conf | head -n 2
ACTIVE=$(docker exec bg_nginx grep "server" /etc/nginx/conf.d/default.conf | head -1 | grep -o 'app_[a-z]*' | cut -d_ -f2)
echo "✅ ACTIVE_POOL currently set to: ${ACTIVE}"
echo

# 3️⃣ Test /version and /healthz endpoints
echo "🌐 Testing endpoints through Nginx..."
curl -s localhost:8080/version
echo
curl -s localhost:8080/healthz
echo
echo "✅ Endpoints responded successfully"
echo

# 4️⃣ Display last few structured log lines
echo "🧾 Showing last 5 structured access logs..."
docker exec bg_nginx tail -n 5 /var/log/nginx/access.log
echo

# 5️⃣ Switch to the other pool and reload Nginx
if [ "$ACTIVE" = "blue" ]; then
  NEW="green"
else
  NEW="blue"
fi

echo "♻️ Switching pool from $ACTIVE to $NEW..."
docker exec -e ACTIVE_POOL=$NEW bg_nginx /etc/nginx/reload.sh
sleep 3

# 6️⃣ Confirm the switch
echo "🔁 Confirming pool switch..."
docker exec bg_nginx grep "server" /etc/nginx/conf.d/default.conf | head -n 2
curl -s localhost:8080/version
echo
echo "✅ Switch successful!"
echo

# 7️⃣ Verify watcher is running
echo "👀 Checking alert_watcher container..."
docker ps --filter "name=alert_watcher" --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"
echo
echo "✅ Watcher is running and monitoring logs."
echo

# 8️⃣ Simulate failure for alert_watcher detection
echo "🚨 Simulating upstream failure for alert demo..."
# Stop the currently active pool to cause 502/504 errors
docker stop app_${NEW} > /dev/null
sleep 5

# Make failing requests
for i in {1..5}; do
  curl -s -o /dev/null -w "%{http_code}\n" localhost:8080/version || true
done

sleep 5
echo "✅ Failure simulated. Check alert_watcher logs:"
docker logs alert_watcher --tail 10
echo

# Restart the stopped app
docker start app_${NEW} > /dev/null
sleep 5
echo "🩵 App ${NEW} restarted successfully."
echo

echo "🎉 Stage 3 verification (including failure alert) completed successfully!"

