from __future__ import annotations

import argparse
import json
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
        choices=["terminal", "json", "html"],
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
    parser.add_argument("--fix", action="store_true", help="Auto-fix findings")
    parser.add_argument("--output", "-o", help="Write output to file")
    parser.add_argument(
        "--level",
        type=int,
        default=2,
        choices=[1, 2],
        help="Max fixer level: 1=safe only, 2=safe+inferred (default: 2)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview fixes without modifying")
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

    # Auto-fix
    fix_result = None
    if args.fix or args.dry_run:
        from ai_api_lint.fixer import FixEngine, create_default_fixers

        fixers = create_default_fixers()
        fix_engine = FixEngine(fixers, max_level=args.level)
        fix_result = fix_engine.fix(spec, report.findings, dry_run=args.dry_run)

        if not args.dry_run and fix_result.applied:
            # Re-lint to get updated score
            report = engine.lint(spec, spec_path=args.spec)

        # Write fixed spec
        if args.output and args.output.endswith(".json") and not args.dry_run:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(spec, f, indent=2, ensure_ascii=False)
                f.write("\n")
            print(f"Fixed spec written to {args.output}", file=sys.stderr)

    # Filter by severity
    severity_order = {"error": 0, "warning": 1, "info": 2}
    min_level = severity_order[args.severity]
    report.findings = [f for f in report.findings if severity_order[f.severity.value] <= min_level]

    # Format output
    if args.output_format == "html":
        from ai_api_lint.report import generate_html_report

        html = generate_html_report(report, fix_result=fix_result)
        output = html
    elif args.output_format == "json":
        output = format_json(report, fix_result=fix_result)
    else:
        output = format_terminal(report, fix_result=fix_result)
        if fix_result and args.dry_run:
            output += "\n  Dry-run only, no changes written"

    # Write or print output
    if args.output and not (args.output.endswith(".json") and args.fix and not args.dry_run):
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Report written to {args.output}", file=sys.stderr)
    else:
        print(output)

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
