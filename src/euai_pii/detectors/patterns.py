"""Server-controlled configured pattern recognizers."""

from __future__ import annotations

import re
from dataclasses import dataclass

from presidio_analyzer import EntityRecognizer, RecognizerResult


@dataclass(frozen=True, slots=True)
class ConfiguredPattern:
    """One immutable trusted pattern loaded from deployment configuration."""

    rule_id: str
    entity_type: str
    expression: str
    case_sensitive: bool = True


class ConfiguredPatternRecognizer(EntityRecognizer):
    """Apply precompiled, deployment-owned literal or regular-expression rules."""

    def __init__(self, patterns: list[ConfiguredPattern]) -> None:
        if not patterns:
            raise ValueError("at least one configured pattern is required")
        ids = [pattern.rule_id for pattern in patterns]
        if len(ids) != len(set(ids)):
            raise ValueError("configured pattern IDs must be unique")
        if any(not pattern.rule_id for pattern in patterns):
            raise ValueError("configured pattern IDs must not be empty")

        self.patterns = tuple(
            (
                pattern,
                re.compile(
                    pattern.expression,
                    0 if pattern.case_sensitive else re.IGNORECASE,
                ),
            )
            for pattern in patterns
        )
        super().__init__(
            supported_entities=sorted({pattern.entity_type for pattern in patterns}),
            name="configured pattern recognizer",
        )

    def analyze(self, text: str, entities: list[str], nlp_artifacts=None) -> list[RecognizerResult]:
        results: list[RecognizerResult] = []
        for pattern, expression in self.patterns:
            if pattern.entity_type not in entities:
                continue
            results.extend(
                RecognizerResult(
                    entity_type=pattern.entity_type,
                    start=match.start(),
                    end=match.end(),
                    score=1.0,
                )
                for match in expression.finditer(text)
            )
        return results
