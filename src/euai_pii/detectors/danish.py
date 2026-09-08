"""Explicit label handling for the selected Danish spaCy model."""

from __future__ import annotations

from collections.abc import Iterable

from presidio_analyzer import EntityRecognizer, RecognizerResult

DANISH_ENTITY_LABELS = {
    "PERSON": frozenset({"PER", "PERSON"}),
    "LOCATION": frozenset({"LOC", "GPE", "LOCATION"}),
}


def validate_danish_labels(labels: Iterable[str]) -> dict[str, str]:
    """Return the configured mapping and reject unknown required labels.

    The model may expose one of the documented aliases. The service must not
    silently fall back to another language or label set.
    """

    available = set(labels)
    mapping: dict[str, str] = {}
    for entity_type, candidates in DANISH_ENTITY_LABELS.items():
        match = next((candidate for candidate in candidates if candidate in available), None)
        if match is not None:
            mapping[match] = entity_type
    if not mapping:
        raise ValueError("Danish model exposes no supported PERSON or LOCATION labels")
    return mapping


class DanishNerRecognizer(EntityRecognizer):
    """Adapt a preloaded Danish spaCy pipeline to Presidio entities."""

    def __init__(self, nlp) -> None:
        self.nlp = nlp
        ner = nlp.get_pipe("ner")
        self.label_mapping = validate_danish_labels(ner.labels)
        super().__init__(
            supported_entities=sorted(set(self.label_mapping.values())),
            name="Danish NER recognizer",
        )

    def analyze(self, text: str, entities: list[str], nlp_artifacts=None) -> list[RecognizerResult]:
        requested = set(entities)
        document = self.nlp(text)
        return [
            RecognizerResult(
                entity_type=self.label_mapping[entity.label_],
                start=entity.start_char,
                end=entity.end_char,
                score=1.0,
            )
            for entity in document.ents
            if entity.label_ in self.label_mapping
            and self.label_mapping[entity.label_] in requested
        ]
