from __future__ import annotations

import json
from pathlib import Path

from ai_api_lint.rules import create_default_engine

FIXTURES = Path(__file__).parent / "fixtures"


def test_create_default_engine():
    engine = create_default_engine()
    assert len(engine._rules) > 0
    assert len(engine._global_checks) > 0


def test_lint_empty_spec():
    engine = create_default_engine()
    report = engine.lint({})
    assert report.total_operations == 0
    assert report.overall_score == 100.0


def test_lint_good_api():
    spec = json.loads((FIXTURES / "good_api.json").read_text())
    engine = create_default_engine()
    report = engine.lint(spec, spec_path="good_api.json")
    assert report.total_operations == 4
    assert report.overall_score >= 75, f"Expected >= 75, got {report.overall_score}"


def test_lint_bad_api():
    spec = json.loads((FIXTURES / "bad_api.json").read_text())
    engine = create_default_engine()
    report = engine.lint(spec, spec_path="bad_api.json")
    assert report.total_operations >= 5
    assert report.overall_score < 50, f"Expected < 50, got {report.overall_score}"
    assert len(report.findings) > 0
