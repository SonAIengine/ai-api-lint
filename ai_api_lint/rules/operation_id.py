from __future__ import annotations

import re

from ai_api_lint.models import Finding, OperationContext, Severity
from ai_api_lint.rules.base import Rule, RuleCategory

_HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options", "trace"}

_VERB_PREFIXES = (
    "get",
    "list",
    "create",
    "update",
    "delete",
    "remove",
    "search",
    "find",
    "fetch",
    "add",
    "set",
    "check",
    "verify",
    "send",
    "upload",
    "download",
    "export",
    "batch",
    "bulk",
)

_VERB_PATTERN = re.compile(r"^(" + "|".join(_VERB_PREFIXES) + r")[A-Z]")

_VALID_ID_PATTERN = re.compile(r"[a-zA-Z0-9_]+")


class AI001_OperationIdMissing(Rule):
    rule_id = "AI001"
    category = RuleCategory.OPERATION_ID
    severity = Severity.ERROR
    short_description = "Operation must have an operationId"
    weight = 1.0

    def check(self, ctx: OperationContext) -> list[Finding]:
        op_id = ctx.operation.get("operationId")
        if not op_id:
            return [
                self._finding(
                    ctx,
                    f"{ctx.method.upper()} {ctx.path} is missing operationId.",
                    suggestion="Add a descriptive operationId like 'getUsers'.",
                )
            ]
        return []


class AI002_OperationIdFormat(Rule):
    rule_id = "AI002"
    category = RuleCategory.OPERATION_ID
    severity = Severity.WARNING
    short_description = "operationId should start with a common verb"
    weight = 1.0

    def check(self, ctx: OperationContext) -> list[Finding]:
        op_id = ctx.operation.get("operationId")
        if not op_id:
            return []
        if not _VERB_PATTERN.match(op_id):
            return [
                self._finding(
                    ctx,
                    f"operationId '{op_id}' does not start with a recognized "
                    f"verb prefix followed by uppercase letter.",
                    suggestion=(
                        "Use a verb prefix like get, list, create, update, "
                        "delete (e.g. 'getUser', 'listOrders')."
                    ),
                )
            ]
        return []


class AI003_OperationIdLength(Rule):
    rule_id = "AI003"
    category = RuleCategory.OPERATION_ID
    severity = Severity.WARNING
    short_description = "operationId should not exceed 64 characters"
    weight = 1.0

    def check(self, ctx: OperationContext) -> list[Finding]:
        op_id = ctx.operation.get("operationId")
        if not op_id:
            return []
        if len(op_id) > 64:
            return [
                self._finding(
                    ctx,
                    f"operationId '{op_id}' is {len(op_id)} characters (exceeds 64 char limit).",
                    suggestion="Shorten the operationId to be more concise.",
                )
            ]
        return []


class AI004_OperationIdSpecialChars(Rule):
    rule_id = "AI004"
    category = RuleCategory.OPERATION_ID
    severity = Severity.ERROR
    short_description = "operationId must only contain alphanumeric and underscore"
    weight = 1.0

    def check(self, ctx: OperationContext) -> list[Finding]:
        op_id = ctx.operation.get("operationId")
        if not op_id:
            return []
        if not re.fullmatch(r"[a-zA-Z0-9_]+", op_id):
            return [
                self._finding(
                    ctx,
                    f"operationId '{op_id}' contains invalid characters.",
                    suggestion="Use only alphanumeric characters and underscores.",
                )
            ]
        return []


class AI005_OperationIdDuplicate(Rule):
    rule_id = "AI005"
    category = RuleCategory.OPERATION_ID
    severity = Severity.ERROR
    short_description = "operationId must be unique across the spec"
    weight = 1.0

    def check(self, ctx: OperationContext) -> list[Finding]:
        return []

    def check_global(self, spec: dict) -> list[Finding]:
        seen: dict[str, tuple[str, str]] = {}
        findings: list[Finding] = []
        paths = spec.get("paths", {})
        for path, path_item in paths.items():
            for method in path_item:
                if method.lower() not in _HTTP_METHODS:
                    continue
                operation = path_item[method]
                if not isinstance(operation, dict):
                    continue
                op_id = operation.get("operationId")
                if not op_id:
                    continue
                if op_id in seen:
                    first_path, first_method = seen[op_id]
                    findings.append(
                        Finding(
                            rule_id=self.rule_id,
                            severity=self.severity,
                            message=(
                                f"Duplicate operationId '{op_id}' — also used "
                                f"at {first_method.upper()} {first_path}."
                            ),
                            path=path,
                            method=method,
                            operation_id=op_id,
                            suggestion="Each operationId must be unique.",
                        )
                    )
                else:
                    seen[op_id] = (path, method)
        return findings
