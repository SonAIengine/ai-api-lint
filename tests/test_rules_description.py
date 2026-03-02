from __future__ import annotations

from ai_api_lint.models import OperationContext, Severity
from ai_api_lint.rules.description import (
    AI010_DescriptionMissing,
    AI011_DescriptionTooShort,
    AI012_DescriptionRepeatsPath,
    AI013_DescriptionNoUsageHint,
    AI014_ParamDescriptionMissing,
    AI015_EnumNoDescription,
)


def _ctx(operation=None, path="/test", method="get", parameters=None):
    op = operation or {}
    return OperationContext(
        path=path,
        method=method,
        operation=op,
        operation_id=op.get("operationId"),
        spec={},
        parameters=parameters if parameters is not None else op.get("parameters", []),
    )


class TestAI010:
    def test_missing_both(self):
        rule = AI010_DescriptionMissing()
        findings = rule.check(_ctx({}))
        assert len(findings) == 1
        assert findings[0].severity == Severity.ERROR

    def test_has_description(self):
        rule = AI010_DescriptionMissing()
        findings = rule.check(_ctx({"description": "Fetch all users from the system"}))
        assert len(findings) == 0

    def test_has_summary_only(self):
        rule = AI010_DescriptionMissing()
        findings = rule.check(_ctx({"summary": "Fetch all users from the system"}))
        assert len(findings) == 0


class TestAI011:
    def test_too_short(self):
        rule = AI011_DescriptionTooShort()
        findings = rule.check(_ctx({"description": "Get users"}))
        assert len(findings) == 1
        assert findings[0].severity == Severity.WARNING

    def test_long_enough(self):
        rule = AI011_DescriptionTooShort()
        findings = rule.check(
            _ctx({"description": "Retrieve a paginated list of all registered users"})
        )
        assert len(findings) == 0

    def test_no_description_skips(self):
        rule = AI011_DescriptionTooShort()
        findings = rule.check(_ctx({}))
        assert len(findings) == 0


class TestAI012:
    def test_repeats_path(self):
        rule = AI012_DescriptionRepeatsPath()
        findings = rule.check(_ctx({"description": "GET /users"}, path="/users", method="get"))
        assert len(findings) == 1

    def test_normal_description(self):
        rule = AI012_DescriptionRepeatsPath()
        findings = rule.check(
            _ctx({"description": "Retrieve a list of all users"}, path="/users", method="get")
        )
        assert len(findings) == 0


class TestAI013:
    def test_no_hint(self):
        rule = AI013_DescriptionNoUsageHint()
        findings = rule.check(
            _ctx({"description": "A lengthy description about the API endpoint for data"})
        )
        assert len(findings) == 1
        assert findings[0].severity == Severity.INFO

    def test_has_hint(self):
        rule = AI013_DescriptionNoUsageHint()
        findings = rule.check(
            _ctx({"description": "Use this endpoint to retrieve all users from the database"})
        )
        assert len(findings) == 0


class TestAI014:
    def test_param_no_description(self):
        rule = AI014_ParamDescriptionMissing()
        params = [{"name": "userId", "in": "path", "schema": {"type": "string"}}]
        findings = rule.check(_ctx(parameters=params))
        assert len(findings) == 1

    def test_param_with_description(self):
        rule = AI014_ParamDescriptionMissing()
        params = [
            {
                "name": "userId",
                "in": "path",
                "description": "The user ID",
                "schema": {"type": "string"},
            }
        ]
        findings = rule.check(_ctx(parameters=params))
        assert len(findings) == 0


class TestAI015:
    def test_enum_no_description(self):
        rule = AI015_EnumNoDescription()
        params = [
            {"name": "status", "in": "query", "schema": {"type": "string", "enum": ["a", "b"]}}
        ]
        findings = rule.check(_ctx(parameters=params))
        assert len(findings) == 1

    def test_enum_with_description(self):
        rule = AI015_EnumNoDescription()
        params = [
            {
                "name": "status",
                "in": "query",
                "description": "Filter by status: a=active, b=blocked",
                "schema": {"type": "string", "enum": ["a", "b"]},
            }
        ]
        findings = rule.check(_ctx(parameters=params))
        assert len(findings) == 0
