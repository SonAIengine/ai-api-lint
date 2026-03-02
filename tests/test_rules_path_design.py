from __future__ import annotations

from ai_api_lint.models import OperationContext, Severity
from ai_api_lint.rules.path_design import (
    AI050_PathContainsVerb,
    AI051_PathTooDeep,
    AI052_InconsistentNaming,
    AI053_MissingTags,
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


class TestAI050:
    def test_verb_in_path(self):
        rule = AI050_PathContainsVerb()
        findings = rule.check(_ctx(path="/api/get/users"))
        assert len(findings) == 1
        assert findings[0].severity == Severity.WARNING

    def test_clean_path(self):
        rule = AI050_PathContainsVerb()
        findings = rule.check(_ctx(path="/api/users"))
        assert len(findings) == 0

    def test_false_positive_excluded(self):
        rule = AI050_PathContainsVerb()
        findings = rule.check(_ctx(path="/api/settings"))
        assert len(findings) == 0


class TestAI051:
    def test_shallow(self):
        rule = AI051_PathTooDeep()
        findings = rule.check(_ctx(path="/api/users"))
        assert len(findings) == 0

    def test_too_deep(self):
        rule = AI051_PathTooDeep()
        findings = rule.check(_ctx(path="/api/v1/users/profiles/settings/advanced"))
        assert len(findings) == 1

    def test_params_not_counted(self):
        rule = AI051_PathTooDeep()
        findings = rule.check(_ctx(path="/api/users/{id}/orders/{oid}"))
        assert len(findings) == 0


class TestAI052:
    def test_consistent_naming(self):
        rule = AI052_InconsistentNaming()
        spec = {"paths": {"/user-list": {}, "/user-detail": {}}}
        findings = rule.check_global(spec)
        assert len(findings) == 0

    def test_inconsistent_naming(self):
        rule = AI052_InconsistentNaming()
        spec = {"paths": {"/user_list": {}, "/userDetail": {}}}
        findings = rule.check_global(spec)
        assert len(findings) == 1

    def test_per_operation_empty(self):
        rule = AI052_InconsistentNaming()
        findings = rule.check(_ctx())
        assert len(findings) == 0


class TestAI053:
    def test_no_tags(self):
        rule = AI053_MissingTags()
        findings = rule.check(_ctx({}))
        assert len(findings) == 1
        assert findings[0].severity == Severity.WARNING

    def test_with_tags(self):
        rule = AI053_MissingTags()
        findings = rule.check(_ctx({"tags": ["users"]}))
        assert len(findings) == 0

    def test_empty_tags(self):
        rule = AI053_MissingTags()
        findings = rule.check(_ctx({"tags": []}))
        assert len(findings) == 1
