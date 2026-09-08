"""Deterministic Danish identifier recognizers.

These recognizers intentionally do not perform registry lookups or checksum
validation. They only claim the v1 coverage defined by F-007.
"""

from __future__ import annotations

import calendar
import re

from presidio_analyzer import EntityRecognizer, RecognizerResult

_CPR_RE = re.compile(
    r"(?<!\d)([0-9]{6})(?:[-\u2010\u2011 \u00a0]?)([0-9]{4})(?!\d)"
)
_CVR_RE = re.compile(r"(?i)(?<!\d)(CVR|DK)[ \t]?([0-9]{8})(?!\d)")


def _valid_cpr_date(value: str) -> bool:
    day = int(value[:2])
    month = int(value[2:4])
    year_suffix = int(value[4:6])
    if not 1 <= month <= 12:
        return False

    # CPR's century is not encoded in this v1 recognizer. Accept a date when
    # at least one plausible 1900/2000 interpretation is calendar-valid.
    for century in (1900, 2000):
        year = century + year_suffix
        if day <= calendar.monthrange(year, month)[1]:
            return True
    return False


def _result(entity_type: str, start: int, end: int) -> RecognizerResult:
    return RecognizerResult(entity_type=entity_type, start=start, end=end, score=1.0)


class CprRecognizer(EntityRecognizer):
    """Recognize supported CPR-shaped values with plausible dates."""

    def __init__(self) -> None:
        super().__init__(supported_entities=["DK_CPR"], name="DK CPR recognizer")

    def analyze(self, text: str, entities: list[str], nlp_artifacts=None) -> list[RecognizerResult]:
        if "DK_CPR" not in entities:
            return []
        results = []
        for match in _CPR_RE.finditer(text):
            if _valid_cpr_date(match.group(1)):
                results.append(_result("DK_CPR", match.start(), match.end()))
        return results


class CvrRecognizer(EntityRecognizer):
    """Recognize prefixed Danish CVR-shaped values."""

    def __init__(self) -> None:
        super().__init__(supported_entities=["DK_CVR"], name="DK CVR recognizer")

    def analyze(self, text: str, entities: list[str], nlp_artifacts=None) -> list[RecognizerResult]:
        if "DK_CVR" not in entities:
            return []
        return [
            _result("DK_CVR", match.start(), match.end())
            for match in _CVR_RE.finditer(text)
        ]
