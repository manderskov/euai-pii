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
4. The Tech Lead decomposes the implementation into GitHub issues.
5. Developer skills execute those GitHub issues on issue-specific branches.
6. When an implementation issue is ready for review, the Developer commits, pushes the issue branch, and opens or updates its pull request.
7. The Reviewer independently verifies the pull request against the issue, feature, technical specification, and applicable developer skill.
8. Blocking review findings return to the assigned developer skill through the pull request for correction and re-review.
9. Manual review/test gates defined by the Tech Lead must be passed before work continues across major implementation boundaries.

Authoritative sources:
- `docs/PRODUCT.md` and `docs/features/` define product intent and functional requirements.
- `docs/SPECS.md` and `docs/specs/` define approved technical design.
- GitHub issues define executable implementation work.
- GitHub pull requests contain the proposed implementation diff and implementation review history.

GitHub issues must not replace durable product or technical documentation.

Developer skills must implement the approved specification rather than redesign it. If an issue cannot be implemented without changing product behavior, architecture, or an approved technical decision, the developer must stop and escalate to the Tech Lead or user.

An implementation issue is not considered complete until the Reviewer approves the resulting change. Reviewer approval is independent verification and does not replace any manual gate defined in the technical specification.

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
- A `RETURN` decision goes back to the same assigned developer skill unless the finding exposes a product or architecture problem that requires escalation.
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
- Skills are centrally installed and are not vendored in this repository.
