from __future__ import annotations

from ai_api_lint.models import OperationContext, Severity
from ai_api_lint.rules.response import (
    AI040_NoSuccessResponse,
    AI041_SuccessResponseNoSchema,
    AI042_NoClientErrorResponse,
    AI043_ErrorResponseNoDescription,
    AI044_GenericErrorOnly,
)


def _ctx(operation=None, path="/test", method="get"):
    op = operation or {}
    return OperationContext(
        path=path,
        method=method,
        operation=op,
        operation_id=op.get("operationId"),
        spec={},
        parameters=[],
    )


class TestAI040:
    def test_no_2xx(self):
        rule = AI040_NoSuccessResponse()
        findings = rule.check(_ctx({"responses": {"400": {"description": "Error"}}}))
        assert len(findings) == 1
        assert findings[0].severity == Severity.ERROR

    def test_has_200(self):
        rule = AI040_NoSuccessResponse()
        findings = rule.check(_ctx({"responses": {"200": {"description": "OK"}}}))
        assert len(findings) == 0

    def test_has_201(self):
        rule = AI040_NoSuccessResponse()
        findings = rule.check(_ctx({"responses": {"201": {"description": "Created"}}}))
        assert len(findings) == 0


class TestAI041:
    def test_no_schema(self):
        rule = AI041_SuccessResponseNoSchema()
        findings = rule.check(_ctx({"responses": {"200": {"description": "OK"}}}))
        assert len(findings) == 1
        assert findings[0].severity == Severity.WARNING

    def test_with_schema(self):
        rule = AI041_SuccessResponseNoSchema()
        op = {
            "responses": {
                "200": {
                    "description": "OK",
                    "content": {"application/json": {"schema": {"type": "object"}}},
                }
            }
        }
        findings = rule.check(_ctx(op))
        assert len(findings) == 0


class TestAI042:
    def test_no_4xx(self):
        rule = AI042_NoClientErrorResponse()
        findings = rule.check(_ctx({"responses": {"200": {"description": "OK"}}}))
        assert len(findings) == 1

    def test_has_400(self):
        rule = AI042_NoClientErrorResponse()
        findings = rule.check(
            _ctx({"responses": {"200": {"description": "OK"}, "400": {"description": "Error"}}})
        )
        assert len(findings) == 0


class TestAI043:
    def test_error_no_description(self):
        rule = AI043_ErrorResponseNoDescription()
        findings = rule.check(_ctx({"responses": {"400": {}, "200": {"description": "OK"}}}))
        assert len(findings) == 1

    def test_error_with_description(self):
        rule = AI043_ErrorResponseNoDescription()
        findings = rule.check(_ctx({"responses": {"400": {"description": "Bad request"}}}))
        assert len(findings) == 0


class TestAI044:
    def test_generic_only(self):
        rule = AI044_GenericErrorOnly()
        findings = rule.check(_ctx({"responses": {"default": {"description": "Error"}}}))
        assert len(findings) == 1
        assert findings[0].severity == Severity.INFO

    def test_specific_codes(self):
        rule = AI044_GenericErrorOnly()
        findings = rule.check(
            _ctx({"responses": {"200": {"description": "OK"}, "400": {"description": "Error"}}})
        )
        assert len(findings) == 0
