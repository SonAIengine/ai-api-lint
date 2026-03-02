"""Tests for the HTML report generator."""

from __future__ import annotations

from ai_api_lint.models import Finding, FixRecord, FixResult, LintReport, Severity
from ai_api_lint.report import generate_html_report


class TestHtmlReportBasic:
    def test_html_structure(self) -> None:
        report = LintReport(
            spec_path="test.json",
            total_operations=5,
            findings=[
                Finding(
                    rule_id="AI042",
                    severity=Severity.WARNING,
                    message="No 4xx response",
                    path="/items",
                    method="get",
                    operation_id="listItems",
                ),
                Finding(
                    rule_id="AI010",
                    severity=Severity.ERROR,
                    message="No description",
                    path="/users",
                    method="post",
                ),
            ],
            overall_score=71.2,
            grade="Fair",
        )
        html = generate_html_report(report)
        assert "<!DOCTYPE html>" in html
        assert "test.json" in html
        assert "71" in html
        assert "Fair" in html
        assert "AI042" in html
        assert "AI010" in html
        assert "/items" in html

    def test_score_gauge_present(self) -> None:
        report = LintReport(
            spec_path="x.json", total_operations=1, overall_score=85.0, grade="Good"
        )
        html = generate_html_report(report)
        assert "<svg" in html
        assert "85" in html


class TestHtmlReportWithFix:
    def test_fix_section_present(self) -> None:
        report = LintReport(
            spec_path="x.json", total_operations=1, overall_score=90.0, grade="Excellent"
        )
        fix_result = FixResult(
            applied=[
                FixRecord(rule_id="AI042", path="/items", method="get", description="Add 400"),
            ],
            skipped=[
                FixRecord(rule_id="AI034", path="/items", method="post", description="Skipped"),
            ],
        )
        html = generate_html_report(report, fix_result=fix_result)
        assert "Fix Results" in html
        assert "Applied" in html
        assert "Skipped" in html


class TestHtmlReportNoFindings:
    def test_no_findings(self) -> None:
        report = LintReport(
            spec_path="clean.json",
            total_operations=10,
            findings=[],
            overall_score=100.0,
            grade="Excellent",
        )
        html = generate_html_report(report)
        assert "<!DOCTYPE html>" in html
        assert "100" in html
        assert "No findings" in html
