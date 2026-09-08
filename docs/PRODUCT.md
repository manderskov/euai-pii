# Product

## Purpose

EUAI PII provides trusted applications with local text screening before external
processing. It supports whole-request blocking and reversible replacement of
protected text with opaque placeholders.

## Scope

- Private screening API with block and redact modes.
- Deterministic identifiers and configured patterns.
- Danish person/location NER, subject to measured domain acceptance.
- Request-local replacement mappings returned only to authenticated callers.
- Explicit failure when required screening cannot complete.

The service does not store customer text or mappings, invoke external models, or
own consumer policy inheritance. EUAI conversation integration, saved-history
representation, streaming restoration, and future model-based detectors require
separate specifications.

## Product Alignment

The remote platform vision in manderskov/euai/PRODUCT-VISION.md is the vision
source of truth. The user's subsequent direction adds reversible redaction to
this service. Platform chat adoption requires the separate alignment and
integration work recorded in F-007. Do not copy or modify the remote vision here.

## Features

| ID | Feature | Description |
| --- | --- | --- |
| F-007 | [Screening Service](features/F-007-screening-service.md) | Private blocking or reversible redaction with deterministic guards and Danish NER. |

F-007 retains its original EUAI platform planning identifier after transfer from
euai-api. Do not renumber it or duplicate its authoritative definition there.

## Ownership

This repository is the source of truth for screening-service requirements.
The consuming EUAI API owns authentication of its end users, effective customer
policies, model/tool authorization, and conversation lifecycle.
