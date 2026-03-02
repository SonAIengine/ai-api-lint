from __future__ import annotations

from ai_api_lint.models import OperationContext, Severity
from ai_api_lint.rules.request_body import (
    AI030_MutationNoRequestBody,
    AI031_RequestBodyNoProperties,
    AI032_RequestBodyNoRequired,
    AI033_RequestBodyNotJson,
    AI034_RequestBodyNoDescription,
)


def _ctx(operation=None, path="/test", method="post"):
    op = operation or {}
    return OperationContext(
        path=path,
        method=method,
        operation=op,
        operation_id=op.get("operationId"),
        spec={},
        parameters=[],
    )


class TestAI030:
    def test_post_no_body(self):
        rule = AI030_MutationNoRequestBody()
        findings = rule.check(_ctx({}, method="post"))
        assert len(findings) == 1
        assert findings[0].severity == Severity.ERROR

    def test_post_with_body(self):
        rule = AI030_MutationNoRequestBody()
        findings = rule.check(_ctx({"requestBody": {"content": {}}}, method="post"))
        assert len(findings) == 0

    def test_get_no_body_ok(self):
        rule = AI030_MutationNoRequestBody()
        assert not rule.applies_to(_ctx({}, method="get"))


class TestAI031:
    def test_no_properties(self):
        rule = AI031_RequestBodyNoProperties()
        op = {"requestBody": {"content": {"application/json": {"schema": {"type": "object"}}}}}
        findings = rule.check(_ctx(op))
        assert len(findings) == 1

    def test_with_properties(self):
        rule = AI031_RequestBodyNoProperties()
        op = {
            "requestBody": {
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {"name": {"type": "string"}},
                        }
                    }
                }
            }
        }
        findings = rule.check(_ctx(op))
        assert len(findings) == 0


class TestAI032:
    def test_no_required(self):
        rule = AI032_RequestBodyNoRequired()
        op = {
            "requestBody": {
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {"name": {"type": "string"}},
                        }
                    }
                }
            }
        }
        findings = rule.check(_ctx(op))
        assert len(findings) == 1

    def test_with_required(self):
        rule = AI032_RequestBodyNoRequired()
        op = {
            "requestBody": {
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {"name": {"type": "string"}},
                            "required": ["name"],
                        }
                    }
                }
            }
        }
        findings = rule.check(_ctx(op))
        assert len(findings) == 0


class TestAI033:
    def test_not_json(self):
        rule = AI033_RequestBodyNotJson()
        op = {"requestBody": {"content": {"text/plain": {"schema": {"type": "string"}}}}}
        findings = rule.check(_ctx(op))
        assert len(findings) == 1
        assert findings[0].severity == Severity.INFO

    def test_json_present(self):
        rule = AI033_RequestBodyNotJson()
        op = {"requestBody": {"content": {"application/json": {"schema": {}}}}}
        findings = rule.check(_ctx(op))
        assert len(findings) == 0


class TestAI034:
    def test_no_description(self):
        rule = AI034_RequestBodyNoDescription()
        op = {"requestBody": {"content": {}}}
        findings = rule.check(_ctx(op))
        assert len(findings) == 1

    def test_with_description(self):
        rule = AI034_RequestBodyNoDescription()
        op = {"requestBody": {"description": "User data", "content": {}}}
        findings = rule.check(_ctx(op))
        assert len(findings) == 0

    def test_no_body_skips(self):
        rule = AI034_RequestBodyNoDescription()
        findings = rule.check(_ctx({}))
        assert len(findings) == 0
