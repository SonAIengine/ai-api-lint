from __future__ import annotations

from ai_api_lint.models import OperationContext, Severity
from ai_api_lint.rules.mcp_readiness import (
    AI060_PythonReservedWord,
    AI061_TooManyParams,
    AI062_TooManyOperations,
    AI063_InconsistentVerbPatterns,
    AI064_NoSecurityScheme,
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


class TestAI060:
    def test_reserved_word(self):
        rule = AI060_PythonReservedWord()
        findings = rule.check(_ctx({"operationId": "class"}))
        assert len(findings) == 1
        assert findings[0].severity == Severity.ERROR

    def test_normal_id(self):
        rule = AI060_PythonReservedWord()
        findings = rule.check(_ctx({"operationId": "getUsers"}))
        assert len(findings) == 0

    def test_no_id_skips(self):
        rule = AI060_PythonReservedWord()
        findings = rule.check(_ctx({}))
        assert len(findings) == 0


class TestAI061:
    def test_few_params(self):
        rule = AI061_TooManyParams()
        params = [{"name": f"p{i}", "in": "query", "schema": {"type": "string"}} for i in range(5)]
        findings = rule.check(_ctx(parameters=params))
        assert len(findings) == 0

    def test_too_many(self):
        rule = AI061_TooManyParams()
        params = [{"name": f"p{i}", "in": "query", "schema": {"type": "string"}} for i in range(16)]
        findings = rule.check(_ctx(parameters=params))
        assert len(findings) == 1


class TestAI062:
    def test_few_operations(self):
        rule = AI062_TooManyOperations()
        spec = {"paths": {f"/p{i}": {"get": {}} for i in range(10)}}
        findings = rule.check_global(spec)
        assert len(findings) == 0

    def test_many_operations(self):
        rule = AI062_TooManyOperations()
        spec = {"paths": {f"/p{i}": {"get": {}, "post": {}} for i in range(25)}}
        findings = rule.check_global(spec)
        assert len(findings) == 1

    def test_per_operation_empty(self):
        rule = AI062_TooManyOperations()
        findings = rule.check(_ctx())
        assert len(findings) == 0


class TestAI063:
    def test_consistent_verbs(self):
        rule = AI063_InconsistentVerbPatterns()
        spec = {
            "paths": {
                "/a": {"get": {"operationId": "getA"}},
                "/b": {"get": {"operationId": "getB"}},
                "/c": {"post": {"operationId": "createC"}},
            }
        }
        findings = rule.check_global(spec)
        assert len(findings) == 0

    def test_many_different_verbs(self):
        rule = AI063_InconsistentVerbPatterns()
        verbs = ["getA", "createB", "fetchC", "removeD", "searchE", "updateF"]
        spec = {"paths": {f"/p{i}": {"get": {"operationId": v}} for i, v in enumerate(verbs)}}
        findings = rule.check_global(spec)
        assert len(findings) == 1


class TestAI064:
    def test_no_security(self):
        rule = AI064_NoSecurityScheme()
        findings = rule.check_global({})
        assert len(findings) == 1
        assert findings[0].severity == Severity.WARNING

    def test_oas3_security_schemes(self):
        rule = AI064_NoSecurityScheme()
        spec = {"components": {"securitySchemes": {"bearer": {"type": "http"}}}}
        findings = rule.check_global(spec)
        assert len(findings) == 0

    def test_top_level_security(self):
        rule = AI064_NoSecurityScheme()
        spec = {"security": [{"apiKey": []}]}
        findings = rule.check_global(spec)
        assert len(findings) == 0
