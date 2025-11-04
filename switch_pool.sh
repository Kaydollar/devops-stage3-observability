#!/bin/bash
set -e

# Load current ACTIVE_POOL from .env
if [ ! -f .env ]; then
  echo "❌ No .env file found. Please create one with ACTIVE_POOL=blue or green."
  exit 1
fi

CURRENT_POOL=$(grep '^ACTIVE_POOL=' .env | cut -d'=' -f2)
NEXT_POOL=""

# --- STATUS FLAG HANDLER ---
if [[ "$1" == "--status" ]]; then
  echo "🔍 Current active pool: ${CURRENT_POOL:-unknown}"
  exit 0
fi

# --- TOGGLE LOGIC ---
if [ "$CURRENT_POOL" = "blue" ]; then
  NEXT_POOL="green"
elif [ "$CURRENT_POOL" = "green" ]; then
  NEXT_POOL="blue"
else
  echo "⚠️ Unknown or missing ACTIVE_POOL in .env"
  exit 1
fi

echo "→ Switching from $CURRENT_POOL → $NEXT_POOL"

# Update .env file
sed -i "s/ACTIVE_POOL=$CURRENT_POOL/ACTIVE_POOL=$NEXT_POOL/" .env

# Recreate only nginx service
echo "→ Recreating Nginx with updated config..."
docker compose up -d --force-recreate nginx

# Health check
echo "→ Performing health check on http://localhost:8080/version..."
sleep 3
if curl -fs http://localhost:8080/version >/dev/null; then
  echo "✔ Switch successful! Active pool: $NEXT_POOL"
else
  echo "❌ Health check failed. Rolling back..."
  sed -i "s/ACTIVE_POOL=$NEXT_POOL/ACTIVE_POOL=$CURRENT_POOL/" .env
  docker compose up -d --force-recreate nginx
  exit 1
fi

