import assert from "node:assert/strict";
import test from "node:test";

import {
  ScreeningBlockedError,
  modelInput,
  restoreExact,
  screen,
  type Replacement,
} from "../src/client.js";

function fakeFetch(body: unknown, status = 200): typeof fetch {
  return async () => new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });
}

const common = {
  schema_version: 1 as const,
  request_id: "11111111-1111-4111-8111-111111111111",
  screening_id: "22222222-2222-4222-8222-222222222222",
  profile_id: "da-identifiers-v1",
  screening_version: "a".repeat(64),
};

test("blocked responses never enter the model input boundary", async () => {
  const result = await screen("http://screening", "secret", {
    mode: "block",
    profile_id: "da-identifiers-v1",
    language: "da",
    text: "protected",
  }, fakeFetch({ ...common, action: "blocked", code: "protected_content" }));
  assert.throws(() => modelInput(result), ScreeningBlockedError);
});

test("allowed and redacted responses expose only transformed model input", async () => {
  const allowed = await screen("http://screening", "secret", {
    mode: "block", profile_id: "da-identifiers-v1", language: "da", text: "safe",
  }, fakeFetch({ ...common, action: "allowed", text: "safe", replacements: [] }));
  assert.equal(modelInput(allowed), "safe");

  const redaction: Replacement = {
    key: "[[EUAI_PII_11111111111141118111111111111111]]",
    value: "Anna Jensen",
    entity_types: ["PERSON"],
  };
  const redacted = await screen("http://screening", "secret", {
    mode: "redact", profile_id: "da-personal-v1", language: "da", text: "Anna Jensen",
  }, fakeFetch({ ...common, action: "redacted", text: redaction.key, replacements: [redaction] }));
  assert.equal(modelInput(redacted), redaction.key);
  assert.equal("text" in redacted && redacted.text.includes(redaction.value), false);
});

test("restoration is exact, single-pass, and supports repeated or reordered tokens", () => {
  const first: Replacement = {
    key: "[[EUAI_PII_11111111111141118111111111111111]]",
    value: "Anna [[EUAI_PII_not-a-token]]",
    entity_types: ["PERSON"],
  };
  const second: Replacement = {
    key: "[[EUAI_PII_22222222222242228222222222222222]]",
    value: "Aarhus",
    entity_types: ["LOCATION"],
  };
  assert.equal(
    restoreExact(`${second.key} / ${first.key} / ${first.key}`, [first, second]),
    `${second.value} / ${first.value} / ${first.value}`,
  );
});

test("restoration rejects unknown or modified tokens but allows missing mappings", () => {
  const known: Replacement = {
    key: "[[EUAI_PII_11111111111141118111111111111111]]",
    value: "Anna",
    entity_types: ["PERSON"],
  };
  assert.equal(restoreExact("No token here", [known]), "No token here");
  assert.throws(() => restoreExact("[[EUAI_PII_99999999999949998999999999999999]]", [known]));
  assert.throws(() => restoreExact("[[EUAI_PII_modified]]", [known]));
});

test("malformed successful envelopes are rejected", async () => {
  await assert.rejects(() => screen("http://screening", "secret", {
    mode: "block", profile_id: "da-identifiers-v1", language: "da", text: "safe",
  }, fakeFetch({ ...common, action: "allowed", text: "safe", replacements: [{}] })));
});

test("duplicate replacement keys are rejected", async () => {
  const replacement: Replacement = {
    key: "[[EUAI_PII_11111111111141118111111111111111]]",
    value: "Anna",
    entity_types: ["PERSON"],
  };
  await assert.rejects(() => screen("http://screening", "secret", {
    mode: "redact", profile_id: "da-personal-v1", language: "da", text: replacement.key,
  }, fakeFetch({ ...common, action: "redacted", text: replacement.key, replacements: [replacement, replacement] })));
});
