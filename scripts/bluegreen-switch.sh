#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/deploy/bluegreen/compose.bluegreen.yml"
NGINX_CONF="$ROOT_DIR/deploy/bluegreen/nginx/conf.d/default.conf"

SLOT="${1:-}"

if [[ "$SLOT" != "blue" && "$SLOT" != "green" ]]; then
  echo "Usage: $0 <blue|green>"
  exit 1
fi

TARGET_SERVICE="fraud-api-${SLOT}"

cat > "$NGINX_CONF" <<EOF
upstream fraud_api {
    server ${TARGET_SERVICE}:8000;
}

server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://fraud_api;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

docker compose -f "$COMPOSE_FILE" exec -T fraud-api-proxy nginx -s reload
echo "Switched live traffic to ${SLOT}."
