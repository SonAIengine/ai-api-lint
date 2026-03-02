from __future__ import annotations

import keyword
import re

from ai_api_lint.models import Finding, OperationContext, Severity
from ai_api_lint.rules.base import Rule, RuleCategory

_HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options", "trace"}

_VERB_PREFIX_RE = re.compile(r"^([a-z]+)[A-Z]")


class AI060_PythonReservedWord(Rule):
    rule_id = "AI060"
    category = RuleCategory.MCP_READINESS
    severity = Severity.ERROR
    short_description = "operationId must not be a Python reserved keyword"
    weight = 1.0

    def check(self, ctx: OperationContext) -> list[Finding]:
        op_id = ctx.operation.get("operationId")
        if not op_id:
            return []
        if keyword.iskeyword(op_id):
            return [
                self._finding(
                    ctx,
                    f"operationId '{op_id}' is a Python reserved keyword.",
                    suggestion="Rename the operationId to avoid Python keywords.",
                )
            ]
        return []


class AI061_TooManyParams(Rule):
    rule_id = "AI061"
    category = RuleCategory.MCP_READINESS
    severity = Severity.WARNING
    short_description = "Operation should not have more than 15 parameters"
    weight = 1.0

    def check(self, ctx: OperationContext) -> list[Finding]:
        if len(ctx.parameters) > 15:
            return [
                self._finding(
                    ctx,
                    f"Operation has {len(ctx.parameters)} parameters (> 15).",
                    suggestion="Reduce parameters or group them in a request body.",
                )
            ]
        return []


class AI062_TooManyOperations(Rule):
    rule_id = "AI062"
    category = RuleCategory.MCP_READINESS
    severity = Severity.INFO
    short_description = "Spec should not have more than 40 operations"
    weight = 1.0

    def check(self, ctx: OperationContext) -> list[Finding]:
        return []

    def check_global(self, spec: dict) -> list[Finding]:
        count = 0
        paths = spec.get("paths", {})
        for path_item in paths.values():
            for method in path_item:
                if method.lower() in _HTTP_METHODS:
                    if isinstance(path_item[method], dict):
                        count += 1
        if count > 40:
            return [
                Finding(
                    rule_id=self.rule_id,
                    severity=self.severity,
                    message=f"Spec has {count} operations (> 40).",
                    path="/",
                    method="*",
                    suggestion="Split into smaller specs or use tags to subset.",
                )
            ]
        return []


class AI063_InconsistentVerbPatterns(Rule):
    rule_id = "AI063"
    category = RuleCategory.MCP_READINESS
    severity = Severity.INFO
    short_description = "operationId verb prefixes should be consistent"
    weight = 1.0

    def check(self, ctx: OperationContext) -> list[Finding]:
        return []

    def check_global(self, spec: dict) -> list[Finding]:
        verbs: set[str] = set()
        paths = spec.get("paths", {})
        for path_item in paths.values():
            for method in path_item:
                if method.lower() not in _HTTP_METHODS:
                    continue
                operation = path_item[method]
                if not isinstance(operation, dict):
                    continue
                op_id = operation.get("operationId")
                if not op_id:
                    continue
                m = _VERB_PREFIX_RE.match(op_id)
                if m:
                    verbs.add(m.group(1))
        if len(verbs) > 5:
            return [
                Finding(
                    rule_id=self.rule_id,
                    severity=self.severity,
                    message=(
                        f"Found {len(verbs)} different verb prefixes in operationIds: "
                        f"{', '.join(sorted(verbs))}."
                    ),
                    path="/",
                    method="*",
                    suggestion="Standardize on a smaller set of verb prefixes.",
                )
            ]
        return []


class AI064_NoSecurityScheme(Rule):
    rule_id = "AI064"
    category = RuleCategory.MCP_READINESS
    severity = Severity.WARNING
    short_description = "Spec should define security schemes"
    weight = 1.0

    def check(self, ctx: OperationContext) -> list[Finding]:
        return []

    def check_global(self, spec: dict) -> list[Finding]:
        # OAS3: components.securitySchemes
        components = spec.get("components", {})
        if components.get("securitySchemes"):
            return []
        # OAS2: securityDefinitions
        if spec.get("securityDefinitions"):
            return []
        # Top-level security array
        if spec.get("security"):
            return []
        return [
            Finding(
                rule_id=self.rule_id,
                severity=self.severity,
                message="No security scheme defined in the spec.",
                path="/",
                method="*",
                suggestion=(
                    "Add 'components.securitySchemes' (OAS3) or 'securityDefinitions' (OAS2)."
                ),
            )
        ]
