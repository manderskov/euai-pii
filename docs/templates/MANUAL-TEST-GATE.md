# F-###-G-## — Feature Name — Gate Name

> LLM instructions: Replace every placeholder before saving a real gate plan. Make the plan executable by a human who has repository access but no hidden setup knowledge. Use safe placeholders, never real secrets or sensitive data.

## Gate Definition

- **Owning feature:** [F-### — Feature Name](../../features/F-###-feature-name.md)
- **Technical specification:** [F-### technical specification](../../specs/F-###-feature-name.md)
- **Pass authority:** Name the user or designated human role.
- **GitHub result source:** Link the implementation pull request or dedicated gate issue, or state when it will be assigned.

## Purpose

State the material behavior, boundary, or risk this gate validates and why human verification is required in addition to automated tests.

## Coverage

| Requirement or Risk | Test Cases |
| --- | --- |
| `F-###-FR-001` | `F-###-G-##-TC-001` |
| Concise technical or security risk | `F-###-G-##-TC-002` |

Every applicable functional requirement and material manual-only risk must be covered. Do not duplicate deterministic automated coverage unless a deliberate smoke or end-to-end check is required.

## Entry Criteria

- List the implementation issues and pull requests that must be complete.
- Require Reviewer approval for the exact target under test.
- List required cross-repository changes, infrastructure, access, or explicit authorizations.
- State any condition that must prevent testing from starting.

## Test Target

The execution record must identify the exact values used:

| Item | Required Value |
| --- | --- |
| Application commit/build/deployment | Exact immutable identifier |
| Related repositories | Exact commit/build identifiers, or `None` |
| Test-plan revision | Commit containing this plan |
| Environment | Named non-production environment |

## Prerequisites and Configuration

### Required Software and Access

List required runtimes, package managers, Docker or other tools, Postman, accounts, network access, and permissions. State how to verify each prerequisite without exposing secrets.

### Configuration

| Setting or Variable | Component | Required | Sensitive | Safe Value or Source |
| --- | --- | --- | --- | --- |
| `VARIABLE_NAME` | Component name | Yes/No | Yes/No | Safe example or where the tester obtains it |

Never include real secrets. Sensitive Postman values belong in local current values only and must not be exported or captured in evidence.

### Test Data

Describe the synthetic accounts, tenants, records, files, prompts, identifiers, and fixtures required. Include exact creation or seed steps and identify values that each case stores for later requests.

## Start and Verify the System

List commands in execution order. Use exact verified commands and working directories; do not invent commands from framework conventions.

| Order | Component | Working Directory | Command | Ready When |
| --- | --- | --- | --- | --- |
| 1 | Dependency or service | Repository path | Exact command | Observable readiness result |
| 2 | Application | Repository path | Exact command | Health URL, log message, or other safe check |

Include required dependency installation, build, migration, seed, and startup commands. State which commands remain running and which require separate terminals.

## Postman Setup

Create or select a local Postman environment with the variables required by this gate:

| Variable | Initial / Safe Example | Current Value Source | Sensitive |
| --- | --- | --- | --- |
| `base_url` | `http://localhost:3000` | Started application | No |
| `access_token` | Leave empty | Authorized test credential source | Yes |

State any collection, folder, request naming, certificate, proxy, timeout, redirect, or streaming settings required. Do not require a committed Postman collection unless the repository explicitly maintains one.

## Automated Evidence Required

List the exact automated commands and results that must already be available from the Developer and Reviewer. These are prerequisites, not substitutes for the manual steps below.

## Test Cases

### F-###-G-##-TC-001 — Test Case Name

**Covers:** List functional requirement IDs and material risks.

**Setup:** State additional case setup, or `Use the common gate setup with no additional preparation.`

**Postman request**

- **Name:** Suggested request name.
- **Method:** HTTP method.
- **URL:** `{{base_url}}/path`
- **Authorization:** Exact Postman authorization type and variable.
- **Headers:** List required headers and variable values.
- **Body:** Provide a complete safe request body, or state `None`.

For a non-API review case, replace the Postman request fields with the exact manual inspection or interaction to perform.

**Steps**

1. Provide exact actions in order.
2. Include follow-up Postman requests or inspections needed to verify persisted or asynchronous outcomes.

**Expected results**

- State the expected status, response fields, event order, visible behavior, and prohibited behavior.
- Attach expected results to individual steps when ambiguity is possible.

**Evidence**

State the sanitized screenshots, response excerpts, request IDs, logs, or observations to capture. Never capture credentials, tokens, secret configuration, or unnecessary sensitive content.

**Cleanup:** State case-specific cleanup, or `Covered by common cleanup.`

Duplicate the test-case section for each required case.

## Pass Criteria

- Every required test case passes against the recorded target.
- No required case is skipped.
- No unresolved result contradicts the feature, specification, or security and privacy requirements.
- Required sanitized evidence is attached to the GitHub result source.
- Only the designated pass authority records the overall `PASS`.

## Failure, Retest, and Invalidation

On failure, keep the gate unpassed, record the failing case and evidence in GitHub, and return corrective implementation work through the relevant pull request or issue. After correction and Reviewer approval, rerun the affected cases plus the regression cases identified by this plan.

A passing result becomes stale when a later change affects covered behavior, configuration, infrastructure, test data, related repository integration, or this procedure. Record the invalidation in the GitHub result source and rerun the affected scope before dependent work continues.

## Shutdown and Cleanup

Provide exact commands and steps to stop applications, remove synthetic data, revoke temporary credentials, and return retained test infrastructure to its approved idle state. Do not prescribe destructive cleanup without explicit authorization and an exact safe target.

## GitHub Execution Record

Copy this structure into the gate's GitHub result source for each run:

```markdown
**Gate:** F-###-G-##
**Overall result:** PASS | FAIL
**Test target:** commit/build/deployment
**Related targets:** commits/builds or None
**Test-plan revision:** commit
**Environment:** name
**Tester:** designated human
**Date:** YYYY-MM-DD

| Test Case | Result | Evidence | Notes |
| --- | --- | --- | --- |
| F-###-G-##-TC-001 | PASS/FAIL | Sanitized link or excerpt | None |

**Deviations or skipped cases:** None
**Residual risks:** None
```
