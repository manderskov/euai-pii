# Technical Specifications

## Architecture

EUAI PII is one independently deployable private Python service. Its HTTP parent
authenticates and validates requests; a bounded, preloaded worker executes
Presidio recognizers and optional Danish NER, then blocks or replaces detected
protected spans. Analyzer and Anonymizer are embedded libraries in the same
service, not separate public APIs.

The service returns a discriminated allowed/blocked/redacted response.
Only a redacted response contains a replacement mapping. There is no database,
cross-request content cache, model-provider integration, or restoration endpoint.

The detailed contract and all exceptions are defined in
[F-007](specs/F-007-screening-service.md).

## Technology Stack

| Area | Technology | Purpose / constraint |
| --- | --- | --- |
| Language/runtime | Python 3 | Native Presidio ecosystem; select and lock a supported compatible minor/patch in implementation step 1. |
| HTTP API | FastAPI | Thin private HTTP boundary and generated OpenAPI contract. |
| Schema validation | Pydantic | Strict request/response and configuration validation; suppress content-bearing validation errors. |
| Detection | Presidio Analyzer | Built-in recognizers plus custom Danish CPR/CVR and configured-pattern recognizers. |
| Replacement | Presidio Anonymizer with a custom operator | Opaque keys and request-local mappings; preserve F-007 overlap and reconstruction rules. |
| Danish NLP | spaCy; da_core_news_md evaluation baseline | CPU-oriented person/location NER; explicit Danish recognizer and label configuration. |
| Service tests | pytest | Detector, API, mapping, isolation, worker-failure, and privacy tests. |
| Consumer verification | TypeScript with Node.js HTTP client | Standalone contract harness matching EUAI API consumption; not a second service. |
| Packaging/deployment | Docker, CPU Linux container | Nonroot, private networking, preinstalled models, restricted runtime egress. |
| Local integration | Docker Compose | Reproducible isolated service/consumer verification. |
| API contract | OpenAPI / JSON Schema | Documented versioned request and response contract. |

An ASGI server compatible with FastAPI will be pinned with the dependency set.
Exact package/model/image versions must be recorded in lock/build artifacts
before release; do not use floating latest model downloads at startup.

No GPU, external LLM, PostgreSQL, Redis, vector store, frontend framework, or
message broker is required for the initial service.

## Model and License Constraints

Presidio is MIT-licensed. The published da_core_news_md model uses CC BY-SA 4.0;
its license is distinct from the spaCy library license. Record exact artifact
licenses and attribution, and obtain the model acceptance required by Gate 1.
Danish NER detects general entities, not guaranteed private identities or
complete street addresses. The proposed baseline must pass the domain evaluation
described in F-007.

Sources:
- [Presidio repository](https://github.com/data-privacy-stack/presidio)
- [Danish model card](https://huggingface.co/spacy/da_core_news_md)
- [Presidio language configuration](https://presidio.dataprivacystack.org/tutorial/05_languages/)
- [FastAPI features](https://fastapi.tiangolo.com/features/)

## Shared Security Rules

- Authenticate callers and authorize their screening profiles/modes.
- Keep all detection local; prohibit runtime model downloads and external inference.
- Never log text, mappings, recognizer fragments, credentials, or unsafe exceptions.
- Store mappings only in request-local state; return them exclusively to the caller.
- Fail closed on missing detectors, timeout, malformed output, or saturation.
- Return no partial screening result.
- Keep the screening endpoint private; use TLS for cross-host traffic.
- Keep model weights and configuration immutable for the deployed version.

## Consumer Boundary

EUAI API remains TypeScript/Fastify/Mastra and owns its customer policy hierarchy.
This service does not replace that authority. The caller must inspect the action
field, retain mappings outside model context, and restore only after the final
authorized model operation. Production conversation integration needs a separate
specification for history, tools, streaming, and mapping lifetime.

## Feature Specifications

| Feature | Specification | Summary |
| --- | --- | --- |
| F-007 | [Screening Service](specs/F-007-screening-service.md) | Presidio API, deterministic guards, Danish NER, blocking, and reversible placeholders. |

## Delivery

Implementation issues belong in manderskov/euai-pii. Preserve F-007's detector
acceptance gate before API completion and its service acceptance gate before
consumer integration. Independent Reviewer approval and human gates remain
separate from merge or deployment authorization.

Implementation issues have not been created by this documentation transfer.
