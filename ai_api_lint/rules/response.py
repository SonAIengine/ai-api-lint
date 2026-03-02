from __future__ import annotations

from ai_api_lint.models import Finding, OperationContext, Severity
from ai_api_lint.rules.base import Rule, RuleCategory


class AI040_NoSuccessResponse(Rule):
    rule_id = "AI040"
    category = RuleCategory.RESPONSE
    severity = Severity.ERROR
    short_description = "Operation must define at least one 2xx response"
    weight = 1.0

    def check(self, ctx: OperationContext) -> list[Finding]:
        responses = ctx.operation.get("responses", {})
        has_success = any(str(code).startswith("2") for code in responses)
        if not has_success:
            return [
                self._finding(
                    ctx,
                    "No 2xx success response defined.",
                    suggestion="Add at least one success response (e.g. '200', '201').",
                )
            ]
        return []


class AI041_SuccessResponseNoSchema(Rule):
    rule_id = "AI041"
    category = RuleCategory.RESPONSE
    severity = Severity.WARNING
    short_description = "Success response should have a schema"
    weight = 1.0

    def check(self, ctx: OperationContext) -> list[Finding]:
        responses = ctx.operation.get("responses", {})
        for code, resp in responses.items():
            if not str(code).startswith("2"):
                continue
            if not isinstance(resp, dict):
                continue
            content = resp.get("content", {})
            if not content:
                return [
                    self._finding(
                        ctx,
                        f"Success response '{code}' has no content/schema.",
                        suggestion=f"Add a schema to response '{code}'.",
                    )
                ]
            has_schema = any(
                media.get("schema") for media in content.values() if isinstance(media, dict)
            )
            if not has_schema:
                return [
                    self._finding(
                        ctx,
                        f"Success response '{code}' has content but no schema.",
                        suggestion=f"Add a schema to response '{code}'.",
                    )
                ]
            return []
        return []


class AI042_NoClientErrorResponse(Rule):
    rule_id = "AI042"
    category = RuleCategory.RESPONSE
    severity = Severity.WARNING
    short_description = "Operation should define at least one 4xx response"
    weight = 1.0

    def check(self, ctx: OperationContext) -> list[Finding]:
        responses = ctx.operation.get("responses", {})
        has_client_error = any(str(code).startswith("4") for code in responses)
        if not has_client_error:
            return [
                self._finding(
                    ctx,
                    "No 4xx client error response defined.",
                    suggestion="Add error responses (e.g. '400', '404') for error handling.",
                )
            ]
        return []


class AI043_ErrorResponseNoDescription(Rule):
    rule_id = "AI043"
    category = RuleCategory.RESPONSE
    severity = Severity.INFO
    short_description = "Error responses should have descriptions"
    weight = 1.0

    def check(self, ctx: OperationContext) -> list[Finding]:
        findings: list[Finding] = []
        responses = ctx.operation.get("responses", {})
        for code, resp in responses.items():
            code_str = str(code)
            if not (code_str.startswith("4") or code_str.startswith("5")):
                continue
            if not isinstance(resp, dict):
                continue
            if not resp.get("description", "").strip():
                findings.append(
                    self._finding(
                        ctx,
                        f"Error response '{code}' has no description.",
                        suggestion=f"Add a description for error response '{code}'.",
                    )
                )
        return findings


class AI044_GenericErrorOnly(Rule):
    rule_id = "AI044"
    category = RuleCategory.RESPONSE
    severity = Severity.INFO
    short_description = "Responses should include specific status codes, not just 'default'"
    weight = 1.0

    def check(self, ctx: OperationContext) -> list[Finding]:
        responses = ctx.operation.get("responses", {})
        if not responses:
            return []
        keys = set(responses.keys())
        if keys == {"default"}:
            return [
                self._finding(
                    ctx,
                    "Responses only contain a 'default' entry with no specific status codes.",
                    suggestion="Add specific status codes (e.g. '200', '400', '404').",
                )
            ]
        return []
