# EUAI PII

Private text-screening service for the EUAI platform, built around Presidio.

The service supports blocking protected content or replacing it with unique,
request-local placeholders while returning the original values separately to a
trusted caller. Danish NER complements deterministic identifier detection.

Status: documentation baseline. No application has been implemented or deployed.

## Documentation

- [Product overview](docs/PRODUCT.md)
- [Technical stack and architecture](docs/SPECS.md)
- [Screening requirements](docs/features/F-007-screening-service.md)
- [Screening technical specification](docs/specs/F-007-screening-service.md)

## Stack

Python, FastAPI/Pydantic, Presidio Analyzer and Anonymizer, spaCy with a Danish NER
pipeline, pytest, and a private CPU Linux Docker container. The Danish evaluation
baseline is da_core_news_md; model license acceptance and domain testing are
required before release. Exact compatible versions will be locked during the
first implementation stage.

EUAI API remains a separate TypeScript/Fastify/Mastra application. This repository
does not change its current block-only policy or saved-chat behavior.
