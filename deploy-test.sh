#!/bin/sh
set -eu

root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
deploy_dir="$HOME/test/euai-pii"

mkdir -p "$deploy_dir"
cp "$root/deploy/test/docker-compose.yml" "$deploy_dir/docker-compose.yml"

if [ ! -f "$deploy_dir/.env" ]; then
  cp "$root/deploy/test/.env.example" "$deploy_dir/.env"
  chmod 600 "$deploy_dir/.env"
  printf '%s\n' "Created $deploy_dir/.env from the template; set SCREENING_CREDENTIAL and run this script again."
  exit 1
fi

cd "$deploy_dir"
docker compose build --pull=false
docker compose up -d --remove-orphans
docker compose ps
