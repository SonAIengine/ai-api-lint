from __future__ import annotations

from ai_api_lint.models import Finding, Severity
from ai_api_lint.scorer import calculate_score


def _make_finding(severity: Severity = Severity.ERROR) -> Finding:
    return Finding(
        rule_id="test",
        severity=severity,
        message="test",
        path="/test",
        method="get",
    )


def test_no_findings_perfect_score():
    score, grade = calculate_score([], 5)
    assert score == 100.0
    assert grade == "Excellent"


def test_zero_operations():
    score, grade = calculate_score([], 0)
    assert score == 100.0
    assert grade == "N/A"


def test_error_penalty():
    findings = [_make_finding(Severity.ERROR)]
    score, _grade = calculate_score(findings, 1)
    assert score == 80.0  # 100 - 20/1


def test_warning_penalty():
    findings = [_make_finding(Severity.WARNING)]
    score, _grade = calculate_score(findings, 1)
    assert score == 92.0  # 100 - 8/1


def test_info_penalty():
    findings = [_make_finding(Severity.INFO)]
    score, _grade = calculate_score(findings, 1)
    assert score == 98.0  # 100 - 2/1


def test_multiple_operations_dilute():
    findings = [_make_finding(Severity.ERROR)]
    score, _grade = calculate_score(findings, 2)
    assert score == 90.0  # 100 - 20/2


def test_grade_excellent():
    _, grade = calculate_score([], 1)
    assert grade == "Excellent"


def test_grade_good():
    findings = [_make_finding(Severity.ERROR)]
    _, grade = calculate_score(findings, 1)
    assert grade == "Good"  # 80


def test_grade_fair():
    findings = [_make_finding(Severity.ERROR)] * 2
    _, grade = calculate_score(findings, 1)
    assert grade == "Fair"  # 60


def test_grade_poor():
    findings = [_make_finding(Severity.ERROR)] * 3
    _, grade = calculate_score(findings, 1)
    assert grade == "Poor"  # 40


def test_grade_critical():
    findings = [_make_finding(Severity.ERROR)] * 4
    _, grade = calculate_score(findings, 1)
    assert grade == "Critical"  # 20


def test_score_floor_at_zero():
    findings = [_make_finding(Severity.ERROR)] * 10
    score, _grade = calculate_score(findings, 1)
    assert score == 0.0
