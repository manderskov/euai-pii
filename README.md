# EUAI PII

Private text-screening service for the EUAI platform, built around Presidio.

The service supports blocking protected content or replacing it with unique,
request-local placeholders while returning the original values separately to a
trusted caller. Danish NER complements deterministic identifier detection.

Status: standalone service implementation and private container are available;
Gate 2 acceptance and production deployment remain pending.

## Documentation

- [Product overview](docs/PRODUCT.md)
- [Technical stack and architecture](docs/SPECS.md)
- [Screening requirements](docs/features/F-007-screening-service.md)
- [Screening technical specification](docs/specs/F-007-screening-service.md)

## Stack

Python, FastAPI/Pydantic, Presidio Analyzer and Anonymizer, spaCy with a Danish NER
 pipeline, pytest, and a private CPU Linux Docker container. The Danish evaluation
 baseline is da_core_news_md; model license acceptance and domain testing are
 required before release. Exact compatible versions are recorded in
 `requirements.lock`.

EUAI API remains a separate TypeScript/Fastify/Mastra application. This repository
does not change its current block-only policy or saved-chat behavior.

## Detector Baseline

Create a Python 3.12 environment and install the pinned service dependencies:

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.lock
.venv/bin/pip install --no-deps -e '.[dev]'
```

Run the deterministic tests and start the development service from VS Code:

```sh
.venv/bin/pytest -q
set -a; source .env; set +a
.venv/bin/uvicorn euai_pii.api:app --host 127.0.0.1 --port 6010
```

The model must be installed during provisioning or image build. The evaluator
reports synthetic quality, missed examples, CPU timing for 1k/10k/100k-character
inputs, and process RSS; it does not download models at runtime. Results from the
current baseline are recorded in `docs/evaluation/F-007-baseline.md` and remain
subject to the Gate 1 acceptance review.

The API requires `SCREENING_CONFIG_PATH` and `SCREENING_CREDENTIAL` at runtime.
Copy `.env.example` to `.env`, generate a local credential, and replace the
placeholder. Deployed interactive documentation and public OpenAPI
routes are disabled; the schema is available only through authenticated
`/openapi.json`.

Deployment profiles and their ports are documented in
[`docs/deployment/F-007-private-service.md`](docs/deployment/F-007-private-service.md).
Use `./deploy-dev.sh` from the VS Code terminal for development, or
`./deploy-test.sh` and `./deploy-prod.sh` to build and update the Docker
deployments.

Container and TypeScript consumer verification instructions are in
[`docs/deployment/F-007-private-service.md`](docs/deployment/F-007-private-service.md).
