from __future__ import annotations

from ai_api_lint.models import OperationContext, Severity
from ai_api_lint.rules.operation_id import (
    AI001_OperationIdMissing,
    AI002_OperationIdFormat,
    AI003_OperationIdLength,
    AI004_OperationIdSpecialChars,
    AI005_OperationIdDuplicate,
)


def _ctx(operation=None, path="/test", method="get", spec=None):
    op = operation or {}
    return OperationContext(
        path=path,
        method=method,
        operation=op,
        operation_id=op.get("operationId"),
        spec=spec or {},
        parameters=op.get("parameters", []),
    )


class TestAI001:
    def test_missing(self):
        rule = AI001_OperationIdMissing()
        findings = rule.check(_ctx({}))
        assert len(findings) == 1
        assert findings[0].severity == Severity.ERROR

    def test_empty_string(self):
        rule = AI001_OperationIdMissing()
        findings = rule.check(_ctx({"operationId": ""}))
        assert len(findings) == 1

    def test_present(self):
        rule = AI001_OperationIdMissing()
        findings = rule.check(_ctx({"operationId": "getUsers"}))
        assert len(findings) == 0


class TestAI002:
    def test_good_format(self):
        rule = AI002_OperationIdFormat()
        findings = rule.check(_ctx({"operationId": "getUsers"}))
        assert len(findings) == 0

    def test_bad_format(self):
        rule = AI002_OperationIdFormat()
        findings = rule.check(_ctx({"operationId": "users"}))
        assert len(findings) == 1
        assert findings[0].severity == Severity.WARNING

    def test_no_operationid_skips(self):
        rule = AI002_OperationIdFormat()
        findings = rule.check(_ctx({}))
        assert len(findings) == 0


class TestAI003:
    def test_short_ok(self):
        rule = AI003_OperationIdLength()
        findings = rule.check(_ctx({"operationId": "getUsers"}))
        assert len(findings) == 0

    def test_too_long(self):
        rule = AI003_OperationIdLength()
        long_id = "a" * 65
        findings = rule.check(_ctx({"operationId": long_id}))
        assert len(findings) == 1


class TestAI004:
    def test_valid_chars(self):
        rule = AI004_OperationIdSpecialChars()
        findings = rule.check(_ctx({"operationId": "get_users_v2"}))
        assert len(findings) == 0

    def test_special_chars(self):
        rule = AI004_OperationIdSpecialChars()
        findings = rule.check(_ctx({"operationId": "update!!!data"}))
        assert len(findings) == 1
        assert findings[0].severity == Severity.ERROR


class TestAI005:
    def test_no_duplicates(self):
        spec = {
            "paths": {
                "/a": {"get": {"operationId": "getA"}},
                "/b": {"get": {"operationId": "getB"}},
            }
        }
        rule = AI005_OperationIdDuplicate()
        findings = rule.check_global(spec)
        assert len(findings) == 0

    def test_duplicates(self):
        spec = {
            "paths": {
                "/a": {"get": {"operationId": "getItems"}},
                "/b": {"get": {"operationId": "getItems"}},
            }
        }
        rule = AI005_OperationIdDuplicate()
        findings = rule.check_global(spec)
        assert len(findings) >= 1
        assert findings[0].severity == Severity.ERROR

    def test_per_operation_returns_empty(self):
        rule = AI005_OperationIdDuplicate()
        findings = rule.check(_ctx({"operationId": "test"}))
        assert len(findings) == 0
