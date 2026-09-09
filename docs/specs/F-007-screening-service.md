# F-007 — Screening Service — Technical Specification

## Source Feature

[F-007 — Screening Service](../features/F-007-screening-service.md)

## Technical Summary

Status: documentation baseline accepted for euai-pii. Presidio, the private standalone API, and block/redact modes are user-selected direction. The stack is summarized in ../SPECS.md; detector/profile acceptance and exact dependency compatibility remain subject to the gates below.

One Python service embeds Presidio Analyzer and Anonymizer libraries behind a small FastAPI/Pydantic API. Use a single container, not separate analyzer, anonymizer, and wrapper services. The service holds loaded recognizers/models in memory and stores no customer content. No model-provider credentials, database, queue, or public ingress are needed.

Flow: authenticate → validate request/profile → detect required categories → resolve protected spans → block or replace → return one complete response. EUAI remains responsible for its own effective tenant/user/Assistant policy and external-call authorization. This service executes an authorized screening profile; it does not implement EUAI's configuration hierarchy.

## Technical Decisions

- **Decision:** Python with FastAPI, Pydantic, Presidio Analyzer/Anonymizer, spaCy, pytest, and one CPU Linux container. **Reason:** use Presidio's native libraries with a typed HTTP contract. **Constraint:** pin compatible runtime, package, model, and image versions in the service's lock/build artifacts before acceptance; no floating model downloads at runtime. FastAPI is proposed for this service only; EUAI remains TypeScript/Fastify.
- **Decision:** Profiles are immutable, server-controlled configuration selected by ID. **Reason:** raw HTTP clients must not disable checks or inject regex/model configuration. **Constraint:** credentials authorize profile IDs; the profile authorizes modes. Unknown/unauthorized profiles deny without revealing their existence. The trusted application decides which authorized profile applies; this cannot replace EUAI policy resolution.
- **Decision:** All accepted findings in a profile receive the requested mode's action. **Reason:** keep two modes simple. **Constraint:** mixed per-category allow/block/redact precedence is outside v1. Enabled categories are protected; unavailable required recognizers are an error, not an empty result.
- **Decision:** Propose `da_core_news_md` for Danish NER. **Reason:** CPU-oriented spaCy pipeline with native Presidio integration. **Constraint:** benchmark it on our domain; it is a statistical detector, not a deterministic or guaranteed privacy classifier. Its published model license is CC BY-SA 4.0, distinct from library licenses. Record attribution and obtain license acceptance before selecting a distributable model artifact. Do not infer package compatibility from an old model card.
- **Decision:** Use random opaque tokens plus a request-local mapping. **Reason:** exact reversible substitution without a secret database or embedding original values in tokens. **Constraint:** no hashing-as-anonymization claim, fuzzy entity linkage, cross-request identity, or reversible encryption token format.
- **Decision:** Complete JSON responses only. **Reason:** no partially screened text can escape. **Constraint:** timeout, overload, malformed recognizer output, or transformation failure yields no text/mapping.

### Verified sources and limitations

Checked 2026-09-08:

- [Presidio language integration](https://presidio.dataprivacystack.org/tutorial/05_languages/): configure both NLP engine languages and recognizers; loading a Danish model alone does not make every recognizer Danish-aware.
- [Supported entities](https://presidio.dataprivacystack.org/supported_entities/): email, telephone, IBAN, and credit-card recognizers exist; the published list does not list Danish CPR/CVR.
- [Danish spaCy pipelines](https://spacy.io/models/da) and [model card](https://huggingface.co/spacy/da_core_news_md): CPU-oriented news-domain model, Danish entities, CC BY-SA 4.0. Published general-domain results do not validate Danish tenant correspondence.
- [Presidio pseudonymization example](https://presidio.dataprivacystack.org/samples/python/pseudonymization/): custom operators can maintain mappings. Our mapping must be request-local, including under concurrency.
- [Presidio Anonymizer](https://presidio.dataprivacystack.org/anonymizer/): supports custom replacement operators and overlapping detections. Our explicit overlap contract below takes precedence over version-dependent default overlap behavior.
- [FastAPI](https://fastapi.tiangolo.com/features/): Pydantic validation and OpenAPI generation support the proposed contract. Validation errors must be replaced with safe envelopes; do not return submitted values.

### Initial proposed recognizers

| Category | Mechanism | v1 behavior |
| --- | --- | --- |
| `DK_CPR` | Custom deterministic recognizer | Ten ASCII digits, either contiguous or six plus optional supported separator plus four; validate day/month plausibility without requiring modulus 11. |
| `DK_CVR` | Custom deterministic recognizer | Eight digits with explicit `CVR` or `DK` prefix, case-insensitive; standalone eight-digit values are not claimed as CVR coverage in v1. |
| `EMAIL_ADDRESS` | Presidio built-in | Configure for Danish profile and verify with Danish sentences. |
| `PHONE_NUMBER` | Presidio phone recognizer | Explicit Denmark region configuration, test national and `+45` forms. |
| `IBAN_CODE`, `CREDIT_CARD` | Presidio built-ins | Preserve their validation; test accepted formats and false positives. |
| `CONFIGURED_PATTERN` | Trusted literal/regex recognizers | Versioned configuration, compiled at startup; no request-supplied expressions. |
| `PERSON` | Danish NER | Explicit `PER`/`PERSON` mapping verified against the selected artifact's labels. Does not distinguish public from private people. |
| `LOCATION` | Danish NER | Explicit `LOC`/`GPE`/`LOCATION` mapping where labels exist. May identify cities; does not promise complete street addresses. |

Ignore `ORG` and `MISC` in the proposed first NER profile; organizations are not automatically treated as people. Reject unknown configured labels at startup. NER recognizer scores are engine scores, not calibrated probabilities. Profile thresholds are pinned server configuration and validated against Gate 1; never expose adjustable thresholds in HTTP requests.

Proposed profiles: `da-identifiers-v1` includes the structured/pattern categories above; `da-personal-v1` adds PERSON and LOCATION. Both permit block/redact. A deployment must explicitly provision profiles and credentials; no permissive default profile. These IDs describe service capability, not an approved customer policy.

CPR separators: absent, a single ASCII hyphen, or a single U+2010/U+2011 hyphen, space, or nonbreaking space between the six/four digit groups. Boundaries reject neighboring Unicode decimal digits. Date plausibility accepts DD/MM in either possible century, including 29 February where possible. No live identifier registry lookup. Add fixtures for these rules, invalid dates, and embedded longer numbers. Unsupported obfuscation remains a documented limitation.

Do not normalize the returned text. Detector normalization, if used, must preserve a verified index map to the original text; prefer recognizers that directly match supported source formats. Literal patterns use documented case-sensitive or Unicode case-insensitive matching as specified in configuration. Regex compilation must be bounded and screening must run in a killable worker, so pathological trusted patterns cannot wedge the HTTP service.

## Affected Areas

Implementation repository: https://github.com/manderskov/euai-pii. Proposed service-owned areas are HTTP contract, profile configuration, recognizer setup, span replacement, worker lifecycle, container packaging, and tests. Do not add Python dependencies to EUAI's package.json.

This repository owns the standalone screening service and its documentation. EUAI API F-006 and public API behavior remain authoritative in manderskov/euai-api until a separately approved integration changes them.

## Data and State Changes

No database, migration, persisted mapping, or cross-request content cache. Model weights and trusted profiles are static deployment assets. Original text, findings, and mappings exist only while processing a request and delivering its response. Python memory release is not a guarantee of cryptographic erasure.

The caller owns mapping lifetime after receiving it and must bind it to its own tenant/user/operation. Transport loss means the mapping is lost; a repeated request produces new keys. v1 has no idempotent mapping recovery or session reuse.

## Interfaces and Contracts

### POST /v1/screen

Require `Authorization: Bearer <service-credential>` and `Content-Type: application/json`. Accept only:

```json
{
  "mode": "redact",
  "profile_id": "da-personal-v1",
  "language": "da",
  "text": "Skriv til Anna Jensen."
}
```

`mode` is required and is `block` or `redact`. `profile_id` is required, 1–128 ASCII letters/digits/underscore/hyphen. `language` is required and only `da` is supported in v1; mixed-language recall is not guaranteed. Text is a nonempty Unicode string. Reject unknown fields, invalid Unicode scalar sequences, and text containing the reserved prefix `[[EUAI_PII_`. No silent coercion, truncation, HTML extraction, URL fetching, or recursive JSON scanning.

Proposed limits: 100,000 Unicode code points per text; 1 MiB raw request body; 10,000 resolved spans; 2 MiB serialized response. Exceeding any limit fails without partial output. Count code points consistently; this differs from JavaScript UTF-16 `.length`. Body limits apply while reading chunked bodies, not only to Content-Length.

HTTP 200 is a successfully completed screening decision, including `blocked`. Common required fields: `schema_version: 1`, `request_id` (server UUID), `screening_id` (fresh server UUID), `profile_id`, and `screening_version` (SHA-256 of canonical profile, recognizer versions, dependency/model artifact identities, thresholds, and normalization rules). Responses are discriminated by `action`:

```json
{
  "schema_version": 1,
  "request_id": "880c8c24-40fd-4b41-8035-7f5088845080",
  "screening_id": "32c7fced-280d-463b-932d-0f409518931b",
  "profile_id": "da-personal-v1",
  "screening_version": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
  "action": "redacted",
  "text": "Skriv til [[EUAI_PII_3b093b39f7804fa4acafde6213c304d1]].",
  "replacements": [
    {
      "key": "[[EUAI_PII_3b093b39f7804fa4acafde6213c304d1]]",
      "value": "Anna Jensen",
      "entity_types": ["PERSON"]
    }
  ]
}
```

Example values are synthetic contract illustrations, not model-output claims.

- `allowed`: no accepted protected findings, original text unchanged, `replacements: []`.
- `blocked`: at least one accepted protected finding in block mode; OMIT `text` and `replacements`. Include only common fields, `action: "blocked"`, and `code: "protected_content"`.
- `redacted`: protected findings in redact mode; include transformed text and mapping. No score, raw findings, or offsets on the wire.

HTTP success never means that all possible sensitive information was detected. The caller must inspect `action`, not just status 200. Existing EUAI 422/503 public errors are a different contract and are not changed by this service.

Every response includes matching `x-request-id` and `Cache-Control: no-store`. Ignore caller-provided correlation values; callers can associate the returned UUID locally. Do not allow a request identifier to become a payload log channel.

### Span and token algorithm

1. Validate every recognizer result: known category, finite score in [0,1], integer original-text offsets with `0 <= start < end <= len(text)` in Unicode code points. Invalid results fail screening.
2. Retain protected findings at or above their profile's category threshold. A deterministic match cannot be dismissed by a negative NER result.
3. Deduplicate identical spans; merge transitively overlapping protected intervals by union, retaining sorted category sets. Adjacent intervals remain separate. Never discard a crossing span in a way that leaves part of a detected value exposed.
4. For each resulting original-text substring, allocate a CSPRNG UUIDv4 token in the format shown above. Reuse the token for exact, case-sensitive identical substrings within this request; union their entity types. Do not equate spelling/format variants or infer two names are the same person. Check every generated token against input and previously generated keys; regenerate on collision.
5. Replace resolved spans without rescanning inserted tokens. Preserve untouched text exactly. Return one mapping entry per token in first-occurrence order. No empty values, unused keys, duplicate keys, or original protected substrings in place of tokens at resolved positions.
6. Use a request-local Presidio anonymizer operator/mapping, with a conformance test proving the overlap and exact reconstruction rules; do not use a process-global sample mapping or rely on default anonymizer merging.

### Caller restoration contract

No restoration endpoint in v1. The trusted caller holds the mapping and performs a single-pass, exact, nonrecursive replacement of recognized tokens in the final model output. Never interpret original text values as HTML, code, URLs to fetch, or new tokens. Unknown/modified reserved tokens cause restoration to fail for review; do not guess their intended values. Known tokens may be repeated/reordered. Missing tokens do not imply an error: the model may choose not to use every entity.

Restoration proves token lookup, not semantic correctness or authorization. The model can associate a valid token with the wrong statement; consequential outputs still need caller-specific review. Mappings must never reach the model. Restored values must not enter later model context, tool parameters, traces, or memory unless separately screened and authorized. Multi-turn reuse, buffered/streaming response handling, and saved-history representation must be designed in the later EUAI integration specification. Input rejection of the reserved prefix intentionally makes already-tokenized continuations unsupported by this v1 contract.

### Failures and health

Safe error envelope: `{"error":{"code":"screening_unavailable","message":"Screening could not complete.","request_id":"<server-uuid>"}}`. Static messages only; never serialize exception strings, Pydantic input details, stack traces, patterns, or matched text.

| Status | Code | Meaning |
| --- | --- | --- |
| 400 | `invalid_request` | Malformed/invalid input, unsupported language, or reserved token prefix |
| 401 | `unauthorized` | Missing/invalid credential |
| 403 | `screening_not_authorized` | Unknown/unauthorized profile or disallowed mode |
| 413 | `screening_limit_exceeded` | Input/span/output bounds exceeded |
| 415 | `unsupported_media_type` | Non-JSON input |
| 503 | `screening_unavailable` | Timeout, worker failure, missing required detector, or saturation |
| 500 | `internal_error` | Unexpected wrapper failure; no result |

`GET /health/live`: minimal 200 when HTTP process is alive. `GET /health/ready`: 200 only after worker/model/profile startup checks succeed; otherwise 503. Health routes are internal-only, unauthenticated, and disclose no profile/model inventory. Authenticate exported OpenAPI schema; disable interactive docs in deployed service.

## Security and Privacy

- Use TLS for cross-host traffic; the test and production host ports are private LAN interfaces and require network restrictions in addition to application authentication. Development may use HTTP on the local network.
- Credentials map to allowed profiles in trusted configuration. Constant-time credential comparison; secrets and profile configuration excluded from errors/access logs.
- Model/tokenizer assets are installed during build/provisioning. Deny runtime outbound network access, including telemetry and automatic model downloads.
- Disable body logging, request capture, diagnostic tracing, crash dumps, and content-bearing metrics. Allow only server correlation ID, fixed outcome code, duration, and non-content operational counters.
- Recognizers/models may be reused; text, replacement maps, and operator mutable state may not be shared between requests. Test simultaneous clients and cancellation.
- Validate configuration at startup, including duplicate rule IDs and missing recognizers/language mappings. No fallback to English or rule-only screening when NER is required.

## Infrastructure Changes

- **Infrastructure:** one private CPU Linux container with HTTP parent and one preloaded screening worker. **Purpose:** isolate Presidio runtime and permit termination of a stuck inference/regex call. **When:** implementation and container tests. **Manual action:** approve the deployment host before provisioning; the repository is euai-pii.
- **Infrastructure:** private network and service credentials, read-only model/config assets, nonroot process, memory/CPU limits. **Purpose:** protect unscreened data. **When:** before integration tests/deployment. **Manual action:** operator provisions credentials and network restrictions; no real customer data required.
- Proposed scheduling: one active request, no application backlog; reject excess with 503. A 10-second processing deadline kills/restarts the worker on expiry; readiness stays false until warmup completes. HTTP health must stay responsive. Bound shutdown and discarded-result behavior after caller disconnect. Benchmark before expanding concurrency.
- No PostgreSQL, LLM provider, GPU, or model-training service is required by the baseline.

## Environment Variables

| Variable | Purpose | Component | Required | Sensitive | Example / Format |
| --- | --- | --- | --- | --- | --- |
| `SCREENING_PORT` | Internal HTTP port | Screening service | No; default 8080 | No | `8080` |
| `SCREENING_CONFIG_PATH` | Read-only profiles/rules manifest | Screening service | Yes | Yes; rules may be confidential | `/run/config/screening.json` |
| `SCREENING_CREDENTIAL` | Bearer credential for configured profiles and modes | Screening service | Yes | Yes | `generated 256-bit secret` |

Model identity, artifact hashes, thresholds, and limits are versioned in configuration/build artifacts, not arbitrary per-request overrides. No new EUAI environment variables in this standalone specification; consumer configuration belongs to later integration work.

## Implementation Plan

Proposed sequence only; no implementation begins before resolving design decisions below.

### Step 1 — Validate Danish detection baseline

**Assigned skill:** `backender`

**Objective:** verify model/package compatibility and recognizer behavior.

**Changes:** in the approved service repository, establish pinned Python/Presidio/spaCy/model dependencies and synthetic Danish evaluation fixtures. Configure explicit Danish recognizers and NER label mapping. Implement/test CPR/CVR and trusted pattern rules.

**Constraints:** local CPU inference; no customer data or remote detection. Record model license and exact artifact identity. Evaluate rule-only and rule-plus-NER independently.

**Verification:** supported identifier fixtures and safe lookalikes; at least 200 held-out synthetic Danish texts balanced between protected and allowed examples, including names/locations, short messages, property correspondence, punctuation, æ/ø/å, and mixed-language failure cases. Report per-category recall/precision, missed-span examples, and message-level false-block rate. Separate tuning data from held-out data. Record warm/cold latency and RSS on named hardware for 1k/10k/100k-character inputs; include maximum-request timeout behavior. Do not claim measured results in advance.

**Expected result:** reproducible evidence and thresholds submitted to Gate 1.

### Step 2 — Implement private screening contract

**Assigned skill:** `backender`

**Objective:** expose one authenticated block/redact API.

**Changes:** implement strict schemas, profile authorization, worker deadline/saturation behavior, union-overlap replacement, request-local mappings, and safe errors/health. Generate OpenAPI and client-facing contract examples.

**Constraints:** Gate 1 passed; no persistent content, raw findings endpoint, or default public Presidio routes.

**Verification:** every status/action variant; overlapping/transitive spans; repeated values; emoji/code-point indexing; reserved-token collisions; exact reconstruction; credential isolation; concurrent requests; limits; missing model; worker crash/timeout; logs and errors inspected for synthetic secret leakage.

**Expected result:** service contract passes deterministic automated tests with real and fake detector boundaries.

### Step 3 — Package and verify standalone consumption

**Assigned skill:** `backender`

**Objective:** deliver the independently deployable service and evidence for integration.

**Changes:** build nonroot image with preinstalled artifacts; private-network example configuration and runbook; standalone TypeScript contract harness using synthetic HTTP requests. Document modes, supported categories, limitations, mapping ownership, and restoration examples.

**Constraints:** do not modify EUAI application routes or persist mappings. No real infrastructure deployment implied.

**Verification:** offline container startup; no egress; readiness recovery; deadline behavior; clean shutdown; TypeScript caller distinguishes 200 blocked from allowed and never forwards replacement values; exact nonrecursive restoration harness tests.

**Expected result:** Gate 2 evidence and reviewable service PRs; EUAI integration remains separately gated.

## Manual Test / Review Gates

### Gate 1 — Danish detector and model acceptance

**After step(s):** Step 1.

**Review / test:** Principal Architect reviews license/artifact selection, actual mislabeled Danish examples, per-category thresholds, message-level false blocks, and measured latency/memory. All specified deterministic positive/negative fixtures must pass. NER has no assumed production accuracy target: the user must explicitly accept the observed quality or require a revised model/profile before continuing.

**Expected result:** an explicitly accepted model/profile and resource budget, with no unsupported claim of full address or sensitive-narrative detection.

**Blocks:** Steps 2 and 3.

### Gate 2 — Service contract and privacy boundary

**After step(s):** Steps 2 and 3.

**Review / test:** demonstrate block/redact/no-match cases, independent-request tokens, mapping restoration, and safe failures using synthetic data and the private container.

**Expected result:** caller can consume the contract without exposing original values to a model; runtime has no content store or outgoing detector request.

**Blocks:** production exposure and any EUAI integration implementation.

## Implementation Issues

| Plan Step | Assigned Skill | GitHub Issue | Status Source |
| --- | --- | --- | --- |
| Step 1 | `backender` | [#1 — Validate Danish detection baseline and lock artifacts](https://github.com/manderskov/euai-pii/issues/1) | GitHub |
| Step 2 | `backender` | [#2 — Implement authenticated block and redact screening API](https://github.com/manderskov/euai-pii/issues/2) | GitHub |
| Step 3 | `backender` | [#3 — Package service and verify standalone TypeScript consumption](https://github.com/manderskov/euai-pii/issues/3) | GitHub |

Issue #1 produces the evidence required for Gate 1. Issue #2 depends on Gate 1 and produces the service contract required for Gate 2. Issue #3 depends on issue #2 and Gate 2. Each issue requires its own branch/PR and independent Reviewer approval; approval does not authorize merge or deployment.

## Completion Criteria

- Both modes and no-match behavior follow the discriminated contract; failures return no text/mapping.
- Required detectors run locally and use pinned, accepted artifacts/configuration.
- Defined supported Danish identifier fixtures pass and NER evidence is accepted at Gate 1.
- Overlap handling, exact reconstruction, isolation, limits, cancellation, and logging tests pass.
- Private container and TypeScript contract harness pass Gate 2.
- Each implementation issue has independent Reviewer approval and documentation is current.
- No claim that EUAI chat redaction, saved-history restoration, or GDPR compliance is completed by this service.

## Open Technical Questions

These block implementation-ready status, not the present draft:

- Repository and issue destination resolved: manderskov/euai-pii; retain F-007 for platform traceability.
- Principal Architect approval of FastAPI/CPU-worker design, initial profiles, request limits, and NER baseline/license. Exact compatible release pins are established by Step 1 before packaging, with no model-family substitution by the developer.
- Product-vision alignment and EUAI redaction/history/tool integration are separate prerequisites for consuming this service in production chats.
