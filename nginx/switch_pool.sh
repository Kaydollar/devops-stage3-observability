#!/bin/bash
# switch_pool.sh — swaps blue/green pools in Nginx dynamically

# Current active pool from env
CURRENT_POOL=${ACTIVE_POOL:-blue}

# Swap pools
if [ "$CURRENT_POOL" = "blue" ]; then
    NEW_POOL="green"
    PRIMARY_HOST="app_green"
    BACKUP_HOST="app_blue"
else
    NEW_POOL="blue"
    PRIMARY_HOST="app_blue"
    BACKUP_HOST="app_green"
fi

PRIMARY_PORT=3000
BACKUP_PORT=3000

echo "Switching ACTIVE_POOL from $CURRENT_POOL → $NEW_POOL"

# Export env for envsubst
export PRIMARY_HOST BACKUP_HOST PRIMARY_PORT BACKUP_PORT ACTIVE_POOL=$NEW_POOL

# Apply template and reload Nginx
envsubst '${PRIMARY_HOST} ${PRIMARY_PORT} ${BACKUP_HOST} ${BACKUP_PORT} ${ACTIVE_POOL}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf

# Reload Nginx without downtime
nginx -s reload

echo "Nginx reloaded. Active pool is now $NEW_POOL"
