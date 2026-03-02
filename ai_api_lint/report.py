"""Single-file HTML report generator for ai-api-lint."""

from __future__ import annotations

import html
from collections import defaultdict
from datetime import datetime, timezone

from ai_api_lint.models import FixResult, LintReport, Severity

_SEVERITY_COLORS = {
    Severity.ERROR: "#ef4444",
    Severity.WARNING: "#f59e0b",
    Severity.INFO: "#3b82f6",
}

_GRADE_COLORS = {
    "Excellent": "#22c55e",
    "Good": "#84cc16",
    "Fair": "#f59e0b",
    "Poor": "#f97316",
    "Critical": "#ef4444",
    "N/A": "#6b7280",
}


def _score_arc(score: float) -> str:
    """SVG arc path for a score gauge (0-100)."""
    angle = score / 100 * 360
    if angle >= 360:
        angle = 359.99
    rad = angle * 3.14159265 / 180
    large = 1 if angle > 180 else 0
    import math

    x = 50 + 40 * math.sin(rad)
    y = 50 - 40 * math.cos(rad)
    return f"M 50 10 A 40 40 0 {large} 1 {x:.2f} {y:.2f}"


def _esc(text: str) -> str:
    return html.escape(str(text))


def generate_html_report(
    report: LintReport,
    fix_result: FixResult | None = None,
) -> str:
    """Generate a self-contained HTML report from a LintReport."""
    now = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    grade_color = _GRADE_COLORS.get(report.grade, "#6b7280")

    # Category counts
    category_counts: dict[str, int] = defaultdict(int)
    for f in report.findings:
        cat = f.rule_id[:4] if len(f.rule_id) >= 4 else f.rule_id
        # Map rule prefix to category name
        cat_map = {
            "AI00": "Operation ID",
            "AI01": "Description",
            "AI02": "Parameters",
            "AI03": "Request Body",
            "AI04": "Response",
            "AI05": "Path Design",
            "AI06": "MCP Readiness",
        }
        cat_name = cat_map.get(cat[:4], "Other")
        category_counts[cat_name] += 1

    # Severity distribution
    sev_counts = {s: 0 for s in Severity}
    for f in report.findings:
        sev_counts[f.severity] += 1
    total_findings = len(report.findings)

    # Top rules
    rule_counts: dict[str, int] = defaultdict(int)
    for f in report.findings:
        rule_counts[f.rule_id] += 1
    top_rules = sorted(rule_counts.items(), key=lambda x: -x[1])[:10]

    # Group findings by operation
    grouped: dict[tuple[str, str], list] = defaultdict(list)
    for f in report.findings:
        grouped[(f.path, f.method)].append(f)

    # Build category bars HTML
    max_cat = max(category_counts.values()) if category_counts else 1
    cat_bars_html = ""
    for cat_name, count in sorted(category_counts.items(), key=lambda x: -x[1]):
        pct = count / max_cat * 100
        cat_bars_html += (
            f'<div class="bar-row">'
            f'<span class="bar-label">{_esc(cat_name)}</span>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{pct:.0f}%"></div></div>'
            f'<span class="bar-count">{count}</span>'
            f"</div>\n"
        )

    # Severity donut SVG
    sev_svg = _build_severity_donut(sev_counts, total_findings)

    # Top rules list
    top_rules_html = ""
    for rule_id, count in top_rules:
        top_rules_html += (
            f'<div class="top-rule">'
            f'<span class="rule-id">{_esc(rule_id)}</span>'
            f'<span class="rule-count">{count}</span>'
            f"</div>\n"
        )

    # Operation table
    ops_html = ""
    for (path, method), findings in sorted(grouped.items()):
        op_id = findings[0].operation_id or ""
        findings_html = ""
        for f in findings:
            sev_color = _SEVERITY_COLORS[f.severity]
            findings_html += (
                f'<div class="finding">'
                f'<span class="sev-dot" style="background:{sev_color}"></span>'
                f'<span class="finding-rule">{_esc(f.rule_id)}</span>'
                f'<span class="finding-msg">{_esc(f.message)}</span>'
                f"</div>\n"
            )
        ops_html += (
            f'<details class="op-section">'
            f"<summary>"
            f'<span class="op-method op-{_esc(method)}">{_esc(method.upper())}</span>'
            f'<span class="op-path">{_esc(path)}</span>'
            f'<span class="op-id">{_esc(op_id)}</span>'
            f'<span class="op-count">{len(findings)}</span>'
            f"</summary>"
            f'<div class="op-findings">{findings_html}</div>'
            f"</details>\n"
        )

    # Fix result section
    fix_html = ""
    if fix_result is not None:
        fix_html = (
            '<div class="section fix-section">'
            "<h2>Fix Results</h2>"
            f'<div class="fix-stats">'
            f'<div class="fix-stat applied">'
            f'<span class="fix-num">{len(fix_result.applied)}</span>'
            f'<span class="fix-label">Applied</span></div>'
            f'<div class="fix-stat skipped">'
            f'<span class="fix-num">{len(fix_result.skipped)}</span>'
            f'<span class="fix-label">Skipped</span></div>'
            f"</div>"
            "</div>"
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ai-api-lint Report — {_esc(report.spec_path)}</title>
<style>
:root {{
  --bg: #ffffff; --fg: #1a1a2e; --card: #f8f9fa; --border: #e2e8f0;
  --muted: #64748b; --accent: #3b82f6;
}}
@media (prefers-color-scheme: dark) {{
  :root {{
    --bg: #0f172a; --fg: #e2e8f0; --card: #1e293b; --border: #334155;
    --muted: #94a3b8; --accent: #60a5fa;
  }}
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
  background: var(--bg); color: var(--fg); line-height: 1.6;
  max-width: 960px; margin: 0 auto; padding: 2rem 1rem;
}}
h1 {{ font-size: 1.5rem; margin-bottom: .25rem; }}
h2 {{ font-size: 1.1rem; margin-bottom: .75rem; color: var(--muted); font-weight: 600; }}
.meta {{ color: var(--muted); font-size: .85rem; margin-bottom: 1.5rem; }}
.header {{ display: flex; align-items: center; gap: 2rem; margin-bottom: 2rem; flex-wrap: wrap; }}
.score-gauge {{ flex-shrink: 0; }}
.score-gauge svg {{ width: 120px; height: 120px; }}
.score-text {{ font-size: 1.8rem; font-weight: 700; }}
.grade {{ font-size: 1rem; font-weight: 600; }}
.section {{ background: var(--card); border-radius: 8px; padding: 1.25rem; margin-bottom: 1.25rem; }}
.grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1.25rem; }}
@media (max-width: 640px) {{ .grid {{ grid-template-columns: 1fr; }} }}
.bar-row {{ display: flex; align-items: center; gap: .5rem; margin-bottom: .4rem; }}
.bar-label {{ width: 110px; font-size: .85rem; text-align: right; color: var(--muted); }}
.bar-track {{ flex: 1; height: 18px; background: var(--border); border-radius: 4px; overflow: hidden; }}
.bar-fill {{ height: 100%; background: var(--accent); border-radius: 4px; transition: width .3s; }}
.bar-count {{ width: 40px; font-size: .85rem; font-weight: 600; }}
.donut-center {{ text-anchor: middle; dominant-baseline: central; fill: var(--fg); }}
.sev-legend {{ display: flex; gap: 1rem; margin-top: .75rem; flex-wrap: wrap; }}
.sev-item {{ display: flex; align-items: center; gap: .3rem; font-size: .85rem; }}
.sev-dot {{ width: 10px; height: 10px; border-radius: 50%; display: inline-block; }}
.top-rule {{ display: flex; justify-content: space-between; padding: .3rem 0;
  border-bottom: 1px solid var(--border); font-size: .9rem; }}
.top-rule:last-child {{ border-bottom: none; }}
.rule-id {{ font-weight: 600; font-family: monospace; }}
.rule-count {{ color: var(--muted); }}
.op-section {{ border-bottom: 1px solid var(--border); }}
.op-section:last-child {{ border-bottom: none; }}
.op-section summary {{
  display: flex; align-items: center; gap: .75rem; padding: .6rem 0;
  cursor: pointer; font-size: .9rem; list-style: none;
}}
.op-section summary::-webkit-details-marker {{ display: none; }}
.op-section summary::before {{ content: '\\25B6'; font-size: .7rem; color: var(--muted); transition: transform .2s; }}
.op-section[open] summary::before {{ transform: rotate(90deg); }}
.op-method {{
  font-weight: 700; font-size: .75rem; padding: 2px 6px; border-radius: 3px;
  text-transform: uppercase; min-width: 52px; text-align: center;
}}
.op-get {{ background: #dbeafe; color: #1d4ed8; }}
.op-post {{ background: #dcfce7; color: #15803d; }}
.op-put {{ background: #fef3c7; color: #a16207; }}
.op-patch {{ background: #fef3c7; color: #a16207; }}
.op-delete {{ background: #fee2e2; color: #b91c1c; }}
.op-path {{ flex: 1; font-family: monospace; font-size: .85rem; }}
.op-id {{ color: var(--muted); font-size: .8rem; }}
.op-count {{
  background: var(--border); border-radius: 12px; padding: 0 8px;
  font-size: .8rem; font-weight: 600;
}}
.op-findings {{ padding: .5rem 0 .75rem 1.5rem; }}
.finding {{ display: flex; align-items: baseline; gap: .5rem; padding: .2rem 0; font-size: .85rem; }}
.finding-rule {{ font-family: monospace; font-weight: 600; min-width: 48px; }}
.finding-msg {{ color: var(--muted); }}
.fix-section {{ text-align: center; }}
.fix-stats {{ display: flex; justify-content: center; gap: 2rem; }}
.fix-stat {{ text-align: center; }}
.fix-num {{ display: block; font-size: 2rem; font-weight: 700; }}
.fix-stat.applied .fix-num {{ color: #22c55e; }}
.fix-stat.skipped .fix-num {{ color: var(--muted); }}
.fix-label {{ font-size: .85rem; color: var(--muted); }}
@media print {{
  body {{ max-width: 100%; }}
  .op-section {{ break-inside: avoid; }}
  details {{ open: true; }}
}}
</style>
</head>
<body>
<div class="header">
  <div class="score-gauge">
    <svg viewBox="0 0 100 100">
      <circle cx="50" cy="50" r="40" fill="none" stroke="var(--border)" stroke-width="8"/>
      <path d="{_score_arc(report.overall_score)}" fill="none" stroke="{grade_color}" stroke-width="8" stroke-linecap="round"/>
      <text x="50" y="46" class="donut-center score-text" font-size="20">{report.overall_score:.0f}</text>
      <text x="50" y="64" class="donut-center grade" font-size="10" fill="{grade_color}">{_esc(report.grade)}</text>
    </svg>
  </div>
  <div>
    <h1>{_esc(report.spec_path)}</h1>
    <div class="meta">{now} &middot; {report.total_operations} operations &middot; {total_findings} findings</div>
  </div>
</div>

<div class="grid">
  <div class="section">
    <h2>Categories</h2>
    {cat_bars_html}
  </div>
  <div class="section">
    <h2>Severity</h2>
    {sev_svg}
  </div>
</div>

<div class="section">
  <h2>Top Rules</h2>
  {top_rules_html if top_rules_html else '<div style="color:var(--muted)">No findings</div>'}
</div>

{fix_html}

<div class="section">
  <h2>Operations ({len(grouped)})</h2>
  {ops_html if ops_html else '<div style="color:var(--muted)">No findings</div>'}
</div>

<div style="text-align:center;color:var(--muted);font-size:.8rem;margin-top:2rem;">
  Generated by ai-api-lint v0.1.0
</div>
</body>
</html>"""


def _build_severity_donut(sev_counts: dict[Severity, int], total: int) -> str:
    """Build an SVG donut chart for severity distribution."""
    if total == 0:
        return '<div style="color:var(--muted)">No findings</div>'

    import math

    colors = {
        Severity.ERROR: "#ef4444",
        Severity.WARNING: "#f59e0b",
        Severity.INFO: "#3b82f6",
    }
    labels = {
        Severity.ERROR: "Error",
        Severity.WARNING: "Warning",
        Severity.INFO: "Info",
    }

    paths = ""
    offset = 0
    for sev in (Severity.ERROR, Severity.WARNING, Severity.INFO):
        count = sev_counts[sev]
        if count == 0:
            continue
        pct = count / total
        angle = pct * 360
        if angle >= 360:
            angle = 359.99
        start_rad = offset * math.pi / 180
        end_rad = (offset + angle) * math.pi / 180
        x1 = 50 + 35 * math.sin(start_rad)
        y1 = 50 - 35 * math.cos(start_rad)
        x2 = 50 + 35 * math.sin(end_rad)
        y2 = 50 - 35 * math.cos(end_rad)
        large = 1 if angle > 180 else 0
        paths += (
            f'<path d="M {x1:.2f} {y1:.2f} A 35 35 0 {large} 1 {x2:.2f} {y2:.2f}" '
            f'fill="none" stroke="{colors[sev]}" stroke-width="12"/>\n'
        )
        offset += angle

    legend = ""
    for sev in (Severity.ERROR, Severity.WARNING, Severity.INFO):
        count = sev_counts[sev]
        pct = count / total * 100 if total else 0
        legend += (
            f'<span class="sev-item">'
            f'<span class="sev-dot" style="background:{colors[sev]}"></span>'
            f"{labels[sev]}: {count} ({pct:.0f}%)</span>\n"
        )

    return (
        f'<svg viewBox="0 0 100 100" style="width:100px;height:100px;margin:0 auto;display:block;">'
        f'<circle cx="50" cy="50" r="35" fill="none" stroke="var(--border)" stroke-width="12"/>'
        f"{paths}"
        f'<text x="50" y="50" class="donut-center" font-size="14" font-weight="700">{total}</text>'
        f"</svg>"
        f'<div class="sev-legend" style="justify-content:center">{legend}</div>'
    )
