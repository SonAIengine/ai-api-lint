"""Tests for the fixer framework and integration."""

from __future__ import annotations

import copy

from ai_api_lint.fixer import FixEngine, create_default_fixers
from ai_api_lint.fixer.engine import FixEngine as FixEngineClass
from ai_api_lint.fixer.fixers import FixAI022, FixAI034, FixAI042
from ai_api_lint.models import Finding, Severity


def _minimal_spec(**overrides: dict) -> dict:
    """Build a minimal OpenAPI spec for testing."""
    spec: dict = {
        "openapi": "3.0.0",
        "info": {"title": "Test", "version": "1.0"},
        "paths": {
            "/items": {
                "get": {
                    "operationId": "listItems",
                    "summary": "List items",
                    "responses": {"200": {"description": "OK"}},
                }
            }
        },
    }
    for k, v in overrides.items():
        spec[k] = v
    return spec


class TestFixAI042:
    def test_adds_400_when_no_4xx(self) -> None:
        spec = _minimal_spec()
        finding = Finding(
            rule_id="AI042",
            severity=Severity.WARNING,
            message="No 4xx client error response defined.",
            path="/items",
            method="get",
        )
        fixer = FixAI042()
        assert fixer.fix(spec, finding) is True
        responses = spec["paths"]["/items"]["get"]["responses"]
        assert "400" in responses
        assert responses["400"]["description"] == "Bad Request"

    def test_skips_when_4xx_exists(self) -> None:
        spec = _minimal_spec()
        spec["paths"]["/items"]["get"]["responses"]["404"] = {"description": "Not Found"}
        finding = Finding(
            rule_id="AI042",
            severity=Severity.WARNING,
            message="No 4xx client error response defined.",
            path="/items",
            method="get",
        )
        fixer = FixAI042()
        assert fixer.fix(spec, finding) is False


class TestFixAI034:
    def test_adds_description(self) -> None:
        spec = _minimal_spec()
        spec["paths"]["/items"]["post"] = {
            "operationId": "createItem",
            "summary": "Create an item",
            "requestBody": {
                "content": {"application/json": {"schema": {"type": "object"}}},
            },
            "responses": {"201": {"description": "Created"}},
        }
        finding = Finding(
            rule_id="AI034",
            severity=Severity.WARNING,
            message="Request body has no 'description'.",
            path="/items",
            method="post",
        )
        fixer = FixAI034()
        assert fixer.fix(spec, finding) is True
        assert "Create an item" in spec["paths"]["/items"]["post"]["requestBody"]["description"]


class TestFixAI022:
    def test_adds_schema(self) -> None:
        spec = _minimal_spec()
        spec["paths"]["/items"]["get"]["parameters"] = [
            {"name": "filter", "in": "query"},
        ]
        finding = Finding(
            rule_id="AI022",
            severity=Severity.ERROR,
            message="Parameter 'filter' has no schema or no type defined.",
            path="/items",
            method="get",
        )
        fixer = FixAI022()
        assert fixer.fix(spec, finding) is True
        param = spec["paths"]["/items"]["get"]["parameters"][0]
        assert param["schema"] == {"type": "string"}


class TestLevelFilter:
    def test_level_1_skips_level_2(self) -> None:
        fixers = create_default_fixers()
        engine = FixEngineClass(fixers, max_level=1)
        # AI034 is level 2 — should not be in engine
        assert "AI034" not in engine._fixers  # noqa: SLF001


class TestDryRun:
    def test_dry_run_no_spec_change(self) -> None:
        spec = _minimal_spec()
        original = copy.deepcopy(spec)
        findings = [
            Finding(
                rule_id="AI042",
                severity=Severity.WARNING,
                message="No 4xx client error response defined.",
                path="/items",
                method="get",
            )
        ]
        engine = FixEngine(create_default_fixers())
        result = engine.fix(spec, findings, dry_run=True)
        assert len(result.applied) == 1
        # Original spec should NOT be modified
        assert spec == original


class TestFixEngineIntegration:
    def test_lint_fix_relint(self) -> None:
        """Full pipeline: lint -> fix -> re-lint shows improvement."""
        from ai_api_lint.loader import resolve_refs
        from ai_api_lint.rules import create_default_engine

        spec: dict = {
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0"},
            "paths": {
                "/items": {
                    "post": {
                        "operationId": "createItem",
                        "responses": {"200": {"description": "OK"}},
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {"type": "object"},
                                }
                            }
                        },
                    }
                }
            },
        }
        resolve_refs(spec)
        lint_engine = create_default_engine()

        # Initial lint
        report1 = lint_engine.lint(spec)
        score1 = report1.overall_score

        # Fix
        fix_engine = FixEngine(create_default_fixers())
        fix_engine.fix(spec, report1.findings)

        # Re-lint
        report2 = lint_engine.lint(spec)
        score2 = report2.overall_score

        assert score2 >= score1
        assert len(report2.findings) < len(report1.findings)
