from __future__ import annotations

import enum
from abc import ABC, abstractmethod

from ai_api_lint.models import Finding, OperationContext, Severity


class RuleCategory(enum.Enum):
    OPERATION_ID = "operation_id"
    DESCRIPTION = "description"
    PARAMETERS = "parameters"
    REQUEST_BODY = "request_body"
    RESPONSE = "response"
    PATH_DESIGN = "path_design"
    MCP_READINESS = "mcp_readiness"


class Rule(ABC):
    rule_id: str
    category: RuleCategory
    severity: Severity
    short_description: str
    weight: float = 1.0

    @abstractmethod
    def check(self, ctx: OperationContext) -> list[Finding]: ...

    def applies_to(self, ctx: OperationContext) -> bool:
        return True

    def _finding(
        self, ctx: OperationContext, message: str, suggestion: str | None = None
    ) -> Finding:
        return Finding(
            rule_id=self.rule_id,
            severity=self.severity,
            message=message,
            path=ctx.path,
            method=ctx.method,
            operation_id=ctx.operation_id,
            suggestion=suggestion,
        )
