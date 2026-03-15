from __future__ import annotations

import json
import os
from collections import defaultdict

from ai_api_lint.models import Finding, FixResult, LintReport, Severity

# ANSI escape codes
_BOLD = "\033[1m"
_RED = "\033[31m"
_YELLOW = "\033[33m"
_BLUE = "\033[34m"
_DIM = "\033[2m"
_RESET = "\033[0m"

_SEVERITY_ICON: dict[Severity, tuple[str, str]] = {
    Severity.ERROR: ("\u2717", _RED),
    Severity.WARNING: ("\u26a0", _YELLOW),
    Severity.INFO: ("\u2139", _BLUE),
}


def _use_color() -> bool:
    """Return False when NO_COLOR env var is set."""
    return os.environ.get("NO_COLOR") is None


def _ansi(code: str) -> str:
    return code if _use_color() else ""


def format_terminal(report: LintReport, fix_result: FixResult | None = None) -> str:
    """Format a LintReport for terminal output with ANSI colors."""
    lines: list[str] = []

    # Header
    lines.append(f"{_ansi(_BOLD)}ai-api-lint: {report.spec_path}{_ansi(_RESET)}")
    lines.append(
        f"{_ansi(_DIM)}\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501"
        f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501"
        f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501"
        f"\u2501\u2501\u2501{_ansi(_RESET)}"
    )

    # Group findings by (path, method)
    grouped: dict[tuple[str, str], list[Finding]] = defaultdict(list)
    for f in report.findings:
        grouped[(f.path, f.method)].append(f)

    # Operation sections (only operations with findings)
    for (path, method), findings in grouped.items():
        op_id = findings[0].operation_id
        heading = f" {method.upper()} {path}"
        if op_id:
            heading += f"  \u2022  {op_id}"
        lines.append("")
        lines.append(f"{_ansi(_BOLD)}{heading}{_ansi(_RESET)}")

        for f in findings:
            icon, color = _SEVERITY_ICON[f.severity]
            lines.append(f"  {_ansi(color)}{icon}{_ansi(_RESET)} {f.rule_id}  {f.message}")

    # Summary
    lines.append("")
    lines.append(
        f" {_ansi(_BOLD)}Overall Score: {report.overall_score:.1f} / {report.grade}{_ansi(_RESET)}"
    )

    error_count = sum(1 for f in report.findings if f.severity is Severity.ERROR)
    warn_count = sum(1 for f in report.findings if f.severity is Severity.WARNING)
    info_count = sum(1 for f in report.findings if f.severity is Severity.INFO)

    parts: list[str] = []
    if error_count:
        parts.append(f"{error_count} error{'s' if error_count != 1 else ''}")
    if warn_count:
        parts.append(f"{warn_count} warning{'s' if warn_count != 1 else ''}")
    if info_count:
        parts.append(f"{info_count} info")

    finding_detail = f" ({', '.join(parts)})" if parts else ""
    lines.append(
        f" {report.total_operations} operation"
        f"{'s' if report.total_operations != 1 else ''}"
        f", {len(report.findings)} finding"
        f"{'s' if len(report.findings) != 1 else ''}"
        f"{finding_detail}"
    )

    if fix_result is not None:
        lines.append("")
        lines.append(
            f" {_ansi(_BOLD)}Fix Results:{_ansi(_RESET)} "
            f"{len(fix_result.applied)} applied, {len(fix_result.skipped)} skipped"
        )
        for record in fix_result.skipped[:5]:
            reason = record.reason or "Skipped without a recorded reason."
            lines.append(f"  - {record.rule_id} {record.method.upper()} {record.path}: {reason}")
        remaining = len(fix_result.skipped) - 5
        if remaining > 0:
            lines.append(f"  - ... {remaining} more skipped")
        if fix_result.diff_preview:
            diff_lines = fix_result.diff_preview.splitlines()
            preview = "\n".join(diff_lines[:20])
            lines.append("")
            lines.append(f" {_ansi(_BOLD)}Dry-Run Diff Preview:{_ansi(_RESET)}")
            lines.append(preview)
            if len(diff_lines) > 20:
                lines.append(f" ... {len(diff_lines) - 20} more diff lines")

    return "\n".join(lines)


def _finding_to_dict(f: Finding) -> dict:
    d: dict = {
        "rule_id": f.rule_id,
        "severity": f.severity.value,
        "message": f.message,
        "path": f.path,
        "method": f.method,
    }
    if f.operation_id is not None:
        d["operation_id"] = f.operation_id
    if f.suggestion is not None:
        d["suggestion"] = f.suggestion
    return d


def _fix_record_to_dict(record: dict) -> dict:
    if hasattr(record, "reason"):
        data = {
            "rule_id": record.rule_id,
            "path": record.path,
            "method": record.method,
            "description": record.description,
        }
        if record.reason is not None:
            data["reason"] = record.reason
        return data
    return record


def format_json(report: LintReport, fix_result: FixResult | None = None) -> str:
    """Serialize a LintReport to formatted JSON."""
    data = {
        "spec_path": report.spec_path,
        "total_operations": report.total_operations,
        "findings": [_finding_to_dict(f) for f in report.findings],
        "overall_score": report.overall_score,
        "grade": report.grade,
    }
    if fix_result is not None:
        data["fix_result"] = {
            "applied": [_fix_record_to_dict(r) for r in fix_result.applied],
            "skipped": [_fix_record_to_dict(r) for r in fix_result.skipped],
        }
        if fix_result.diff_preview is not None:
            data["fix_result"]["diff_preview"] = fix_result.diff_preview
    return json.dumps(data, indent=2)
