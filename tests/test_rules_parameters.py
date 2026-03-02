from __future__ import annotations

from ai_api_lint.models import OperationContext, Severity
from ai_api_lint.rules.parameters import (
    AI020_IdParamNoSourceHint,
    AI021_TooManyRequiredParams,
    AI022_ParamMissingType,
    AI023_ComplexParamNoExample,
)


def _ctx(operation=None, path="/test", method="get", parameters=None):
    op = operation or {}
    return OperationContext(
        path=path,
        method=method,
        operation=op,
        operation_id=op.get("operationId"),
        spec={},
        parameters=parameters if parameters is not None else [],
    )


class TestAI020:
    def test_id_param_no_description(self):
        rule = AI020_IdParamNoSourceHint()
        params = [{"name": "userId", "in": "path", "schema": {"type": "string"}}]
        findings = rule.check(_ctx(parameters=params))
        assert len(findings) == 1
        assert findings[0].severity == Severity.WARNING

    def test_id_param_with_description(self):
        rule = AI020_IdParamNoSourceHint()
        params = [
            {
                "name": "userId",
                "in": "path",
                "description": "Obtained from listUsers",
                "schema": {"type": "string"},
            }
        ]
        findings = rule.check(_ctx(parameters=params))
        assert len(findings) == 0

    def test_non_id_param_ignored(self):
        rule = AI020_IdParamNoSourceHint()
        params = [{"name": "limit", "in": "query", "schema": {"type": "integer"}}]
        findings = rule.check(_ctx(parameters=params))
        assert len(findings) == 0


class TestAI021:
    def test_few_required(self):
        rule = AI021_TooManyRequiredParams()
        params = [
            {"name": f"p{i}", "in": "query", "required": True, "schema": {"type": "string"}}
            for i in range(3)
        ]
        findings = rule.check(_ctx(parameters=params))
        assert len(findings) == 0

    def test_too_many_required(self):
        rule = AI021_TooManyRequiredParams()
        params = [
            {"name": f"p{i}", "in": "query", "required": True, "schema": {"type": "string"}}
            for i in range(8)
        ]
        findings = rule.check(_ctx(parameters=params))
        assert len(findings) == 1


class TestAI022:
    def test_has_type(self):
        rule = AI022_ParamMissingType()
        params = [{"name": "id", "in": "path", "schema": {"type": "string"}}]
        findings = rule.check(_ctx(parameters=params))
        assert len(findings) == 0

    def test_missing_schema(self):
        rule = AI022_ParamMissingType()
        params = [{"name": "id", "in": "path"}]
        findings = rule.check(_ctx(parameters=params))
        assert len(findings) == 1
        assert findings[0].severity == Severity.ERROR

    def test_missing_type_in_schema(self):
        rule = AI022_ParamMissingType()
        params = [{"name": "id", "in": "path", "schema": {}}]
        findings = rule.check(_ctx(parameters=params))
        assert len(findings) == 1


class TestAI023:
    def test_complex_without_example(self):
        rule = AI023_ComplexParamNoExample()
        params = [{"name": "filter", "in": "query", "schema": {"type": "object"}}]
        findings = rule.check(_ctx(parameters=params))
        assert len(findings) == 1

    def test_complex_with_example(self):
        rule = AI023_ComplexParamNoExample()
        params = [
            {
                "name": "filter",
                "in": "query",
                "schema": {"type": "object"},
                "example": {"key": "value"},
            }
        ]
        findings = rule.check(_ctx(parameters=params))
        assert len(findings) == 0

    def test_simple_type_ignored(self):
        rule = AI023_ComplexParamNoExample()
        params = [{"name": "id", "in": "path", "schema": {"type": "string"}}]
        findings = rule.check(_ctx(parameters=params))
        assert len(findings) == 0
