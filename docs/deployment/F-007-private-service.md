# F-007 Private Service Runbook

## Image

Build the pinned CPU image from the repository root:

```sh
docker compose build --pull=false
```

The image installs the exact Python/package/model artifacts from
`requirements.lock` during the build. It runs as UID/GID `10001`, drops all
Linux capabilities, uses a read-only root filesystem, and has no runtime model
download path.

## Deployment Profiles

The service supports three deployment profiles. Each profile has its own `.env`
file, credential, port, and Compose project directory:

| Profile | Start method | Directory | Host port |
| --- | --- | --- | ---: |
| Development | VS Code integrated terminal | repository root | 6010 |
| Test | Docker Compose | `~/test/euai-pii` | 6110 |
| Production | Docker Compose | `~/prod/euai-pii` | 6210 |

The screening credential is supplied as `SCREENING_CREDENTIAL` through the
profile's ignored `.env` file. Do not commit `.env` files or credentials.

Development:

```sh
./deploy-dev.sh
```

Test and production deployment directories should contain the corresponding
Compose file and `.env` copied from the templates under `deploy/`:

```sh
./deploy-test.sh
./deploy-prod.sh
```

On the first run, each script creates its deployment directory and `.env` from
the matching template, then exits. Replace the placeholder with a separately
generated credential and run the script again. The test profile may use
synthetic data; production requires an operator-provisioned secret and approved
network access. On later runs, the scripts refresh the Compose file, rebuild the
image, and recreate changed containers without overwriting `.env`.

```sh
cd ~/test/euai-pii && docker compose up -d && docker compose ps
cd ~/prod/euai-pii && docker compose up -d && docker compose ps
```

Stop a profile with `docker compose down --remove-orphans` from its directory.

Test and production are reachable at `http://apex.lan:6110` and
`http://apex.lan:6210`. Cross-host deployments require TLS and network
restrictions in addition to the bearer credential.

## Contract Smoke Test

The container's liveness/readiness endpoints are internal. The OpenAPI schema is
available at `/openapi.json` only with a valid service credential; `/docs` and
`/redoc` are disabled. The configured example profile can be exercised with a
synthetic CPR value from a private-network consumer.

Run the repository smoke checks:

```sh
./scripts/verify_container.sh
```

The smoke script verifies offline image build, readiness, unauthenticated schema
rejection, and blocked outbound connectivity. It does not use customer data.

## Consumer Harness

The TypeScript harness is intentionally separate from EUAI application code:

```sh
cd consumer-harness
npm ci
npm test
```

`screen()` distinguishes `allowed`, `blocked`, and `redacted` responses. Only
transformed text is returned by `modelInput()`, and replacement values remain in
the caller's mapping. `restoreExact()` performs one nonrecursive replacement
pass, permits repeated/reordered known keys and missing keys, and rejects unknown
or modified reserved tokens.

## Gate 2 Evidence

Gate 2 requires a human review of the synthetic container demonstration, mapping
isolation, safe failures, no-content-store behavior, and no-egress behavior. The
implementation and automated harness do not themselves pass that gate. Production
exposure and EUAI integration remain blocked until the gate is explicitly accepted.
