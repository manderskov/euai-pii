import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
from uuid import UUID

from fastapi.testclient import TestClient
from presidio_analyzer import RecognizerResult

from euai_pii.api import CredentialBinding, CredentialStore, ScreeningRuntime, create_app
from euai_pii.detectors import CprRecognizer
from euai_pii.screening import Profile, ScreeningService


def make_runtime(detector=None, deadline_seconds=10):
    detector = detector or CprRecognizer()
    profile = Profile(
        profile_id="da-identifiers-v1",
        allowed_modes=frozenset({"block", "redact"}),
        detectors=(detector,),
        categories=frozenset(detector.supported_entities),
        thresholds={entity: 0.5 for entity in detector.supported_entities},
        version_material="test-profile",
    )
    service = ScreeningService({profile.profile_id: profile})
    credentials = CredentialStore(
        (CredentialBinding("test-secret", frozenset({profile.profile_id}), frozenset({"block", "redact"})),)
    )
    return ScreeningRuntime(service, credentials, deadline_seconds=deadline_seconds)


def client(detector=None, deadline_seconds=10):
    return TestClient(create_app(make_runtime(detector, deadline_seconds)))


def request_body(mode="redact", text="hello"):
    return {"mode": mode, "profile_id": "da-identifiers-v1", "language": "da", "text": text}


def test_allowed_response_is_complete_and_has_safe_headers():
    with client() as http:
        response = http.post("/v1/screen", headers={"Authorization": "Bearer test-secret"}, json=request_body())
    assert response.status_code == 200
    assert response.json()["action"] == "allowed"
    assert response.json()["text"] == "hello"
    assert response.json()["replacements"] == []
    assert response.headers["x-request-id"] == response.json()["request_id"]
    assert response.headers["cache-control"] == "no-store"


def test_block_response_contains_no_original_text_or_mapping():
    with client() as http:
        response = http.post(
            "/v1/screen",
            headers={"Authorization": "Bearer test-secret"},
            json=request_body("block", "CPR 010100-1234"),
        )
    body = response.json()
    assert response.status_code == 200
    assert body["action"] == "blocked"
    assert body["code"] == "protected_content"
    assert "text" not in body
    assert "replacements" not in body
    assert "010100-1234" not in response.text


def test_redaction_reuses_exact_values_and_reconstructs():
    text = "A 010100-1234, B 010100-1234."
    with client() as http:
        response = http.post(
            "/v1/screen",
            headers={"Authorization": "Bearer test-secret"},
            json=request_body("redact", text),
        )
    body = response.json()
    assert response.status_code == 200
    assert len(body["replacements"]) == 1
    replacement = body["replacements"][0]
    assert body["text"].count(replacement["key"]) == 2
    assert body["text"].replace(replacement["key"], replacement["value"]) == text


def test_token_collision_with_input_is_regenerated():
    collision = UUID("00000000-0000-4000-8000-000000000000")
    replacement = UUID("11111111-1111-4111-8111-111111111111")
    text = "[[EUAI_PII_00000000000040008000000000000000]] 010100-1234"
    runtime = make_runtime()
    profile = runtime.service.profiles["da-identifiers-v1"]
    try:
        with patch("euai_pii.screening.uuid.uuid4", side_effect=[UUID(int=1), collision, replacement]):
            result = runtime.service.screen(text, profile, "redact")
    finally:
        runtime.close()
    assert result["replacements"][0]["key"] == "[[EUAI_PII_11111111111141118111111111111111]]"


class StaticDetector:
    supported_entities = ["A", "B"]

    def analyze(self, text, entities):
        return [
            RecognizerResult("A", 1, 5, 1.0),
            RecognizerResult("B", 3, 8, 1.0),
            RecognizerResult("A", 7, 10, 1.0),
            RecognizerResult("A", 10, 12, 1.0),
        ]


def test_transitive_overlaps_merge_and_adjacent_spans_remain_distinct():
    with client(StaticDetector()) as http:
        response = http.post(
            "/v1/screen",
            headers={"Authorization": "Bearer test-secret"},
            json=request_body("redact", "012345678901"),
        )
    body = response.json()
    assert response.status_code == 200
    assert body["replacements"][0]["value"] == "123456789"
    assert body["replacements"][0]["entity_types"] == ["A", "B"]
    assert body["replacements"][1]["value"] == "01"


def test_authentication_and_profile_authorization_are_distinct():
    with client() as http:
        missing = http.post("/v1/screen", json=request_body())
        forbidden = http.post(
            "/v1/screen",
            headers={"Authorization": "Bearer wrong"},
            json=request_body(),
        )
    assert missing.status_code == 401
    assert missing.json()["error"]["code"] == "unauthorized"
    assert forbidden.status_code == 403
    assert forbidden.json()["error"]["code"] == "screening_not_authorized"


def test_validation_is_strict_and_does_not_echo_input():
    with client() as http:
        response = http.post(
            "/v1/screen",
            headers={"Authorization": "Bearer test-secret"},
            json={**request_body(), "unexpected": "secret-value"},
        )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_request"
    assert "secret-value" not in response.text


def test_non_json_and_reserved_prefix_are_rejected():
    with client() as http:
        media = http.post(
            "/v1/screen",
            headers={"Authorization": "Bearer test-secret", "Content-Type": "text/plain"},
            content="not json",
        )
        reserved = http.post(
            "/v1/screen",
            headers={"Authorization": "Bearer test-secret"},
            json=request_body(text="[[EUAI_PII_existing]]"),
        )
    assert media.status_code == 415
    assert reserved.status_code == 400


def test_raw_body_limit_is_enforced_without_echoing_body():
    oversized = '{"mode":"redact","profile_id":"da-identifiers-v1","language":"da","text":"ok","extra":"' + "x" * (1024 * 1024) + '"}'
    with client() as http:
        response = http.post(
            "/v1/screen",
            headers={"Authorization": "Bearer test-secret", "Content-Type": "application/json"},
            content=oversized,
        )
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "screening_limit_exceeded"
    assert "xxx" not in response.text


def test_text_codepoint_limit_is_distinguished_from_malformed_input():
    with client() as http:
        response = http.post(
            "/v1/screen",
            headers={"Authorization": "Bearer test-secret"},
            json=request_body(text="x" * 100001),
        )
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "screening_limit_exceeded"


class BadDetector:
    supported_entities = ["A"]

    def analyze(self, text, entities):
        return [RecognizerResult("A", 0, 1, float("nan"))]


def test_malformed_detector_output_fails_closed():
    with client(BadDetector()) as http:
        response = http.post(
            "/v1/screen",
            headers={"Authorization": "Bearer test-secret"},
            json=request_body(),
        )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "screening_unavailable"


def test_health_routes_do_not_disclose_runtime_inventory():
    with client() as http:
        live = http.get("/health/live")
        ready = http.get("/health/ready")
    assert live.status_code == 200
    assert live.json() == {"status": "ok"}
    assert ready.status_code == 200
    assert ready.json() == {"status": "ready"}


def test_openapi_is_available_programmatically_but_not_publicly_exposed():
    application = create_app(make_runtime())
    assert "/v1/screen" in application.openapi()["paths"]
    with TestClient(application) as http:
        assert http.get("/openapi.json").status_code == 404


class SlowDetector:
    supported_entities = ["A"]

    def analyze(self, text, entities):
        time.sleep(0.05)
        return []


def test_timeout_fails_closed_and_marks_readiness_false():
    with client(SlowDetector(), deadline_seconds=0.001) as http:
        response = http.post(
            "/v1/screen",
            headers={"Authorization": "Bearer test-secret"},
            json=request_body(),
        )
        ready = http.get("/health/ready")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "screening_unavailable"
    assert ready.status_code == 200


def test_saturation_rejects_the_second_request():
    with client(SlowDetector(), deadline_seconds=1) as http:
        with ThreadPoolExecutor(max_workers=2) as pool:
            responses = list(
                pool.map(
                    lambda _: http.post(
                        "/v1/screen",
                        headers={"Authorization": "Bearer test-secret"},
                        json=request_body(),
                    ),
                    range(2),
                )
            )
    assert sorted(response.status_code for response in responses) == [200, 503]
