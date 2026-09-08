"""Run the deterministic baseline evaluation and emit a JSON report.

The report is intentionally generated locally. It is evidence for Gate 1, not
a precomputed quality claim. Danish NER evaluation is enabled with --model.
"""

from __future__ import annotations

import argparse
import json
import multiprocessing
import platform
import resource
import statistics
import time
from dataclasses import dataclass
from pathlib import Path

from euai_pii.detectors import CprRecognizer, CvrRecognizer, DanishNerRecognizer


@dataclass(frozen=True, slots=True)
class Example:
    text: str
    expected: tuple[str, ...]


def _detector_worker(model_name: str | None, text: str, result_queue) -> None:
    """Load a fresh detector process and run one bounded measurement."""

    from euai_pii.detectors import CprRecognizer, CvrRecognizer, DanishNerRecognizer

    recognizers = [CprRecognizer(), CvrRecognizer()]
    if model_name:
        import spacy

        recognizers.append(DanishNerRecognizer(spacy.load(model_name)))
    started = time.perf_counter()
    for recognizer in recognizers:
        recognizer.analyze(text, recognizer.supported_entities)
    result_queue.put((time.perf_counter() - started) * 1000)


def _timeout_worker(model_name: str | None, text: str, result_queue) -> None:
    """Simulate work that exceeds the service's maximum request deadline."""

    _detector_worker(model_name, text, result_queue)
    time.sleep(11)


def _run_process(target, args: tuple, timeout_seconds: float) -> dict[str, object]:
    context = multiprocessing.get_context("spawn")
    result_queue = context.Queue()
    process = context.Process(target=target, args=(*args, result_queue))
    started = time.perf_counter()
    process.start()
    process.join(timeout_seconds)
    elapsed_ms = (time.perf_counter() - started) * 1000
    terminated = process.is_alive()
    if terminated:
        process.terminate()
        process.join(5)
    result = result_queue.get_nowait() if not result_queue.empty() else None
    result_queue.close()
    return {
        "elapsed_ms": elapsed_ms,
        "worker_result_ms": result,
        "timed_out": terminated,
        "exit_code": process.exitcode,
    }


def synthetic_examples() -> list[Example]:
    names = [
        "Anna Jensen", "Mikkel Sørensen", "Lise Nielsen", "Jørgen Hansen",
        "Freja Andersen", "Poul Christensen", "Ida Larsen", "Niels Rasmussen",
        "Sofie Thomsen", "Kasper Madsen", "Clara Pedersen", "Emil Poulsen",
        "Asta Knudsen", "Viggo Mortensen", "Laura Jakobsen", "Oskar Lund",
        "Alma Holm", "Elias Schmidt", "Nora Vestergaard", "Noah Frandsen",
        "Karla Møller", "August Kristensen", "Maja Gregersen", "William Bak",
        "Ella Søndergaard",
    ]
    cities = [
        "Aarhus", "København", "Odense", "Aalborg", "Esbjerg", "Randers",
        "Kolding", "Horsens", "Vejle", "Roskilde", "Herning", "Hørsholm",
        "Silkeborg", "Næstved", "Fredericia", "Viborg", "Køge", "Holstebro",
        "Tårnby", "Slagelse", "Svendborg", "Hjørring", "Helsingør", "Ballerup",
        "Skive",
    ]
    examples = []
    for index, (name, city) in enumerate(zip(names, cities)):
        examples.extend(
            [
                Example(f"Kontakt {name} om sagen.", ("PERSON",)),
                Example(f"CPR 0101{index:02d}-1234 skal beskyttes.", ("DK_CPR",)),
                Example(f"CVR {12345678 + index:08d} er et virksomheds-id.", ("DK_CVR",)),
                Example(f"{12345678 + index:08d} uden præfiks er ikke en CVR-match.", ()),
                Example(f"DK {87654321 - index:08d} er et virksomheds-id.", ("DK_CVR",)),
                Example(f"Adresse: Sønder Allé {index + 10}, 8000 {city}.", ("LOCATION",)),
                Example(f"Mødestedet er i {city} på fredag.", ("LOCATION",)),
                Example(f"Navnet er Mærsk og teksten har æ, ø og å i variant {index}.", ()),
                Example(f"Nummer 32{index:02d}99-1234 er en ugyldig dato.", ()),
            ]
        )
    return examples


def evaluate(model_name: str | None = None) -> dict[str, object]:
    recognizers = [CprRecognizer(), CvrRecognizer()]
    if model_name:
        import spacy

        recognizers.append(DanishNerRecognizer(spacy.load(model_name)))
    examples = synthetic_examples()
    category_stats: dict[str, dict[str, int]] = {}
    missed_examples: list[dict[str, object]] = []
    seen_missed: set[tuple[str, tuple[str, ...], tuple[str, ...]]] = set()
    for example in examples:
        found = {
            result.entity_type
            for recognizer in recognizers
            for result in recognizer.analyze(example.text, recognizer.supported_entities)
        }
        expected = set(example.expected)
        for category in {"DK_CPR", "DK_CVR", "PERSON", "LOCATION"}:
            stats = category_stats.setdefault(category, {"true_positive": 0, "false_positive": 0, "false_negative": 0})
            if category in found and category in expected:
                stats["true_positive"] += 1
            elif category in found:
                stats["false_positive"] += 1
            elif category in expected:
                stats["false_negative"] += 1
        missed_key = (example.text, tuple(sorted(expected)), tuple(sorted(found)))
        if found != expected and missed_key not in seen_missed and len(missed_examples) < 20:
            seen_missed.add(missed_key)
            missed_examples.append({"text": example.text, "expected": sorted(expected), "found": sorted(found)})

    timing_results = {}
    for size in (1000, 10000, 100000):
        sample = ("Kontakt på 010100-1234 og CVR 12345678. " * (size // 41 + 1))[:size]
        timings = []
        for _ in range(5):
            started = time.perf_counter()
            for recognizer in recognizers:
                recognizer.analyze(sample, recognizer.supported_entities)
            timings.append((time.perf_counter() - started) * 1000)
        timing_results[str(size)] = {
            "median_ms": statistics.median(timings),
            "max_ms": max(timings),
            "within_10_second_deadline": max(timings) < 10000,
        }
    cold_start = _run_process(
        _detector_worker,
        (model_name, "Kontakt på 010100-1234 og CVR 12345678. " * 20),
        10,
    )
    timeout_probe = _run_process(
        _timeout_worker,
        (model_name, "Kontakt på 010100-1234 og CVR 12345678. "),
        10,
    )
    for stats in category_stats.values():
        stats["precision"] = (
            stats["true_positive"] / (stats["true_positive"] + stats["false_positive"])
            if stats["true_positive"] + stats["false_positive"]
            else 0.0
        )
        stats["recall"] = (
            stats["true_positive"] / (stats["true_positive"] + stats["false_negative"])
            if stats["true_positive"] + stats["false_negative"]
            else 0.0
        )
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "dataset_size": len(examples),
        "detectors": category_stats,
        "message_level_false_blocks": sum(
            1
            for example in examples
            if not example.expected
            and any(
                recognizer.analyze(example.text, recognizer.supported_entities)
                for recognizer in recognizers
            )
        ),
        "missed_examples": missed_examples,
        "resource": {"max_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss},
        "cold_start": cold_start,
        "timeout_probe": {
            **timeout_probe,
            "deadline_seconds": 10,
            "worker_was_terminated": timeout_probe["timed_out"],
        },
        "timing_ms": timing_results,
        "ner": {
            "status": "complete" if model_name else "not run",
            "model": model_name,
            "reason": None if model_name else "Pass --model in the Gate 1 environment.",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("artifacts/baseline-report.json"))
    parser.add_argument("--model", help="Installed spaCy model package or path, for example da_core_news_md")
    args = parser.parse_args()
    report = evaluate(args.model)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
