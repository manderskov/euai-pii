#!/bin/sh
set -eu

compose="docker compose -f docker-compose.yml"
cleanup() {
  $compose down --remove-orphans
}
trap cleanup EXIT INT TERM

$compose build --pull=false
$compose up -d
ready=0
for _ in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30; do
  if $compose exec -T screening python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health/ready', timeout=3)" >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 2
done
test "$ready" -eq 1
$compose exec -T screening python -c "import http.client; c=http.client.HTTPConnection('127.0.0.1',8080,timeout=3); c.request('GET','/openapi.json'); assert c.getresponse().status == 401"
$compose exec -T screening python -c "import socket; sock=socket.socket(); sock.settimeout(2); result=sock.connect_ex(('93.184.216.34', 80)); sock.close(); assert result != 0, 'unexpected egress'"
