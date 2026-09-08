export type Mode = "block" | "redact";

export type Replacement = {
  key: string;
  value: string;
  entity_types: string[];
};

type CommonResponse = {
  schema_version: 1;
  request_id: string;
  screening_id: string;
  profile_id: string;
  screening_version: string;
};

export type AllowedResponse = CommonResponse & {
  action: "allowed";
  text: string;
  replacements: [];
};

export type BlockedResponse = CommonResponse & {
  action: "blocked";
  code: "protected_content";
};

export type RedactedResponse = CommonResponse & {
  action: "redacted";
  text: string;
  replacements: Replacement[];
};

export type ScreeningResponse = AllowedResponse | BlockedResponse | RedactedResponse;

export type ScreeningRequest = {
  mode: Mode;
  profile_id: string;
  language: "da";
  text: string;
};

export class ScreeningBlockedError extends Error {
  constructor() {
    super("Screening blocked the request.");
    this.name = "ScreeningBlockedError";
  }
}

export async function screen(
  baseUrl: string,
  credential: string,
  request: ScreeningRequest,
  fetcher: typeof fetch = fetch,
): Promise<ScreeningResponse> {
  const response = await fetcher(`${baseUrl.replace(/\/$/, "")}/v1/screen`, {
    method: "POST",
    headers: {
      authorization: `Bearer ${credential}`,
      "content-type": "application/json",
    },
    body: JSON.stringify(request),
  });
  const body: unknown = await response.json();
  if (!response.ok) {
    throw new Error("Screening service request failed.");
  }
  if (!isScreeningResponse(body)) {
    throw new Error("Screening service returned an invalid response.");
  }
  return body;
}

export function modelInput(result: ScreeningResponse): string {
  if (result.action === "blocked") {
    throw new ScreeningBlockedError();
  }
  return result.text;
}

const tokenPattern = /\[\[EUAI_PII_[^\]]*\]\]/g;

export function restoreExact(modelOutput: string, replacements: Replacement[]): string {
  const values = new Map<string, string>();
  for (const replacement of replacements) {
    if (!/^\[\[EUAI_PII_[0-9a-f]{32}\]\]$/.test(replacement.key) || !replacement.value) {
      throw new Error("Invalid replacement mapping.");
    }
    if (values.has(replacement.key)) {
      throw new Error("Duplicate replacement key.");
    }
    values.set(replacement.key, replacement.value);
  }
  return modelOutput.replace(tokenPattern, (token) => {
    const value = values.get(token);
    if (value === undefined) {
      throw new Error("Unknown or modified screening token.");
    }
    return value;
  });
}

function isScreeningResponse(value: unknown): value is ScreeningResponse {
  if (!value || typeof value !== "object" || !("action" in value)) {
    return false;
  }
  const body = value as Record<string, unknown>;
  if (
    body.schema_version !== 1 ||
    !isUuid(body.request_id) ||
    !isUuid(body.screening_id) ||
    typeof body.profile_id !== "string" ||
    !/^[A-Za-z0-9_-]{1,128}$/.test(body.profile_id) ||
    typeof body.screening_version !== "string" ||
    !/^[0-9a-f]{64}$/.test(body.screening_version)
  ) {
    return false;
  }
  const action = body.action;
  if (action === "blocked") {
    return (
      body.code === "protected_content" &&
      hasOnlyKeys(body, ["schema_version", "request_id", "screening_id", "profile_id", "screening_version", "action", "code"])
    );
  }
  if (action === "allowed") {
    return (
      typeof body.text === "string" &&
      Array.isArray(body.replacements) &&
      body.replacements.length === 0 &&
      hasOnlyKeys(body, ["schema_version", "request_id", "screening_id", "profile_id", "screening_version", "action", "text", "replacements"])
    );
  }
  if (action === "redacted") {
    return (
      typeof body.text === "string" &&
      Array.isArray(body.replacements) &&
      body.replacements.length > 0 &&
      body.replacements.every(isReplacement) &&
      new Set(body.replacements.map((replacement) => replacement.key)).size === body.replacements.length &&
      hasOnlyKeys(body, ["schema_version", "request_id", "screening_id", "profile_id", "screening_version", "action", "text", "replacements"])
    );
  }
  return false;
}

function isUuid(value: unknown): value is string {
  return typeof value === "string" && /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/.test(value);
}

function isReplacement(value: unknown): value is Replacement {
  if (!value || typeof value !== "object") {
    return false;
  }
  const replacement = value as Record<string, unknown>;
  return (
    hasOnlyKeys(replacement, ["key", "value", "entity_types"]) &&
    typeof replacement.key === "string" &&
    /^\[\[EUAI_PII_[0-9a-f]{32}\]\]$/.test(replacement.key) &&
    typeof replacement.value === "string" &&
    replacement.value.length > 0 &&
    Array.isArray(replacement.entity_types) &&
    replacement.entity_types.length > 0 &&
    replacement.entity_types.every((entity) => typeof entity === "string" && entity.length > 0)
  );
}

function hasOnlyKeys(value: Record<string, unknown>, keys: string[]): boolean {
  const allowed = new Set(keys);
  return Object.keys(value).every((key) => allowed.has(key));
}
