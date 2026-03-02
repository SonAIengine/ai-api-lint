"""Built-in fixer implementations for all supported rules."""

from __future__ import annotations

import re

from ai_api_lint.models import Finding

from .base import Fixer

_STATUS_DESCRIPTIONS: dict[str, str] = {
    "400": "Bad Request",
    "401": "Unauthorized",
    "403": "Forbidden",
    "404": "Not Found",
    "405": "Method Not Allowed",
    "409": "Conflict",
    "422": "Unprocessable Entity",
    "429": "Too Many Requests",
    "500": "Internal Server Error",
    "502": "Bad Gateway",
    "503": "Service Unavailable",
}


def _get_operation(spec: dict, path: str, method: str) -> dict | None:
    """Safely navigate to the operation dict."""
    return spec.get("paths", {}).get(path, {}).get(method)


def _path_slug(path: str) -> str:
    """Convert a path like /api/v1/users/{id}/orders to users_id_orders."""
    parts = path.strip("/").split("/")
    cleaned = []
    for p in parts:
        if p.startswith("{") and p.endswith("}"):
            cleaned.append(p[1:-1])
        elif p in ("api", "v1", "v2", "v3"):
            continue
        else:
            cleaned.append(p)
    return "_".join(cleaned)


# ---- AI042: No 4xx response ----


class FixAI042(Fixer):
    rule_id = "AI042"
    level = 1

    def fix(self, spec: dict, finding: Finding) -> bool:
        op = _get_operation(spec, finding.path, finding.method)
        if op is None:
            return False
        responses = op.setdefault("responses", {})
        if any(str(c).startswith("4") for c in responses):
            return False
        responses["400"] = {"description": "Bad Request"}
        return True

    def description(self) -> str:
        return "Add '400: Bad Request' response"


# ---- AI034: requestBody missing description ----


class FixAI034(Fixer):
    rule_id = "AI034"
    level = 2

    def fix(self, spec: dict, finding: Finding) -> bool:
        op = _get_operation(spec, finding.path, finding.method)
        if op is None:
            return False
        rb = op.get("requestBody")
        if not rb or rb.get("description", "").strip():
            return False
        op_id = op.get("operationId", "")
        summary = op.get("summary", "")
        if summary:
            rb["description"] = f"Request body for {summary}"
        elif op_id:
            rb["description"] = f"Request body for {op_id}"
        else:
            rb["description"] = f"Request body for {finding.method.upper()} {finding.path}"
        return True

    def description(self) -> str:
        return "Add auto-generated requestBody description"


# ---- AI031: requestBody schema has no properties ----


class FixAI031(Fixer):
    rule_id = "AI031"
    level = 1

    def fix(self, spec: dict, finding: Finding) -> bool:
        op = _get_operation(spec, finding.path, finding.method)
        if op is None:
            return False
        rb = op.get("requestBody", {})
        content = rb.get("content", {})
        json_media = content.get("application/json", {})
        schema = json_media.get("schema", {})
        if not schema or schema.get("properties"):
            return False
        schema["properties"] = {}
        return True

    def description(self) -> str:
        return "Add empty 'properties' to requestBody schema"


# ---- AI014: parameter missing description ----


class FixAI014(Fixer):
    rule_id = "AI014"
    level = 2

    def fix(self, spec: dict, finding: Finding) -> bool:
        op = _get_operation(spec, finding.path, finding.method)
        if op is None:
            return False
        # Extract param name from finding message: "Parameter 'xxx' has no description."
        match = re.search(r"Parameter '([^']+)'", finding.message)
        if not match:
            return False
        param_name = match.group(1)

        # Check path-level params too
        path_item = spec.get("paths", {}).get(finding.path, {})
        all_params = list(path_item.get("parameters", [])) + list(op.get("parameters", []))

        for param in all_params:
            if param.get("name") == param_name and not param.get("description", "").strip():
                schema = param.get("schema", {})
                ptype = schema.get("type", "value")
                location = param.get("in", "parameter")
                param["description"] = f"The {param_name} {location} ({ptype})"
                return True
        return False

    def description(self) -> str:
        return "Add auto-generated parameter description"


# ---- AI022: parameter missing schema/type ----


class FixAI022(Fixer):
    rule_id = "AI022"
    level = 1

    def fix(self, spec: dict, finding: Finding) -> bool:
        op = _get_operation(spec, finding.path, finding.method)
        if op is None:
            return False
        match = re.search(r"Parameter '([^']+)'", finding.message)
        if not match:
            return False
        param_name = match.group(1)

        path_item = spec.get("paths", {}).get(finding.path, {})
        all_params = list(path_item.get("parameters", [])) + list(op.get("parameters", []))

        for param in all_params:
            if param.get("name") == param_name:
                schema = param.get("schema")
                if not schema or not schema.get("type"):
                    param["schema"] = {"type": "string"}
                    return True
        return False

    def description(self) -> str:
        return "Add default schema {type: string} to parameter"


# ---- AI010: description/summary missing ----


class FixAI010(Fixer):
    rule_id = "AI010"
    level = 2

    def fix(self, spec: dict, finding: Finding) -> bool:
        op = _get_operation(spec, finding.path, finding.method)
        if op is None:
            return False
        if op.get("summary", "").strip() or op.get("description", "").strip():
            return False
        tags = op.get("tags", [])
        parts = [finding.method.upper(), finding.path]
        if tags:
            parts.append(f"({', '.join(tags)})")
        op["summary"] = " ".join(parts)
        return True

    def description(self) -> str:
        return "Add auto-generated summary from method/path/tags"


# ---- AI041: success response has no schema ----


class FixAI041(Fixer):
    rule_id = "AI041"
    level = 1

    def fix(self, spec: dict, finding: Finding) -> bool:
        op = _get_operation(spec, finding.path, finding.method)
        if op is None:
            return False
        responses = op.get("responses", {})
        for code, resp in responses.items():
            if not str(code).startswith("2") or not isinstance(resp, dict):
                continue
            content = resp.get("content")
            if content is None:
                resp["content"] = {"application/json": {"schema": {"type": "object"}}}
                return True
            json_media = content.get("application/json")
            if json_media is not None and not json_media.get("schema"):
                json_media["schema"] = {"type": "object"}
                return True
        return False

    def description(self) -> str:
        return "Add empty object schema to success response"


# ---- AI032: requestBody has properties but no required ----


class FixAI032(Fixer):
    rule_id = "AI032"
    level = 1

    def fix(self, spec: dict, finding: Finding) -> bool:
        op = _get_operation(spec, finding.path, finding.method)
        if op is None:
            return False
        rb = op.get("requestBody", {})
        content = rb.get("content", {})
        json_media = content.get("application/json", {})
        schema = json_media.get("schema", {})
        if schema.get("properties") and not schema.get("required"):
            schema["required"] = []
            return True
        return False

    def description(self) -> str:
        return "Add empty 'required' array to requestBody schema"


# ---- AI043: error response has no description ----


class FixAI043(Fixer):
    rule_id = "AI043"
    level = 1

    def fix(self, spec: dict, finding: Finding) -> bool:
        op = _get_operation(spec, finding.path, finding.method)
        if op is None:
            return False
        # Extract status code from message: "Error response 'xxx' has no description."
        match = re.search(r"response '(\d+)'", finding.message)
        if not match:
            return False
        code = match.group(1)
        responses = op.get("responses", {})
        resp = responses.get(code)
        if resp is not None and not resp.get("description", "").strip():
            resp["description"] = _STATUS_DESCRIPTIONS.get(code, f"Error {code}")
            return True
        return False

    def description(self) -> str:
        return "Add status-code-based description to error response"


# ---- AI053: missing tags ----


class FixAI053(Fixer):
    rule_id = "AI053"
    level = 1

    def fix(self, spec: dict, finding: Finding) -> bool:
        op = _get_operation(spec, finding.path, finding.method)
        if op is None:
            return False
        if op.get("tags"):
            return False
        segments = [s for s in finding.path.strip("/").split("/") if s and not s.startswith("{")]
        if segments:
            # Skip common prefixes like 'api', 'v1', 'v2', 'v3'
            tag = segments[0]
            for s in segments:
                if s.lower() not in ("api", "v1", "v2", "v3"):
                    tag = s
                    break
            op["tags"] = [tag]
            return True
        return False

    def description(self) -> str:
        return "Add tag from first path segment"


# ---- AI011: description too short (< 30 chars) ----


class FixAI011(Fixer):
    rule_id = "AI011"
    level = 2

    def fix(self, spec: dict, finding: Finding) -> bool:
        op = _get_operation(spec, finding.path, finding.method)
        if op is None:
            return False
        summary = op.get("summary", "").strip()
        desc = op.get("description", "").strip()
        existing = summary or desc
        if not existing or len(existing) >= 30:
            return False
        tags = op.get("tags", [])
        extra = f" — {finding.method.upper()} {finding.path}"
        if tags:
            extra += f" ({', '.join(tags)})"
        new_desc = existing + extra
        if summary:
            op["summary"] = new_desc
        else:
            op["description"] = new_desc
        return True

    def description(self) -> str:
        return "Augment short description with method/path info"


# ---- AI001: operationId missing ----


class FixAI001(Fixer):
    rule_id = "AI001"
    level = 2

    def fix(self, spec: dict, finding: Finding) -> bool:
        op = _get_operation(spec, finding.path, finding.method)
        if op is None:
            return False
        if op.get("operationId"):
            return False
        slug = _path_slug(finding.path)
        op["operationId"] = f"{finding.method}_{slug}"
        return True

    def description(self) -> str:
        return "Generate operationId from method and path"


# ---- AI033: requestBody not JSON ----


class FixAI033(Fixer):
    rule_id = "AI033"
    level = 1

    def fix(self, spec: dict, finding: Finding) -> bool:
        op = _get_operation(spec, finding.path, finding.method)
        if op is None:
            return False
        rb = op.get("requestBody")
        if not rb:
            return False
        content = rb.get("content", {})
        if "application/json" in content:
            return False
        # Copy schema from first available content type, or create empty
        existing_schema: dict = {"type": "object"}
        for media in content.values():
            if isinstance(media, dict) and media.get("schema"):
                existing_schema = media["schema"]
                break
        content["application/json"] = {"schema": existing_schema}
        rb["content"] = content
        return True

    def description(self) -> str:
        return "Add application/json content type to requestBody"


# ---- AI040: no 2xx success response ----


class FixAI040(Fixer):
    rule_id = "AI040"
    level = 1

    def fix(self, spec: dict, finding: Finding) -> bool:
        op = _get_operation(spec, finding.path, finding.method)
        if op is None:
            return False
        responses = op.setdefault("responses", {})
        if any(str(c).startswith("2") for c in responses):
            return False
        code = "201" if finding.method in ("post",) else "200"
        responses[code] = {"description": "OK" if code == "200" else "Created"}
        return True

    def description(self) -> str:
        return "Add success response (200 OK or 201 Created)"
