#!/bin/sh
set -eu

root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
env_file="$root/.env"

if [ ! -f "$env_file" ]; then
  cp "$root/.env.example" "$env_file"
  chmod 600 "$env_file"
  printf '%s\n' "Created $env_file from .env.example; set SCREENING_CREDENTIAL and run this script again."
  exit 1
fi

set -a
. "$env_file"
set +a
: "${SCREENING_CONFIG_PATH:?SCREENING_CONFIG_PATH must be set in .env}"
: "${SCREENING_CREDENTIAL:?SCREENING_CREDENTIAL must be set in .env}"

"$root/.venv/bin/python" -m pip install --no-deps -e "$root" >/dev/null
cd "$root"
exec "$root/.venv/bin/uvicorn" euai_pii.api:app --host 0.0.0.0 --port 6010
