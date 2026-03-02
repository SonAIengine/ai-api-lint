from __future__ import annotations

import enum
from dataclasses import dataclass, field


class Severity(enum.Enum):
    ERROR = "error"  # 20 point penalty
    WARNING = "warning"  # 8 point penalty
    INFO = "info"  # 2 point penalty

    @property
    def penalty(self) -> int:
        return {Severity.ERROR: 20, Severity.WARNING: 8, Severity.INFO: 2}[self]


@dataclass
class Finding:
    rule_id: str
    severity: Severity
    message: str
    path: str
    method: str
    operation_id: str | None = None
    suggestion: str | None = None


@dataclass
class OperationContext:
    path: str
    method: str
    operation: dict
    operation_id: str | None
    spec: dict
    parameters: list[dict] = field(default_factory=list)


@dataclass
class LintReport:
    spec_path: str
    total_operations: int
    findings: list[Finding] = field(default_factory=list)
    overall_score: float = 100.0
    grade: str = "Excellent"
