"""Screening orchestration and the F-007 span/token contract."""

from __future__ import annotations

import hashlib
import json
import math
import secrets
import uuid
from dataclasses import dataclass
from typing import Protocol

from presidio_analyzer import RecognizerResult


class Detector(Protocol):
    supported_entities: list[str]

    def analyze(self, text: str, entities: list[str]) -> list[RecognizerResult]: ...


class PresidioDetector:
    """Expose a configured Presidio analyzer through the local detector boundary."""

    def __init__(self, engine, recognizers: tuple[Detector, ...] = ()):
        self.engine = engine
        self.recognizers = recognizers
        self.supported_entities = sorted(
            {entity for recognizer in recognizers for entity in recognizer.supported_entities}
        )

    def analyze(self, text: str, entities: list[str]) -> list[RecognizerResult]:
        results = self.engine.analyze(text=text, language="da", entities=entities)
        for recognizer in self.recognizers:
            results.extend(recognizer.analyze(text, entities))
        return results


@dataclass(frozen=True, slots=True)
class Profile:
    profile_id: str
    allowed_modes: frozenset[str]
    detectors: tuple[Detector, ...]
    categories: frozenset[str]
    thresholds: dict[str, float]
    version_material: str


@dataclass(frozen=True, slots=True)
class Finding:
    start: int
    end: int
    entity_types: frozenset[str]


@dataclass(frozen=True, slots=True)
class Replacement:
    key: str
    value: str
    entity_types: tuple[str, ...]


class ScreeningFailure(Exception):
    """A safe, non-content-bearing screening failure."""

    def __init__(self, code: str = "screening_unavailable", status: int = 503):
        super().__init__(code)
        self.code = code
        self.status = status


class ScreeningService:
    """Run one complete screening decision without retaining request state."""

    def __init__(self, profiles: dict[str, Profile], max_spans: int = 10_000, max_output_bytes: int = 2 * 1024 * 1024):
        self.profiles = profiles
        self.max_spans = max_spans
        self.max_output_bytes = max_output_bytes

    def screen(self, text: str, profile: Profile, mode: str) -> dict[str, object]:
        findings = self._findings(text, profile)
        common = {
            "schema_version": 1,
            "screening_id": str(uuid.uuid4()),
            "profile_id": profile.profile_id,
            "screening_version": hashlib.sha256(profile.version_material.encode()).hexdigest(),
        }
        if not findings:
            result = {**common, "action": "allowed", "text": text, "replacements": []}
            self._validate_output_size(result)
            return result
        if mode == "block":
            return {**common, "action": "blocked", "code": "protected_content"}
        transformed, replacements = self._replace(text, findings)
        result = {
            **common,
            "action": "redacted",
            "text": transformed,
            "replacements": [
                {
                    "key": replacement.key,
                    "value": replacement.value,
                    "entity_types": list(replacement.entity_types),
                }
                for replacement in replacements
            ],
        }
        self._validate_output_size(result)
        return result

    def _validate_output_size(self, result: dict[str, object]) -> None:
        if len(json.dumps(result, ensure_ascii=False).encode("utf-8")) > self.max_output_bytes:
            raise ScreeningFailure("screening_limit_exceeded", 413)

    def _findings(self, text: str, profile: Profile) -> list[Finding]:
        raw: list[Finding] = []
        for detector in profile.detectors:
            results = detector.analyze(text, list(profile.categories))
            for result in results:
                self._validate_result(result, text, profile)
                if result.score >= profile.thresholds.get(result.entity_type, 1.0):
                    raw.append(Finding(result.start, result.end, frozenset({result.entity_type})))
        if len(raw) > self.max_spans:
            raise ScreeningFailure("screening_limit_exceeded", 413)
        merged = self._merge(raw)
        if len(merged) > self.max_spans:
            raise ScreeningFailure("screening_limit_exceeded", 413)
        return merged

    @staticmethod
    def _validate_result(result: RecognizerResult, text: str, profile: Profile) -> None:
        if result.entity_type not in profile.categories:
            raise ScreeningFailure()
        if not isinstance(result.start, int) or not isinstance(result.end, int):
            raise ScreeningFailure()
        if result.start < 0 or result.start >= result.end or result.end > len(text):
            raise ScreeningFailure()
        try:
            valid_score = math.isfinite(result.score) and 0 <= result.score <= 1
        except (TypeError, ValueError):
            valid_score = False
        if not valid_score:
            raise ScreeningFailure()

    @staticmethod
    def _merge(findings: list[Finding]) -> list[Finding]:
        merged: list[Finding] = []
        for finding in sorted(findings, key=lambda item: (item.start, item.end)):
            if merged and finding.start < merged[-1].end:
                previous = merged[-1]
                merged[-1] = Finding(
                    previous.start,
                    max(previous.end, finding.end),
                    previous.entity_types | finding.entity_types,
                )
            else:
                merged.append(finding)
        return merged

    @staticmethod
    def _new_key(text: str, used: set[str]) -> str:
        while True:
            key = f"[[EUAI_PII_{uuid.uuid4().hex}]]"
            if key not in text and key not in used:
                return key

    def _replace(self, text: str, findings: list[Finding]) -> tuple[str, list[Replacement]]:
        values_to_keys: dict[str, str] = {}
        used_keys: set[str] = set()
        replacements: list[Replacement] = []
        edits: list[tuple[int, int, str]] = []
        for finding in findings:
            value = text[finding.start:finding.end]
            key = values_to_keys.get(value)
            if key is None:
                key = self._new_key(text, used_keys)
                values_to_keys[value] = key
                used_keys.add(key)
                replacements.append(Replacement(key, value, tuple(sorted(finding.entity_types))))
            else:
                for index, replacement in enumerate(replacements):
                    if replacement.key == key:
                        replacements[index] = Replacement(
                            replacement.key,
                            replacement.value,
                            tuple(sorted(set(replacement.entity_types) | finding.entity_types)),
                        )
                        break
            edits.append((finding.start, finding.end, key))
        transformed = text
        for start, end, key in reversed(edits):
            transformed = transformed[:start] + key + transformed[end:]
        return transformed, replacements


def constant_time_credential_match(candidate: str, configured: tuple[str, ...]) -> bool:
    """Compare credentials without exposing which configured value matched."""

    matched = False
    for credential in configured:
        matched = secrets.compare_digest(candidate, credential) or matched
    return matched
