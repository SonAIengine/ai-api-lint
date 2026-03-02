from __future__ import annotations

from ai_api_lint.models import Finding, OperationContext, Severity
from ai_api_lint.rules.base import Rule, RuleCategory


class AI020_IdParamNoSourceHint(Rule):
    rule_id = "AI020"
    category = RuleCategory.PARAMETERS
    severity = Severity.WARNING
    short_description = "ID parameters should describe how to obtain the ID"
    weight = 1.0

    def check(self, ctx: OperationContext) -> list[Finding]:
        findings: list[Finding] = []
        for param in ctx.parameters:
            name = param.get("name", "")
            if name.lower().endswith("id") or name.lower().endswith("_id"):
                if not param.get("description", "").strip():
                    findings.append(
                        self._finding(
                            ctx,
                            f"ID parameter '{name}' has no description.",
                            suggestion=(
                                f"Describe how to obtain '{name}' (e.g. from a list endpoint)."
                            ),
                        )
                    )
        return findings


class AI021_TooManyRequiredParams(Rule):
    rule_id = "AI021"
    category = RuleCategory.PARAMETERS
    severity = Severity.WARNING
    short_description = "Too many required parameters (> 7)"
    weight = 1.0

    def check(self, ctx: OperationContext) -> list[Finding]:
        required_count = sum(1 for p in ctx.parameters if p.get("required") is True)
        if required_count > 7:
            return [
                self._finding(
                    ctx,
                    f"Operation has {required_count} required parameters (> 7).",
                    suggestion=(
                        "Consider reducing required parameters or grouping "
                        "them into a request body object."
                    ),
                )
            ]
        return []


class AI022_ParamMissingType(Rule):
    rule_id = "AI022"
    category = RuleCategory.PARAMETERS
    severity = Severity.ERROR
    short_description = "Parameter must have a schema with a type"
    weight = 1.0

    def check(self, ctx: OperationContext) -> list[Finding]:
        findings: list[Finding] = []
        for param in ctx.parameters:
            name = param.get("name", "<unnamed>")
            schema = param.get("schema")
            if not schema or not schema.get("type"):
                findings.append(
                    self._finding(
                        ctx,
                        f"Parameter '{name}' has no schema or no type defined.",
                        suggestion=f"Add a 'schema' with 'type' for parameter '{name}'.",
                    )
                )
        return findings


class AI023_ComplexParamNoExample(Rule):
    rule_id = "AI023"
    category = RuleCategory.PARAMETERS
    severity = Severity.WARNING
    short_description = "Complex parameters (object/array) should have examples"
    weight = 1.0

    def check(self, ctx: OperationContext) -> list[Finding]:
        findings: list[Finding] = []
        for param in ctx.parameters:
            schema = param.get("schema", {})
            schema_type = schema.get("type")
            if schema_type in ("object", "array"):
                has_example = param.get("example") is not None or schema.get("example") is not None
                if not has_example:
                    name = param.get("name", "<unnamed>")
                    findings.append(
                        self._finding(
                            ctx,
                            f"Complex parameter '{name}' (type: {schema_type}) has no example.",
                            suggestion=(
                                "Add an 'example' to help LLM agents "
                                "understand the expected structure."
                            ),
                        )
                    )
        return findings
