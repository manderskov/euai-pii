import pytest

from euai_pii.detectors import (
    ConfiguredPattern,
    ConfiguredPatternRecognizer,
    DanishNerRecognizer,
    validate_danish_labels,
)


def test_configured_patterns_are_case_sensitive_by_default():
    recognizer = ConfiguredPatternRecognizer(
        [ConfiguredPattern("case-id", "CONFIGURED_PATTERN", "Project Aurora")]
    )
    assert len(recognizer.analyze("Project Aurora", ["CONFIGURED_PATTERN"])) == 1
    assert recognizer.analyze("project aurora", ["CONFIGURED_PATTERN"]) == []


def test_configured_patterns_can_be_unicode_case_insensitive():
    recognizer = ConfiguredPatternRecognizer(
        [ConfiguredPattern("secret", "CONFIGURED_PATTERN", "følsom", case_sensitive=False)]
    )
    assert len(recognizer.analyze("FØLSOM", ["CONFIGURED_PATTERN"])) == 1


def test_configured_pattern_ids_are_unique():
    with pytest.raises(ValueError, match="unique"):
        ConfiguredPatternRecognizer(
            [
                ConfiguredPattern("duplicate", "A", "a"),
                ConfiguredPattern("duplicate", "B", "b"),
            ]
        )


def test_danish_labels_map_explicit_aliases_and_ignore_org():
    assert validate_danish_labels(["PER", "LOC", "ORG"]) == {"PER": "PERSON", "LOC": "LOCATION"}


def test_danish_labels_fail_closed_when_required_labels_are_missing():
    with pytest.raises(ValueError, match="no supported"):
        validate_danish_labels(["ORG", "MISC"])


class FakeEntity:
    def __init__(self, label, start, end):
        self.label_ = label
        self.start_char = start
        self.end_char = end


class FakeNer:
    labels = ("PER", "LOC", "ORG")


class FakeDoc:
    ents = (FakeEntity("PER", 0, 4), FakeEntity("ORG", 5, 9), FakeEntity("LOC", 10, 14))


class FakeNlp:
    def get_pipe(self, name):
        assert name == "ner"
        return FakeNer()

    def __call__(self, text):
        return FakeDoc()


def test_danish_ner_maps_only_supported_labels():
    recognizer = DanishNerRecognizer(FakeNlp())
    results = recognizer.analyze("text", ["PERSON", "LOCATION"])
    assert [(result.entity_type, result.start, result.end) for result in results] == [
        ("PERSON", 0, 4),
        ("LOCATION", 10, 14),
    ]
