from __future__ import annotations

from ai_api_lint.loader import resolve_refs


class TestResolveRefs:
    def test_resolves_nested_internal_schema_ref(self) -> None:
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0"},
            "components": {
                "schemas": {
                    "User": {
                        "type": "object",
                        "properties": {"id": {"type": "string"}},
                    }
                }
            },
            "paths": {
                "/users": {
                    "get": {
                        "responses": {
                            "200": {
                                "description": "OK",
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "#/components/schemas/User"}
                                    }
                                },
                            }
                        }
                    }
                }
            },
        }

        resolve_refs(spec)

        schema = spec["paths"]["/users"]["get"]["responses"]["200"]["content"]["application/json"][
            "schema"
        ]
        assert schema["type"] == "object"
        assert schema["properties"]["id"]["type"] == "string"
