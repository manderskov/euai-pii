# Test Plan 1 - Private Screening Service

This plan verifies the EUAI PII development service started from VS Code on port
6010 and the F-007 screening contract using synthetic data and Postman. It is
suitable for Gate 2 review evidence.

Do not use customer data or real credentials.

## 1. Prerequisites

- VS Code is installed with this repository opened as the workspace.
- The repository `.venv` has been created and its pinned dependencies installed.
- Postman is installed.
- The machine running VS Code is reachable on the network as `apex.lan`.
- A local `.env` contains `SCREENING_CONFIG_PATH` and `SCREENING_CREDENTIAL`.

From the VS Code integrated terminal, at the repository root, verify the setup:

```sh
.venv/bin/python --version
.venv/bin/python -c "import euai_pii, spacy; spacy.load('da_core_news_md')"
```

## 2. Start From VS Code

Start the service in the VS Code integrated terminal. The `0.0.0.0` bind is
required so another machine on the network can connect through `apex.lan`:

```sh
export SCREENING_CONFIG_PATH="$PWD/config/screening.example.json"
set -a; source .env; set +a
.venv/bin/uvicorn euai_pii.api:app --host 0.0.0.0 --port 6010
```

Leave this terminal running while testing. Do not use the example credential or
synthetic configuration for production or customer data.

## 3. Verify Startup

```sh
curl http://127.0.0.1:6010/health/live
curl http://apex.lan:6010/health/ready
```

Both requests must return HTTP `200`. Model startup can take approximately
30 seconds.

If startup fails, inspect the output in the VS Code terminal where Uvicorn is
running without using customer content.

## 4. Configure Postman

Create a Postman environment with:

| Variable | Value |
| --- | --- |
| `base_url` | `http://apex.lan:6010` |
| `screening_credential` | The value of `SCREENING_CREDENTIAL` from `.env` |

Use `Authorization: Bearer {{screening_credential}}` for authenticated requests.
Use `Content-Type: application/json` for screening requests.

The remaining tests use this `base_url`.

## 5. Test Liveness

Request:

```text
GET {{base_url}}/health/live
```

Expected result:

- HTTP `200`
- Body is exactly `{"status":"ok"}`
- No model or profile inventory is disclosed.

## 6. Test Readiness

Request:

```text
GET {{base_url}}/health/ready
```

Expected result after startup:

- HTTP `200`
- Body is exactly `{"status":"ready"}`

The service must not be used while this request returns HTTP `503`.

## 7. Test OpenAPI Authentication

Unauthenticated request:

```text
GET {{base_url}}/openapi.json
```

Expected result:

- HTTP `401`
- No schema is returned.

Authenticated request:

```text
GET {{base_url}}/openapi.json
Authorization: Bearer {{screening_credential}}
```

Expected result:

- HTTP `200`
- The schema contains `POST /v1/screen`.
- Interactive `/docs` and `/redoc` endpoints are unavailable.

## 8. Test Allowed Content

Request:

```text
POST {{base_url}}/v1/screen
```

Body:

```json
{
  "mode": "block",
  "profile_id": "da-identifiers-v1",
  "language": "da",
  "text": "Dette er en syntetisk besked uden beskyttet indhold."
}
```

Expected result:

- HTTP `200`
- `action` is `allowed`.
- `text` is unchanged.
- `replacements` is an empty array.
- `x-request-id` matches the response `request_id`.
- `Cache-Control` is `no-store`.

## 9. Test Blocked Content

Use the same request with:

```json
{
  "mode": "block",
  "profile_id": "da-identifiers-v1",
  "language": "da",
  "text": "Syntetisk CPR: 010100-1234"
}
```

Expected result:

- HTTP `200`.
- `action` is `blocked`.
- `code` is `protected_content`.
- The response has no `text` field.
- The response has no `replacements` field.
- The original CPR value is not present in the response body.

## 10. Test Redaction And Restoration

Use:

```json
{
  "mode": "redact",
  "profile_id": "da-identifiers-v1",
  "language": "da",
  "text": "Syntetisk CPR: 010100-1234"
}
```

Expected result:

- HTTP `200`.
- `action` is `redacted`.
- `text` contains an opaque `[[EUAI_PII_<32 hex characters>]]` token.
- `text` does not contain `010100-1234`.
- `replacements` contains one entry with the original value and entity type
  `DK_CPR`.

Copy the returned mapping into a local Postman test script or inspect manually.
Replace the token in the transformed text with the mapping value exactly once.
The resulting text must equal:

```text
Syntetisk CPR: 010100-1234
```

Do not send the mapping or original value to a model or external service.

## 11. Test Request-Local Isolation

Repeat the same redaction request twice.

Expected result:

- Both requests return `redacted`.
- Each response has a complete mapping.
- The token from request 1 differs from the token from request 2.
- Request 1's mapping reconstructs only request 1.
- No response depends on a previous request.

## 12. Test Danish NER Profile

Use the personal profile:

```json
{
  "mode": "redact",
  "profile_id": "da-personal-v1",
  "language": "da",
  "text": "Skriv til Anna Jensen i Aarhus."
}
```

Expected result:

- HTTP `200`.
- `action` is `redacted` or `allowed` according to the accepted Gate 1 model
  behavior.
- Any returned replacement must not expose its original value in transformed
  `text`.
- Do not treat this test as proof of complete person or address detection.

## 13. Test Safe Failures

Run each case and verify that the response is static and contains no submitted
content, validation details, stack trace, credential, or exception text.

| Case | Expected status | Expected code |
| --- | ---: | --- |
| Missing `Authorization` header | 401 | `unauthorized` |
| Wrong bearer credential | 403 | `screening_not_authorized` |
| Unsupported content type | 415 | `unsupported_media_type` |
| Unknown JSON field | 400 | `invalid_request` |
| Reserved token prefix in input | 400 | `invalid_request` |
| Text over 100,000 code points | 413 | `screening_limit_exceeded` |

## 14. Test Consumer Boundary

Run the standalone harness independently of the EUAI application:

```sh
cd consumer-harness
npm ci
npm test
npm audit --audit-level=high
```

Expected result:

- TypeScript compilation succeeds.
- All consumer tests pass.
- Blocked responses never produce model input.
- Redacted model input contains tokens but not replacement values.
- Restoration supports repeated and reordered known tokens.
- Missing tokens are allowed.
- Unknown or modified tokens fail restoration.
- Duplicate or malformed mappings fail validation.

## 15. Verify Runtime Privacy And Network Boundaries

Run the repository verification script:

```sh
./scripts/verify_container.sh
```

The script verifies:

- Pinned offline image build.
- Nonroot startup and readiness.
- Authenticated OpenAPI access.
- Live allowed, blocked, and redacted responses.
- Exact restoration and request-token isolation.
- Safe authentication/media failures.
- Concurrent request behavior and saturation handling.
- Worker timeout, restart, and discarded-result isolation.
- Caller disconnect followed by safe request recovery.
- No outbound network connectivity.
- No synthetic payload values in service logs.
- Clean Compose shutdown.

## 16. Cleanup

Stop the VS Code-launched development service:

```text
Ctrl+C in the VS Code integrated terminal running Uvicorn
```

## 17. Gate 2 Decision

**Status: PASSED — 2026-09-09**

The human reviewer explicitly accepted the Gate 2 test results after all tests
passed.

Gate 2 passes only when the designated human reviewer has inspected the results
above and explicitly accepts:

- The block/redact/no-match contract.
- Request-local mapping isolation and exact restoration.
- Safe failures and cancellation/recovery behavior.
- No content store or sensitive log leakage.
- No external detector or runtime network egress.
- The private deployment boundary and resource behavior.

Reviewer approval of the implementation PR does not itself pass Gate 2.
