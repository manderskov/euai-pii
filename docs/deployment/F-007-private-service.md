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

## Local Private Network

The baseline Compose file mounts read-only configuration and credentials,
publishes no host port, and uses an internal Docker network:

```sh
docker compose up -d
docker compose ps
docker compose logs --no-log-prefix screening
docker compose down --remove-orphans
```

Replace the example credential in `config/screening-clients.example.json` through
the operator's secret provisioning process before any non-synthetic use. Do not
commit real credentials or customer text.

The service is reachable only by another container attached to the private
network. Cross-host deployments require TLS and network restrictions in addition
to the bearer credential. The screening port is intentionally not published to
the host.

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
