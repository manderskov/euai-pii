# F-### — Feature Name — Technical Specification

> LLM instructions: Replace all placeholders before saving a real specification. This document is the durable technical source of truth for the feature. It must be detailed enough for a developer using a less capable model to implement the approved solution without redesigning it.

## Source Feature

Link to the corresponding feature definition:

`../features/F-###-feature-name.md`

Use the same feature ID and feature name as the Product Owner feature.

## Technical Summary

Describe the chosen technical solution concisely.

Explain:
- The main components involved.
- How the feature fits the existing architecture.
- The main technical flow from input to outcome.

Do not write an alternatives catalogue. Document the approved solution.

## Technical Decisions

Document feature-specific technical decisions developers must follow.

For each material decision, state:
- **Decision:** What was chosen.
- **Reason:** Why it was chosen.
- **Constraint:** Any important verified limitation or rule developers must preserve.

Only include decisions that materially affect implementation.

## Affected Areas

Identify the existing product areas expected to change.

Use repository paths when known.

Include relevant:
- Applications.
- Modules.
- Components.
- Services.
- Shared packages.
- Interfaces.
- Data stores.
- Configuration.

Do not list files speculatively when the repository structure has not been verified.

## Data and State Changes

Describe required changes to persisted data, schemas, migrations, state, caching, or data lifecycle.

Be explicit about:
- New or changed data.
- Ownership.
- Migration requirements.
- Backward compatibility when relevant.

If no data or state changes are required, state:

No data or state changes required.

## Interfaces and Contracts

Describe every interface or contract introduced or changed by this feature.

Include when relevant:
- APIs.
- Request and response shapes.
- Events.
- Shared types.
- Schemas.
- Integration contracts.
- Error behavior.
- Compatibility requirements.

Define contracts precisely enough that separate developer workers can implement interacting parts independently.

If no interface changes are required, state:

No interface or contract changes required.

## Security and Privacy

Describe security and privacy behavior introduced or affected by the feature.

Include when relevant:
- Authentication.
- Authorization.
- Input validation.
- Trust boundaries.
- Sensitive data.
- Secret handling.
- Logging or auditing.
- External access.

Do not use generic security boilerplate. State concrete requirements developers must implement or preserve.

If the existing security model is sufficient, state that explicitly.

## Infrastructure Changes

List infrastructure that must be created, changed, configured, or made available before or during implementation.

For each required change, state:
- **Infrastructure:** What is needed.
- **Purpose:** Why the feature needs it.
- **When:** Before implementation, during implementation, before testing, or before deployment.
- **Manual action:** What the user or operator must do, if anything.

Examples:
- Databases.
- Queues.
- Storage.
- External services.
- Cloud resources.
- Containers.
- DNS.
- Reverse proxies.
- Certificates.
- Network access.
- Runtime services.

If no infrastructure changes are required, state:

No infrastructure changes required.

## Environment Variables

List every new or changed environment variable.

Use this format:

| Variable | Purpose | Component | Required | Sensitive | Example / Format |
| --- | --- | --- | --- | --- | --- |
| `VARIABLE_NAME` | Why it exists | Component using it | Yes/No | Yes/No | Safe example or format |

Never include real secrets.

If no environment-variable changes are required, state:

No environment-variable changes required.

## Implementation Plan

Provide the approved step-by-step implementation sequence.

Each numbered step must contain:

### Step N — Short Objective

**Assigned skill:** Name the developer skill expected to execute this work.

**Objective**

State the concrete result this step must produce.

**Changes**

Describe precisely what must be implemented.

Identify relevant areas or repository paths when known.

**Constraints**

State technical decisions, contracts, security requirements, or architectural boundaries the developer must preserve.

**Verification**

Define automated tests, checks, or observable results required for this step.

**Expected result**

State what must be true when the step is complete.

Rules:
- Put dependencies before dependent work.
- Keep steps small enough to implement and verify coherently.
- Do not combine unrelated work into one step.
- Do not leave architecture decisions for the developer to make.

## Manual Test / Review Gates

Insert gates only between major implementation stages where human validation materially reduces risk.

Use this format:

### F-###-G-## — Short Name

**After step(s):** Identify the implementation steps that must be complete.

**Purpose**

State the material risk or assumption this human gate validates.

**Test plan**

Link to the executable plan under `../tests/F-###-feature-name/G-##-short-name.md`.

**Pass authority**

Name the user or explicitly designated human role permitted to pass the gate.

**Blocks**

State which later implementation step or steps must not begin until this gate passes.

**Result source**

Link the implementation pull request that will record the result. Use a dedicated gate issue only when the gate spans multiple pull requests or repositories, occurs after merge, blocks multiple independent work items, or represents final end-to-end acceptance. If the result source has not been created, state that it will be assigned with the implementation issues.

Do not add a gate after every trivial step.

Create every linked test plan from `docs/templates/MANUAL-TEST-GATE.md` before creating implementation issues. The specification owns why and when the gate occurs; the test plan owns how it is executed; GitHub owns the execution result and current status. Do not duplicate detailed test cases in this specification.

If no formal manual gate is justified, state that no manual gate is required; independent Reviewer approval still applies. If final human acceptance is required, define it as a formal gate with the same complete test plan and tracking rules.

## Implementation Issues

Map the implementation plan to the GitHub issues created for developer execution.

Use this format:

| Plan Step | Assigned Skill | GitHub Issue | Status Source |
| --- | --- | --- | --- |
| Step 1 | `backender` | #123 — Issue title | GitHub |
| Step 2 | `frontender` | #124 — Issue title | GitHub |

Rules:
- Use only `developer`, `frontender`, or `backender` as the assigned implementation skill.
- The assigned skill must match the implementation-plan step and GitHub issue.
- GitHub is the source of truth for issue status. Do not copy open/in-progress/done status into this file.
- Each implementation issue normally uses one issue-specific branch and one pull request.
- Later issues must identify blocking gates by stable gate ID and link their GitHub result source.
- The Developer is authorized by this workflow to create/switch to that branch, commit issue-scoped work, push the branch, and open/update the pull request.
- The pull request must reference its implementation issue and should use `Closes #<issue-number>` when merge should close it.
- When the pull request is ready, the Developer automatically starts a separate Reviewer execution. On `RETURN`, it may make and re-submit up to three authorized correction attempts, stopping earlier for findings outside its scope or authority or requiring human input.
- Reviewer feedback and approval status are normally recorded in pull request reviews/comments.
- Use implementation issue comments for review only when a pull request genuinely cannot or should not be created.
- Do not copy branch state, pull request state, review findings, or review status into this specification.
- Do not require the user to relay Reviewer findings between skills.
- Add issue references after the Tech Lead creates the implementation issues.
- Keep the mapping synchronized if issues are replaced, split, or merged.
- Do not duplicate the issue body here.

If implementation issues have not yet been created, state:

Implementation issues not yet created.

## Completion Criteria

Define what must be true for the complete feature implementation to be considered done.

Include:
- Required functional behavior is implemented.
- Required automated tests pass.
- Each implementation issue has received independent Reviewer approval.
- Required manual gates have passed.
- Security and validation requirements are satisfied.
- Required infrastructure and configuration are in place.
- Required documentation is updated.

Add feature-specific completion conditions where needed.

## Open Technical Questions

List only unresolved technical questions that do not prevent safe implementation from starting.

Do not leave architecture, security, contract, infrastructure, or product decisions unresolved here when developers would need to make those decisions themselves.

If there are no open technical questions, state:

None.
