# Manual Test Plans

## Purpose

This directory contains reusable manual test and review procedures for formal feature gates.

The owning feature specification defines why a gate exists, when it occurs, who may pass it, and what it blocks. The gate plan in this directory defines how to prepare and execute it. GitHub records individual executions and current status.

Do not store execution status, real credentials, secret values, production data, or sensitive evidence in these files.

## Structure and IDs

Store one plan per gate:

`docs/tests/F-###-feature-name/G-##-short-name.md`

Use stable IDs:

- Gate: `F-###-G-##`
- Test case: `F-###-G-##-TC-###`

Each gate has exactly one owning feature. Other features link to that gate rather than copying its procedure.

## Test Plan Rules

Create plans from `docs/templates/MANUAL-TEST-GATE.md`.

Every plan must:

- Map its cases to stable functional requirements and material technical risks.
- State the exact entry criteria and automated evidence required before manual work begins.
- Provide all configuration, safe value sources, working directories, commands, startup order, readiness checks, fixtures, and cleanup needed to test.
- Distinguish common gate setup from case-specific setup. Every case must either name its additional setup or explicitly use the common setup unchanged.
- Use Postman for API invocation and provide method, variable-based URL, authentication, headers, body, and expected response details.
- Keep secrets in local environment or Postman current values only. Use safe placeholders in documentation and sanitize evidence.
- Define pass, failure, retest, regression, and invalidation rules.

Only retain manual cases where human validation adds material confidence. Prefer automated tests for deterministic behavior; list those tests as gate prerequisites rather than reproducing all of them manually.

## Execution and Tracking

Normally record a gate run on the implementation pull request it follows. Use a dedicated gate issue only when the gate spans multiple pull requests or repositories, occurs after merge, blocks multiple independent work items, or represents final end-to-end acceptance.

Every run records:

- Gate ID and test-plan revision.
- Exact commit, build, pull request, or deployment tested.
- Environment, tester, and date.
- Result and evidence for every case.
- Deviations, skipped cases, and residual risks.
- Overall `PASS` or `FAIL`.

Only the designated human pass authority may record `PASS`. A later change affecting covered behavior, configuration, infrastructure, data, or procedure makes the result stale until the affected cases and required regression cases pass again.
