from __future__ import annotations

import json
from pathlib import Path


def load_spec(path: str) -> dict:
    """Load an OpenAPI spec from a JSON or YAML file."""
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    if p.suffix in (".yaml", ".yml"):
        try:
            import yaml  # noqa: F811
        except ImportError:
            msg = "PyYAML required for YAML files: pip install ai-api-lint[yaml]"
            raise ImportError(msg)  # noqa: B904
        return yaml.safe_load(text)
    return json.loads(text)


def _resolve_pointer(spec: dict, pointer: str) -> dict | list | str | None:
    """Follow a JSON pointer like '#/components/schemas/User'."""
    if not pointer.startswith("#/"):
        return None
    parts = pointer[2:].split("/")
    current: dict | list | str | None = spec
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
        if current is None:
            return None
    return current


def resolve_refs(spec: dict, _visiting: set | None = None) -> dict:
    """Resolve $ref references in-place (internal JSON pointer only)."""
    if _visiting is None:
        _visiting = set()

    if isinstance(spec, dict):
        if "$ref" in spec and isinstance(spec["$ref"], str):
            ref = spec["$ref"]
            if ref in _visiting:
                # Circular reference — skip
                return spec
            _visiting.add(ref)
            resolved = _resolve_pointer(spec, ref)
            if isinstance(resolved, dict):
                # Replace the $ref dict contents with resolved value
                spec.clear()
                spec.update(resolved)
                resolve_refs(spec, _visiting)
            _visiting.discard(ref)
        else:
            for value in spec.values():
                if isinstance(value, dict):
                    resolve_refs(value, _visiting)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            resolve_refs(item, _visiting)
    elif isinstance(spec, list):
        for item in spec:
            if isinstance(item, dict):
                resolve_refs(item, _visiting)

    return spec
