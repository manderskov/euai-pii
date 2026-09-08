from presidio_analyzer import RecognizerResult

from euai_pii.detectors import CprRecognizer, CvrRecognizer


def spans(recognizer, text, entity):
    return [(result.start, result.end, result.entity_type) for result in recognizer.analyze(text, [entity])]


def test_cpr_accepts_supported_formats_and_danish_characters_around_value():
    text = "Kontakt Jørgen på 010100-1234, eller på 010100\u20101234."
    results = spans(CprRecognizer(), text, "DK_CPR")
    assert [text[start:end] for start, end, _ in results] == ["010100-1234", "010100\u20101234"]


def test_cpr_accepts_nonbreaking_space_and_rejects_invalid_dates_and_long_numbers():
    text = "010100\u00a01234 321399-1234 0013001234 10101001234"
    results = spans(CprRecognizer(), text, "DK_CPR")
    assert [text[start:end] for start, end, _ in results] == ["010100\u00a01234"]


def test_cpr_rejects_unicode_decimal_digit_neighbors():
    assert spans(CprRecognizer(), "x١01010-1234", "DK_CPR") == []
    assert spans(CprRecognizer(), "010100-1234٩", "DK_CPR") == []


def test_cvr_requires_explicit_prefix():
    recognizer = CvrRecognizer()
    text = "CVR12345678 DK 87654321 12345678"
    results = spans(recognizer, text, "DK_CVR")
    assert [text[start:end] for start, end, _ in results] == ["CVR12345678", "DK 87654321"]


def test_recognizers_return_full_confidence_results():
    result = CprRecognizer().analyze("0101001234", ["DK_CPR"])[0]
    assert isinstance(result, RecognizerResult)
    assert result.score == 1.0
