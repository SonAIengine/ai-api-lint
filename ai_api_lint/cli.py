from __future__ import annotations

import argparse
import sys

from ai_api_lint.formatter import format_json, format_terminal
from ai_api_lint.loader import load_spec, resolve_refs
from ai_api_lint.rules import create_default_engine


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="ai-api-lint",
        description="AI-friendly API linter for OpenAPI specifications",
    )
    parser.add_argument("spec", nargs="?", help="Path to OpenAPI spec (JSON/YAML)")
    parser.add_argument(
        "--format",
        choices=["terminal", "json"],
        default="terminal",
        dest="output_format",
    )
    parser.add_argument("--min-score", type=float, default=0)
    parser.add_argument(
        "--severity",
        choices=["error", "warning", "info"],
        default="info",
    )
    parser.add_argument("--list-rules", action="store_true")
    args = parser.parse_args()

    if args.list_rules:
        engine = create_default_engine()
        for rule in engine._rules:  # noqa: SLF001
            print(f"  {rule.rule_id}  [{rule.severity.value:>7}]  {rule.short_description}")
        sys.exit(0)

    if not args.spec:
        parser.print_help()
        sys.exit(1)

    try:
        spec = load_spec(args.spec)
    except Exception as e:  # noqa: BLE001
        print(f"Error loading spec: {e}", file=sys.stderr)
        sys.exit(3)

    resolve_refs(spec)
    engine = create_default_engine()
    report = engine.lint(spec, spec_path=args.spec)

    # Filter by severity
    severity_order = {"error": 0, "warning": 1, "info": 2}
    min_level = severity_order[args.severity]
    report.findings = [f for f in report.findings if severity_order[f.severity.value] <= min_level]

    if args.output_format == "json":
        print(format_json(report))
    else:
        print(format_terminal(report))

    if report.overall_score < args.min_score:
        sys.exit(2)

    has_errors = any(f.severity.value == "error" for f in report.findings)
    has_warnings = any(f.severity.value == "warning" for f in report.findings)

    if has_errors:
        sys.exit(2)
    elif has_warnings:
        sys.exit(1)
    else:
        sys.exit(0)
