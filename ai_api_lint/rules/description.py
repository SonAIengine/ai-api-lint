from __future__ import annotations

from ai_api_lint.models import Finding, OperationContext, Severity
from ai_api_lint.rules.base import Rule, RuleCategory

_USAGE_HINT_WORDS = (
    "use",
    "call",
    "returns",
    "when",
    "used to",
    "allows",
    "enables",
    "provides",
    "retrieves",
    "creates",
    "updates",
    "deletes",
)


class AI010_DescriptionMissing(Rule):
    rule_id = "AI010"
    category = RuleCategory.DESCRIPTION
    severity = Severity.ERROR
    short_description = "Operation must have a description or summary"
    weight = 1.0

    def check(self, ctx: OperationContext) -> list[Finding]:
        desc = ctx.operation.get("description", "").strip()
        summary = ctx.operation.get("summary", "").strip()
        if not desc and not summary:
            return [
                self._finding(
                    ctx,
                    f"{ctx.method.upper()} {ctx.path} has no description or summary.",
                    suggestion="Add a 'description' or 'summary' explaining this operation.",
                )
            ]
        return []


class AI011_DescriptionTooShort(Rule):
    rule_id = "AI011"
    category = RuleCategory.DESCRIPTION
    severity = Severity.WARNING
    short_description = "Description/summary should be at least 30 characters"
    weight = 1.0

    def check(self, ctx: OperationContext) -> list[Finding]:
        desc = ctx.operation.get("description", "").strip()
        summary = ctx.operation.get("summary", "").strip()
        if not desc and not summary:
            return []
        longest = max(len(desc), len(summary))
        if longest < 30:
            return [
                self._finding(
                    ctx,
                    f"Description/summary is only {longest} characters (< 30).",
                    suggestion="Write a more detailed description (30+ characters).",
                )
            ]
        return []


class AI012_DescriptionRepeatsPath(Rule):
    rule_id = "AI012"
    category = RuleCategory.DESCRIPTION
    severity = Severity.WARNING
    short_description = "Description should not just repeat the HTTP method and path"
    weight = 1.0

    def check(self, ctx: OperationContext) -> list[Finding]:
        desc = ctx.operation.get("description", "").strip()
        summary = ctx.operation.get("summary", "").strip()
        if not desc and not summary:
            return []
        method_lower = ctx.method.lower()
        path_lower = ctx.path.lower()
        for text in (desc, summary):
            if not text:
                continue
            t = text.strip().lower()
            if t in (
                f"{method_lower} {path_lower}",
                f"{method_lower}{path_lower}",
            ):
                return [
                    self._finding(
                        ctx,
                        f"Description '{text}' merely repeats the method and path.",
                        suggestion="Describe what the operation does, not its path.",
                    )
                ]
            if t == path_lower or path_lower == t:
                return [
                    self._finding(
                        ctx,
                        f"Description '{text}' is just the path.",
                        suggestion="Describe what the operation does, not its path.",
                    )
                ]
        return []


class AI013_DescriptionNoUsageHint(Rule):
    rule_id = "AI013"
    category = RuleCategory.DESCRIPTION
    severity = Severity.INFO
    short_description = "Description should include usage hint words"
    weight = 1.0

    def check(self, ctx: OperationContext) -> list[Finding]:
        desc = ctx.operation.get("description", "").strip()
        if not desc or len(desc) < 30:
            return []
        desc_lower = desc.lower()
        for word in _USAGE_HINT_WORDS:
            if word in desc_lower:
                return []
        return [
            self._finding(
                ctx,
                "Description lacks usage hint words (e.g. 'returns', 'allows', 'use').",
                suggestion=(
                    "Include words like 'returns', 'allows', 'use' to help "
                    "LLM agents understand when to call this operation."
                ),
            )
        ]


class AI014_ParamDescriptionMissing(Rule):
    rule_id = "AI014"
    category = RuleCategory.DESCRIPTION
    severity = Severity.WARNING
    short_description = "Parameters should have descriptions"
    weight = 1.0

    def check(self, ctx: OperationContext) -> list[Finding]:
        findings: list[Finding] = []
        for param in ctx.parameters:
            name = param.get("name", "<unnamed>")
            if not param.get("description", "").strip():
                findings.append(
                    self._finding(
                        ctx,
                        f"Parameter '{name}' has no description.",
                        suggestion=f"Add a 'description' for parameter '{name}'.",
                    )
                )
        return findings


class AI015_EnumNoDescription(Rule):
    rule_id = "AI015"
    category = RuleCategory.DESCRIPTION
    severity = Severity.INFO
    short_description = "Enum parameters should have a description"
    weight = 1.0

    def check(self, ctx: OperationContext) -> list[Finding]:
        findings: list[Finding] = []
        for param in ctx.parameters:
            schema = param.get("schema", {})
            if schema.get("enum") and not param.get("description", "").strip():
                name = param.get("name", "<unnamed>")
                findings.append(
                    self._finding(
                        ctx,
                        f"Parameter '{name}' has enum values but no description.",
                        suggestion=(f"Describe what each enum value means for '{name}'."),
                    )
                )
        return findings
