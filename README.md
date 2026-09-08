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

## Detector Baseline

Create a Python 3.12 environment and install the pinned service dependencies:

```sh
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/pip install https://github.com/explosion/spacy-models/releases/download/da_core_news_md-3.8.0/da_core_news_md-3.8.0-py3-none-any.whl
```

Run the deterministic tests and the synthetic detector evaluation:

```sh
.venv/bin/pytest -q
.venv/bin/python scripts/evaluate_baseline.py --model da_core_news_md
```

The model must be installed during provisioning or image build. The evaluator
reports synthetic quality, missed examples, CPU timing for 1k/10k/100k-character
inputs, and process RSS; it does not download models at runtime. Results from the
current baseline are recorded in `docs/evaluation/F-007-baseline.md` and remain
subject to the Gate 1 acceptance review.
