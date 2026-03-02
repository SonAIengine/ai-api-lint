"""Individual tests for all 14 fixers."""

from __future__ import annotations

from ai_api_lint.fixer.fixers import (
    FixAI001,
    FixAI010,
    FixAI011,
    FixAI014,
    FixAI022,
    FixAI031,
    FixAI032,
    FixAI033,
    FixAI034,
    FixAI040,
    FixAI041,
    FixAI042,
    FixAI043,
    FixAI053,
)
from ai_api_lint.models import Finding, Severity


def _spec_with_op(method: str = "get", path: str = "/items", **op_fields: dict) -> dict:
    """Build a spec with one operation."""
    op: dict = {"responses": {"200": {"description": "OK"}}}
    op.update(op_fields)
    return {
        "openapi": "3.0.0",
        "info": {"title": "T", "version": "1.0"},
        "paths": {path: {method: op}},
    }


def _finding(
    rule_id: str,
    path: str = "/items",
    method: str = "get",
    message: str = "",
    severity: Severity = Severity.WARNING,
) -> Finding:
    return Finding(rule_id=rule_id, severity=severity, message=message, path=path, method=method)


class TestFixAI042:
    def test_adds_400(self) -> None:
        spec = _spec_with_op()
        f = _finding("AI042", message="No 4xx client error response defined.")
        assert FixAI042().fix(spec, f) is True
        assert "400" in spec["paths"]["/items"]["get"]["responses"]


class TestFixAI034:
    def test_adds_rb_description(self) -> None:
        spec = _spec_with_op(
            method="post",
            operationId="createItem",
            summary="Create item",
            requestBody={"content": {"application/json": {"schema": {"type": "object"}}}},
        )
        f = _finding("AI034", method="post", message="Request body has no 'description'.")
        assert FixAI034().fix(spec, f) is True
        assert spec["paths"]["/items"]["post"]["requestBody"]["description"]


class TestFixAI031:
    def test_adds_properties(self) -> None:
        spec = _spec_with_op(
            method="post",
            requestBody={
                "content": {"application/json": {"schema": {"type": "object"}}},
            },
        )
        f = _finding("AI031", method="post", message="no properties")
        assert FixAI031().fix(spec, f) is True
        schema = spec["paths"]["/items"]["post"]["requestBody"]["content"]["application/json"][
            "schema"
        ]
        assert "properties" in schema


class TestFixAI014:
    def test_adds_param_description(self) -> None:
        spec = _spec_with_op(
            parameters=[{"name": "limit", "in": "query", "schema": {"type": "integer"}}]
        )
        f = _finding("AI014", message="Parameter 'limit' has no description.")
        assert FixAI014().fix(spec, f) is True
        assert spec["paths"]["/items"]["get"]["parameters"][0]["description"]


class TestFixAI022:
    def test_adds_schema_type(self) -> None:
        spec = _spec_with_op(parameters=[{"name": "q", "in": "query"}])
        f = _finding(
            "AI022",
            message="Parameter 'q' has no schema or no type defined.",
            severity=Severity.ERROR,
        )
        assert FixAI022().fix(spec, f) is True
        assert spec["paths"]["/items"]["get"]["parameters"][0]["schema"] == {"type": "string"}


class TestFixAI010:
    def test_adds_summary(self) -> None:
        spec = _spec_with_op(tags=["items"])
        # No summary or description
        op = spec["paths"]["/items"]["get"]
        op.pop("summary", None)
        op.pop("description", None)
        f = _finding("AI010", message="has no description or summary.", severity=Severity.ERROR)
        assert FixAI010().fix(spec, f) is True
        assert "GET" in spec["paths"]["/items"]["get"]["summary"]


class TestFixAI041:
    def test_adds_schema_to_success(self) -> None:
        spec = _spec_with_op()
        # 200 response with no content
        spec["paths"]["/items"]["get"]["responses"]["200"] = {"description": "OK"}
        f = _finding("AI041", message="Success response '200' has no content/schema.")
        assert FixAI041().fix(spec, f) is True
        assert "content" in spec["paths"]["/items"]["get"]["responses"]["200"]


class TestFixAI032:
    def test_adds_required_array(self) -> None:
        spec = _spec_with_op(
            method="post",
            requestBody={
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {"name": {"type": "string"}},
                        }
                    }
                },
            },
        )
        f = _finding("AI032", method="post", message="no 'required' list")
        assert FixAI032().fix(spec, f) is True
        schema = spec["paths"]["/items"]["post"]["requestBody"]["content"]["application/json"][
            "schema"
        ]
        assert "required" in schema


class TestFixAI043:
    def test_adds_error_description(self) -> None:
        spec = _spec_with_op()
        spec["paths"]["/items"]["get"]["responses"]["500"] = {}
        f = _finding(
            "AI043", message="Error response '500' has no description.", severity=Severity.INFO
        )
        assert FixAI043().fix(spec, f) is True
        assert (
            spec["paths"]["/items"]["get"]["responses"]["500"]["description"]
            == "Internal Server Error"
        )


class TestFixAI053:
    def test_adds_tag(self) -> None:
        spec = _spec_with_op()
        f = _finding("AI053", message="has no tags.")
        assert FixAI053().fix(spec, f) is True
        assert spec["paths"]["/items"]["get"]["tags"] == ["items"]


class TestFixAI011:
    def test_augments_short_description(self) -> None:
        spec = _spec_with_op(summary="List items")
        f = _finding("AI011", message="Description/summary is only 10 characters")
        assert FixAI011().fix(spec, f) is True
        summary = spec["paths"]["/items"]["get"]["summary"]
        assert len(summary) > len("List items")
        assert "GET" in summary
        assert "/items" in summary


class TestFixAI001:
    def test_generates_operation_id(self) -> None:
        spec = _spec_with_op()
        op = spec["paths"]["/items"]["get"]
        op.pop("operationId", None)
        f = _finding("AI001", message="no operationId")
        assert FixAI001().fix(spec, f) is True
        assert spec["paths"]["/items"]["get"]["operationId"] == "get_items"


class TestFixAI033:
    def test_adds_json_content_type(self) -> None:
        spec = _spec_with_op(
            method="post",
            requestBody={
                "content": {
                    "application/xml": {"schema": {"type": "object"}},
                },
            },
        )
        f = _finding(
            "AI033",
            method="post",
            message="Request body does not include 'application/json'.",
            severity=Severity.INFO,
        )
        assert FixAI033().fix(spec, f) is True
        content = spec["paths"]["/items"]["post"]["requestBody"]["content"]
        assert "application/json" in content


class TestFixAI040:
    def test_adds_200_response(self) -> None:
        spec = _spec_with_op()
        spec["paths"]["/items"]["get"]["responses"] = {}
        f = _finding("AI040", message="No 2xx success response.", severity=Severity.ERROR)
        assert FixAI040().fix(spec, f) is True
        assert "200" in spec["paths"]["/items"]["get"]["responses"]

    def test_adds_201_for_post(self) -> None:
        spec = _spec_with_op(method="post")
        spec["paths"]["/items"]["post"]["responses"] = {}
        f = _finding(
            "AI040", method="post", message="No 2xx success response.", severity=Severity.ERROR
        )
        assert FixAI040().fix(spec, f) is True
        assert "201" in spec["paths"]["/items"]["post"]["responses"]
