#!/bin/sh
set -eu

compose="docker compose -f docker-compose.yml"
cleanup() {
  $compose down --remove-orphans
  test -z "$($compose ps -q)"
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
$compose exec -T screening python - <<'PY'
import http.client
import json
from concurrent.futures import ThreadPoolExecutor

def request(payload, credential="replace-with-a-provisioned-secret", content_type="application/json"):
    connection = http.client.HTTPConnection("127.0.0.1", 8080, timeout=15)
    connection.request("POST", "/v1/screen", body=json.dumps(payload), headers={
        "Authorization": f"Bearer {credential}",
        "Content-Type": content_type,
    })
    response = connection.getresponse()
    body = json.loads(response.read())
    connection.close()
    return response.status, body

base = {"profile_id": "da-identifiers-v1", "language": "da"}
status, allowed = request({**base, "mode": "block", "text": "SYNTHETIC_SECRET_VALUE"})
assert status == 200 and allowed["action"] == "allowed" and allowed["text"] == "SYNTHETIC_SECRET_VALUE"

status, blocked = request({**base, "mode": "block", "text": "CPR 010100-1234"})
assert status == 200 and blocked["action"] == "blocked"
assert "text" not in blocked and "replacements" not in blocked

status, redacted = request({**base, "mode": "redact", "text": "CPR 010100-1234"})
assert status == 200 and redacted["action"] == "redacted"
assert "010100-1234" not in redacted["text"]
restored = redacted["text"]
for replacement in redacted["replacements"]:
    restored = restored.replace(replacement["key"], replacement["value"])
assert restored == "CPR 010100-1234"

status, repeated = request({**base, "mode": "redact", "text": "CPR 010100-1234"})
assert status == 200 and repeated["replacements"][0]["key"] != redacted["replacements"][0]["key"]

status, unauthorized = request({**base, "mode": "block", "text": "safe"}, credential="wrong")
assert status == 403 and unauthorized["error"]["code"] == "screening_not_authorized"

status, invalid = request({**base, "mode": "block", "text": "not json"}, content_type="text/plain")
assert status == 415 and invalid["error"]["code"] == "unsupported_media_type"

large = {**base, "mode": "block", "text": "safe " * 20000}
with ThreadPoolExecutor(max_workers=2) as pool:
    statuses = list(pool.map(lambda _: request(large)[0], range(2)))
assert all(status in (200, 503) for status in statuses)
PY
$compose exec -T screening python - <<'PY'
import asyncio
import time
from euai_pii.api import CredentialBinding, CredentialStore, ScreenRequest, ScreeningRuntime
from euai_pii.screening import Profile, ScreeningService

class SlowDetector:
    supported_entities = ["A"]
    def analyze(self, text, entities):
        if text == "slow":
            time.sleep(11)
        return []

async def verify_worker_boundary():
    profile = Profile("da-identifiers-v1", frozenset({"block", "redact"}), (SlowDetector(),), frozenset({"A"}), {"A": 0.5}, "verify")
    service = ScreeningService({profile.profile_id: profile})
    credentials = CredentialStore((CredentialBinding("test", frozenset({profile.profile_id}), frozenset({"block", "redact"})),))
    runtime = ScreeningRuntime(service, credentials, deadline_seconds=0.05)
    request = ScreenRequest(mode="block", profile_id=profile.profile_id, language="da", text="slow")
    try:
        result = await runtime.screen(ScreenRequest(mode="block", profile_id=profile.profile_id, language="da", text="safe"), "test")
        assert result["action"] == "allowed"
        try:
            await runtime.screen(request, "test")
        except Exception as error:
            assert getattr(error, "code", None) == "screening_unavailable"
        assert runtime.ready
    finally:
        runtime.close()

asyncio.run(verify_worker_boundary())
PY
 $compose exec -T screening python - <<'PY'
import http.client
import json
import socket
import time

text = "CPR 010100-1234 " * 5000
body = json.dumps({"mode": "redact", "profile_id": "da-personal-v1", "language": "da", "text": text}).encode()
request = (
    b"POST /v1/screen HTTP/1.1\r\n"
    b"Host: 127.0.0.1:8080\r\n"
    b"Authorization: Bearer replace-with-a-provisioned-secret\r\n"
    b"Content-Type: application/json\r\n"
    + f"Content-Length: {len(body)}\r\n\r\n".encode()
    + body
)
connection = socket.create_connection(("127.0.0.1", 8080), timeout=3)
connection.sendall(request)
connection.shutdown(socket.SHUT_RDWR)
connection.close()
time.sleep(12)

followup = http.client.HTTPConnection("127.0.0.1", 8080, timeout=15)
followup.request("POST", "/v1/screen", body=json.dumps({
    "mode": "block", "profile_id": "da-identifiers-v1", "language": "da", "text": "safe"
}), headers={
    "Authorization": "Bearer replace-with-a-provisioned-secret",
    "Content-Type": "application/json",
})
response = followup.getresponse()
assert response.status == 200
assert json.loads(response.read())["action"] == "allowed"
followup.close()
PY
logs=$($compose logs --no-log-prefix screening)
case "$logs" in
  *SYNTHETIC_SECRET_VALUE*|*010100-1234*) exit 1 ;;
esac
$compose exec -T screening python -c "import socket; sock=socket.socket(); sock.settimeout(2); result=sock.connect_ex(('93.184.216.34', 80)); sock.close(); assert result != 0, 'unexpected egress'"
