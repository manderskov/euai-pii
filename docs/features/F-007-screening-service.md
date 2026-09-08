# F-007 — Screening Service

## Purpose

Let trusted applications screen text locally and either block protected content or replace it with reversible, unique placeholders before external processing.

## Functional Description

Status: documentation baseline accepted for the standalone euai-pii repository; implementation and detector acceptance gates remain separate.

A standalone private service receives text and an authorized screening profile. In block mode, a protected match blocks the submission. In redact mode, detected protected spans are replaced with opaque keys and the original values are returned separately to the trusted caller. The caller sends only transformed text to its model and retains the mapping for later controlled restoration.

The user has selected Presidio and requested both modes. Danish named-entity recognition is proposed alongside structured identifier detection. The service does not itself invoke a conversational model, restore generated responses, or persist conversations.

The remote product vision and F-006 currently prescribe block-only behavior. The user's subsequent request explicitly introduces reversible redaction for this service. This draft records that scoped change; it does not silently change F-006 or authorize redaction in existing EUAI chat routes. The platform vision must be aligned by its owner before platform integration is treated as approved. The remote vision is not copied or edited here.

## Functional Requirements

- Authenticate trusted callers and restrict them to authorized screening profiles and modes.
- Support `block` and `redact` operations with explicit, distinguishable outcomes.
- Return unchanged text when screening completes without a protected match.
- Return no original content or restoration mapping for blocked submissions.
- In redact mode, return transformed text and a complete mapping for every replacement.
- Repeated identical protected text uses the same key within one request; unrelated requests do not share keys or mappings.
- Preserve all text outside replaced spans, including Danish characters, whitespace, and punctuation.
- Detect structured identifiers using explicit rules; propose Danish person and location detection using local NER. Report no guarantee of complete PII detection.
- Keep NER optional by trusted profile, but never silently skip it when that profile requires it.
- Fail the whole operation if required screening or transformation cannot complete. Never return partially screened text as successful.
- Keep sensitive text and mappings out of logs, persistent storage, and external detector services.
- Keep rules and model behavior versioned so consumers can identify the screening configuration used.
- Make the restoration contract precise enough for a trusted caller to merge exact keys after model generation.

## Out of Scope

This first specification covers the screening service boundary. EUAI chat integration, mapping persistence, streaming restoration, cross-request mapping reuse, uploads/OCR, policy administration UI, public client access, and OpenAI Privacy Filter integration require subsequent specifications. General NER does not establish private-person status or detect arbitrary medical, financial, or confidential narrative content.

## Open Questions

- Repository ownership is resolved: https://github.com/manderskov/euai-pii. Feature ID F-007 is retained from the EUAI platform planning sequence.
- Approve the proposed Danish NER baseline and initial profile categories in the technical specification.
- Platform integration requires the product-vision change and a separate functional definition of redacted history, restoration, and tool behavior.
