from __future__ import annotations

from ai_api_lint.models import Finding


def calculate_score(findings: list[Finding], operation_count: int) -> tuple[float, str]:
    if operation_count == 0:
        return 100.0, "N/A"

    total_penalty = sum(f.severity.penalty for f in findings)
    score = max(0.0, 100.0 - (total_penalty / operation_count))

    if score >= 90:
        grade = "Excellent"
    elif score >= 75:
        grade = "Good"
    elif score >= 60:
        grade = "Fair"
    elif score >= 40:
        grade = "Poor"
    else:
        grade = "Critical"

    return round(score, 1), grade
