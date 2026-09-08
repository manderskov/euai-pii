# F-007 Detector Baseline

Status: Gate 1 pending. This is a reproducible baseline, not an acceptance
decision or a claim of complete PII detection.

## Run

Environment:

- Python 3.12.3
- Linux x86_64 CPU host
- `presidio-analyzer==2.2.364`
- `spacy==3.8.16`
- `da_core_news_md==3.8.0`

Command:

```sh
.venv/bin/python scripts/evaluate_baseline.py --model da_core_news_md --output artifacts/baseline-report.json
```

The command evaluates 225 deterministic synthetic examples, including Danish
characters, identifiers, names, locations, invalid dates, and prefixed/unprefixed
CVR lookalikes. It also measures 1,000, 10,000, and 100,000 Unicode-character
inputs, starts a fresh spawned detector process for cold-start timing, and runs a
10-second subprocess termination probe. The complete generated JSON report is
intentionally local because its timings and RSS are host-specific.

## Observed Run

| Category | Precision | Recall |
| --- | ---: | ---: |
| `DK_CPR` | 1.000 | 1.000 |
| `DK_CVR` | 1.000 | 1.000 |
| `PERSON` | 0.960 | 0.960 |
| `LOCATION` | 0.706 | 0.960 |

The model labelled several `DK` CVR prefixes as `LOCATION`, labelled one CPR
fixture as `PERSON`, and missed two location fixtures. These are concrete
false-positive and missed-span examples requiring threshold/profile review
before production acceptance. Message-level false blocks in this fixture set: 0.

Observed maximum timings on this host were approximately 12 ms, 91 ms, and
1,010 ms for 1k, 10k, and 100k characters respectively. A fresh spawned process
completed cold startup and processing in approximately 2.31 seconds. Maximum
process RSS was approximately 1.13 GiB. These measurements are baseline
evidence only and do not establish a deployment resource budget. The synthetic
timeout probe terminated the worker at approximately 10.01 seconds and reported
`worker_was_terminated: true`, demonstrating the enforced 10-second process
boundary.

## Acceptance Boundary

Gate 1 still requires review of the model license and attribution, held-out
domain quality, false blocks, thresholds, and resource budget by the Principal
Architect. The baseline does not claim complete street-address detection,
private-person classification, or detection of arbitrary sensitive narratives.
