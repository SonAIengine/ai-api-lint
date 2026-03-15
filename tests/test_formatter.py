from __future__ import annotations

import json

from ai_api_lint.formatter import format_json, format_terminal
from ai_api_lint.models import FixRecord, FixResult, LintReport


class TestFormatterWithFixResults:
    def test_terminal_includes_skip_reasons(self) -> None:
        report = LintReport(spec_path="test.json", total_operations=1)
        fix_result = FixResult(
            applied=[
                FixRecord(
                    rule_id="AI042",
                    path="/items",
                    method="get",
                    description="Add 400",
                )
            ],
            skipped=[
                FixRecord(
                    rule_id="AI034",
                    path="/items",
                    method="post",
                    description="Add request body description",
                    reason="No changes were needed for the current spec state.",
                )
            ],
        )

        output = format_terminal(report, fix_result=fix_result)

        assert "Fix Results:" in output
        assert "1 applied, 1 skipped" in output
        assert "AI034 POST /items" in output
        assert "No changes were needed" in output

    def test_terminal_includes_diff_preview(self) -> None:
        report = LintReport(spec_path="test.json", total_operations=1)
        fix_result = FixResult(diff_preview='--- before\n+++ after\n+  "400": {}')

        output = format_terminal(report, fix_result=fix_result)

        assert "Dry-Run Diff Preview:" in output
        assert "--- before" in output
        assert "+++ after" in output

    def test_json_includes_fix_result_details(self) -> None:
        report = LintReport(spec_path="test.json", total_operations=1)
        fix_result = FixResult(
            skipped=[
                FixRecord(
                    rule_id="AI034",
                    path="/items",
                    method="post",
                    description="Add request body description",
                    reason="ValueError: bad state",
                )
            ],
            diff_preview="--- before\n+++ after",
        )

        payload = json.loads(format_json(report, fix_result=fix_result))

        assert payload["fix_result"]["skipped"][0]["rule_id"] == "AI034"
        assert payload["fix_result"]["skipped"][0]["reason"] == "ValueError: bad state"
        assert payload["fix_result"]["diff_preview"] == "--- before\n+++ after"
