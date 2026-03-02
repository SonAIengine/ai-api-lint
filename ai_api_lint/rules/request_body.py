from __future__ import annotations

from ai_api_lint.models import Finding, OperationContext, Severity
from ai_api_lint.rules.base import Rule, RuleCategory

_MUTATION_METHODS = {"post", "put", "patch"}


class AI030_MutationNoRequestBody(Rule):
    rule_id = "AI030"
    category = RuleCategory.REQUEST_BODY
    severity = Severity.ERROR
    short_description = "Mutation endpoints (POST/PUT/PATCH) must have a requestBody"
    weight = 1.0

    def applies_to(self, ctx: OperationContext) -> bool:
        return ctx.method.lower() in _MUTATION_METHODS

    def check(self, ctx: OperationContext) -> list[Finding]:
        if ctx.operation.get("requestBody") is None:
            return [
                self._finding(
                    ctx,
                    f"{ctx.method.upper()} {ctx.path} has no requestBody.",
                    suggestion="Add a 'requestBody' with a JSON schema.",
                )
            ]
        return []


class AI031_RequestBodyNoProperties(Rule):
    rule_id = "AI031"
    category = RuleCategory.REQUEST_BODY
    severity = Severity.WARNING
    short_description = "Request body schema should define properties"
    weight = 1.0

    def check(self, ctx: OperationContext) -> list[Finding]:
        rb = ctx.operation.get("requestBody")
        if not rb:
            return []
        content = rb.get("content", {})
        json_media = content.get("application/json", {})
        schema = json_media.get("schema", {})
        if schema and not schema.get("properties"):
            return [
                self._finding(
                    ctx,
                    "Request body schema has no 'properties' defined.",
                    suggestion="Define 'properties' in the request body schema.",
                )
            ]
        return []


class AI032_RequestBodyNoRequired(Rule):
    rule_id = "AI032"
    category = RuleCategory.REQUEST_BODY
    severity = Severity.WARNING
    short_description = "Request body schema should specify required fields"
    weight = 1.0

    def check(self, ctx: OperationContext) -> list[Finding]:
        rb = ctx.operation.get("requestBody")
        if not rb:
            return []
        content = rb.get("content", {})
        json_media = content.get("application/json", {})
        schema = json_media.get("schema", {})
        if schema.get("properties") and not schema.get("required"):
            return [
                self._finding(
                    ctx,
                    "Request body schema has properties but no 'required' list.",
                    suggestion="Add a 'required' array listing mandatory fields.",
                )
            ]
        return []


class AI033_RequestBodyNotJson(Rule):
    rule_id = "AI033"
    category = RuleCategory.REQUEST_BODY
    severity = Severity.INFO
    short_description = "Request body should support application/json"
    weight = 1.0

    def check(self, ctx: OperationContext) -> list[Finding]:
        rb = ctx.operation.get("requestBody")
        if not rb:
            return []
        content = rb.get("content", {})
        if content and "application/json" not in content:
            return [
                self._finding(
                    ctx,
                    "Request body does not include 'application/json' content type.",
                    suggestion="Add 'application/json' media type for LLM compatibility.",
                )
            ]
        return []


class AI034_RequestBodyNoDescription(Rule):
    rule_id = "AI034"
    category = RuleCategory.REQUEST_BODY
    severity = Severity.WARNING
    short_description = "Request body should have a description"
    weight = 1.0

    def check(self, ctx: OperationContext) -> list[Finding]:
        rb = ctx.operation.get("requestBody")
        if not rb:
            return []
        if not rb.get("description", "").strip():
            return [
                self._finding(
                    ctx,
                    "Request body has no 'description'.",
                    suggestion="Add a description explaining the request body structure.",
                )
            ]
        return []
