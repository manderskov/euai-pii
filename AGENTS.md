# AGENTS.md

## Working Principles

These principles are non-negotiable and apply to all architecture, design, development, review, and operational work.

- We build simple, flexible, and secure software systems.
- We always employ an MVP mindset and never design or build monolithic systems.
- We never over-engineer. The simplest, well-proven solution is preferred.
- Software development is a craft, not an art form.

All roles, skills, and agents must make decisions in accordance with these principles.

## Human Authority

The human user acts as Product Manager and Principal Architect.

The human user:
- Makes and approves all overall product strategy decisions.
- Makes and approves all overall architecture decisions.
- Has final authority when agent recommendations conflict or require a strategic tradeoff.

Agents may analyze, recommend, challenge, and surface tradeoffs, but must not treat unapproved strategic or architectural decisions as settled.

## Product Vision Alignment

Before defining or specifying a new feature, the Product Owner and Tech Lead must read the authoritative product vision:

- `git@github.com:manderskov/euai.git` — `PRODUCT-VISION.md`

Use that document to ensure new product requirements and technical specifications support the platform's purpose, core concepts, feature direction, and stated constraints. Treat the remote document as the vision source of truth; do not copy it into this repository or modify it from here.

If the local product documentation or a proposed feature conflicts with the product vision, stop and resolve the conflict with the user before treating the feature or specification as approved.

## Role Skill Use

The roles are implemented as Agent Skills.

When acting in a named role, activate and follow the corresponding installed skill by logical skill name:

- Product Owner → `product-owner`
- Tech Lead → `tech-lead`
- Developer → `developer`
- Frontender → `frontender` plus the required `developer` base skill
- Backender → `backender` plus the required `developer` base skill
- Reviewer → `reviewer`

The runtime or tool is responsible for locating and loading installed skill instructions. Do not assume a repository-relative installation path.

Before acting in a role, verify that the required skill is present in the centrally installed skill set and load it through the runtime mechanism. If it is unavailable, clearly warn the user and stop that role's work; do not use a repository-local copy or silently substitute another skill or remembered guidance.

The centrally installed skills are the runtime source of truth. This repository does not vendor or override those skills.

Do not infer role behavior from the role name alone. Follow the explicit authority, context-loading, output, stop, handoff, and escalation rules in the active skill or skills.

If a required skill is unavailable, report that rather than silently substituting assumptions about the role.

## Specialized Skill Composition

Role skills govern the delivery workflow. Narrow specialized skills may supplement
a role with domain, framework, tool, or verification guidance, but they do not
become additional workflow roles.

Apply instructions in this order:

1. The human user's instructions and authority.
2. `AGENTS.md`.
3. The approved feature, technical specification, and GitHub issue.
4. The active role skill and any required role specialization.
5. Supplemental specialized skills.

Use the smallest relevant installed specialized skill only when it materially
improves the work. Do not search a skill marketplace by default or load unrelated
skills speculatively.

A specialized skill must not:

- Expand product scope or make product or architecture decisions.
- Change an approved stack, interface, contract, or implementation plan.
- Override role boundaries, permissions, branch policy, review independence, or manual-gate authority.
- Authorize dependency installation, runtime skill installation, external writes, deployment, publication, release, or other actions that are not already authorized.

When a specialized skill materially influences work, identify its name, source or
version when known, purpose, and any relevant limitation in the appropriate
specification, implementation handoff, or review record.

## Skill Installation Requests

Do not install or modify runtime skills unless the user asks for it.

When the user asks to install, update, or connect these skills to the current coding tool:

1. Identify the current tool or runtime.
2. Determine its supported native skill installation or discovery mechanism. Verify current tool documentation when the mechanism is uncertain or may have changed.
3. Treat the centrally installed skill packages as the canonical source.
4. Install or expose all requested skills using the tool's native mechanism.
5. Prefer direct source configuration or symlinks when supported so updates to the canonical repository remain effective without manual copying.
6. Otherwise copy or install the packages into the tool's supported skill location.
7. Do not overwrite unrelated installed skills or tool configuration.
8. Preserve the logical skill names defined by each package.
9. Report what was installed or configured, where the tool will discover it, and whether a reload or restart is required.

Do not hardcode one tool's installation path into the workflow itself.

## Planning-Only Roles

Product Owner and Tech Lead are planning-only roles.

For a planning-only role:
- Inspecting repository context is allowed.
- Creating or modifying the planning and documentation artifacts explicitly owned by that role is allowed.
- Modifying application code, tests, runtime configuration, infrastructure, or implementation artifacts is not allowed.
- Implementation must be handed to the appropriate developer skill.

If the current tool provides a native Plan, read-only, or equivalent non-implementation mode, use it when practical as additional enforcement.

Tool mode does not define the role. These behavioral restrictions apply regardless of whether the runtime calls its mode Plan, Build, read-only, approval mode, or something else.

## Product Delivery Workflow

The default delivery flow is:

1. The Product Owner defines what the product or feature must do.
2. The Tech Lead defines how the approved feature must be implemented.
3. The Tech Lead records the durable technical solution in a feature specification under `docs/specs/`.
4. The Tech Lead defines each justified manual gate in the specification and creates its executable test plan under `docs/tests/`.
5. The Tech Lead decomposes the implementation into GitHub issues; dependent issues identify blocking gate IDs and their GitHub result sources.
6. Developer skills execute those GitHub issues on issue-specific branches.
7. When an implementation issue is ready for review, the Developer commits, pushes the issue branch, opens or updates its pull request, and automatically starts an independent Reviewer execution.
8. The Reviewer independently verifies the pull request against the issue, feature, technical specification, applicable test plans, and assigned developer skill.
9. Blocking review findings return to the assigned developer skill through the pull request for correction and re-review.
10. On `RETURN`, the Developer addresses authorized blocking findings and automatically requests re-review, for at most three correction attempts.
11. The Developer stops earlier when a finding cannot be fixed within its scope or authority or requires human input.
12. After Reviewer approval, the designated human executes any required manual gate against the exact reviewed target and records the result in GitHub.
13. Dependent work continues only after its required manual gates pass.

Authoritative sources:
- `docs/PRODUCT.md` and `docs/features/` define product intent and functional requirements.
- `docs/SPECS.md` and `docs/specs/` define approved technical design.
- `docs/tests/` defines reusable manual test and review procedures.
- GitHub issues define executable implementation work.
- GitHub pull requests and dedicated gate issues contain implementation review history and manual-gate execution results.

GitHub issues must not replace durable product or technical documentation.

Developer skills must implement the approved specification rather than redesign it. If an issue cannot be implemented without changing product behavior, architecture, or an approved technical decision, the developer must stop and escalate to the Tech Lead or user.

An implementation issue is not considered complete until the Reviewer approves the resulting change. Reviewer approval is independent verification and does not replace any manual gate defined in the technical specification.

## Manual Test and Review Gates

Use manual gates only where human validation materially reduces product,
architecture, integration, infrastructure, security, or user-experience risk.
Deterministic behavior should normally be covered by automated tests.

For every formal gate:

- Use a feature-scoped stable ID such as `F-003-G-01` and case IDs such as `F-003-G-01-TC-001`.
- Give the gate exactly one owning feature; related features link to the owning gate.
- Define the gate's purpose, position, pass authority, blocking effect, and test-plan link in the owning technical specification.
- Store the executable procedure under `docs/tests/F-###-feature-name/` using `docs/templates/MANUAL-TEST-GATE.md`.
- Include configuration, safe value sources, exact working directories and commands, startup order, readiness checks, test data, and cleanup.
- Specify API requests for Postman, including environment variables, method, URL, authentication, headers, body, and expected response. Never store real secrets or sensitive evidence.
- Separate automated prerequisites from actions the designated human must perform.
- Record each execution in GitHub against the exact commit, build or deployment, environment, and test-plan revision. Do not store changing execution status in the test plan.
- Allow only the explicitly designated human pass authority to record `PASS`.
- Treat a passing result as stale when a later change affects covered behavior, configuration, infrastructure, test data, or the test procedure.

Normally record a gate on the implementation pull request it directly follows.
Create a dedicated gate issue only when the gate spans multiple pull requests or
repositories, occurs after merge, blocks multiple independent work items, or is
final end-to-end feature acceptance.

## Reviewer Independence

The `reviewer` skill is independent from implementation skills.

The Reviewer:
- Reviews the actual change against the GitHub issue, source feature, technical specification, repository rules, and assigned developer skill.
- Does not edit or fix the implementation.
- Returns blocking findings to the assigned developer skill.
- Escalates product or architecture conflicts to the Tech Lead or user.
- Approves clean work without inventing findings.
- Does not authorize merge, push, deployment, publication, or release.
- Does not mark a Tech Lead-defined manual gate as passed.

## Implementation Branch and Pull Request Policy

For implementation issues created under this workflow:

- Use one issue-specific branch and normally one pull request per implementation issue.
- The assigned Developer is authorized to create/switch to the issue branch, commit issue-scoped work, push that branch, and open/update its pull request.
- This standing authorization does not allow direct pushes to `main`, force-pushes, merges, deployments, releases, destructive actions, or unrelated GitHub changes.
- The pull request must reference the implementation issue.
- Use `Closes #<issue-number>` when merging the pull request should close the issue.
- The pull request is the normal implementation-review surface.
- The Developer never merges its own pull request.
- Reviewer approval is required before the issue is considered complete.
- Any required manual gate remains separate and may still block merge or dependent work.
- Issue-comment-only review is an exception for work where a pull request genuinely cannot or should not be created.

## Review Handoff

GitHub is the standard handoff channel between developer skills and the Reviewer.

- Use the implementation pull request as the default review surface.
- Use implementation issue comments only when a pull request genuinely cannot or should not be created.
- The implementation issue body remains the Tech Lead-defined work package and must not be used as a mutable review log.
- Reviewer findings and decisions must not be stored in product or technical Markdown documentation.
- The user must not be required to copy or relay Reviewer findings between skills.
- After preparing the review surface, the Developer must use the runtime's native agent, task, thread, or equivalent mechanism to start a separate Reviewer execution automatically. The Developer must not perform or approve its own independent review.
- A `RETURN` decision goes back to the same assigned developer skill unless the finding exposes a product or architecture problem that requires escalation.
- A correction attempt begins when the Developer acts on one `RETURN` decision and ends with the next Reviewer decision. The initial review is not a correction attempt.
- Permit at most three correction attempts for an implementation handoff. Use the same issue branch and pull request and preserve every review record.
- Stop the loop immediately when a finding requires product or architecture changes, conflicts with an authoritative source, needs new authority or human input, or cannot be fixed safely by the Developer.
- If the third correction attempt still receives `RETURN`, stop and escalate. Do not begin a fourth correction attempt automatically.
- If the runtime cannot start a separate Reviewer execution, report that limitation and request a separate Reviewer run; do not substitute Developer self-review.
- An `APPROVE` decision makes the issue eligible for completion or the next required manual gate; it does not itself pass that manual gate.

## Developer Skill Orchestration

The implementation skill model is:

- `developer` is the shared execution contract and direct skill for general or tightly coupled cross-layer implementation.
- `frontender` is a frontend specialization of `developer`.
- `backender` is a backend specialization of `developer`.

`frontender` and `backender` require the `developer` skill in addition to their specialization. Do not assume automatic skill inheritance or a repository-relative skill path.

The Tech Lead assigns one primary skill per implementation issue.

Split frontend and backend work only when a stable contract allows the pieces to be implemented and verified independently. Otherwise keep tightly coupled cross-layer work with `developer`.

Do not create frontend/backend handoffs merely to mirror human team boundaries.

## Documentation Location

Repository documentation must follow these placement rules:

- `README.md` belongs at the repository root.
- `AGENTS.md` belongs at the repository root.
- All other documentation belongs under `/docs/`.
- Manual test plans belong under `/docs/tests/`.
- Skills are centrally installed and are not vendored in this repository.

## Forward-Only Workflow Adoption

This repository adopts the current workflow from the migration cutoff forward.
Completed historical work is not retrofitted with new test cases, manual gates,
IDs, templates, or review records. Work already in progress continues under its
current workflow unless the user explicitly requests migration. Features and
implementation tasks created after this migration use the current workflow.
Future changes to existing features use the current workflow only for the changed
scope and any necessary regression coverage; they do not rewrite completed
artifacts merely to match the new format.
