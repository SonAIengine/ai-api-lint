from __future__ import annotations

import re

from ai_api_lint.models import Finding, OperationContext, Severity
from ai_api_lint.rules.base import Rule, RuleCategory

_HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options", "trace"}

_PATH_VERBS = {
    "get",
    "create",
    "update",
    "delete",
    "fetch",
    "remove",
    "add",
    "set",
    "find",
    "search",
    "make",
    "do",
    "run",
    "execute",
    "process",
    "handle",
    "list",
    "post",
    "put",
}

_FALSE_POSITIVES = {
    "settings",
    "notifications",
    "results",
    "services",
    "resources",
    "assets",
    "events",
    "updates",
    "listings",
    "posts",
    "sets",
    "processes",
    "handles",
    "runs",
    "lists",
}

_CAMEL_RE = re.compile(r"[a-z]+[A-Z]")
_SNAKE_RE = re.compile(r"_")
_KEBAB_RE = re.compile(r"-")


def _non_param_segments(path: str) -> list[str]:
    """Return path segments that are not empty and not path parameters."""
    return [seg for seg in path.split("/") if seg and not seg.startswith("{")]


class AI050_PathContainsVerb(Rule):
    rule_id = "AI050"
    category = RuleCategory.PATH_DESIGN
    severity = Severity.WARNING
    short_description = "Path segments should not contain verbs"
    weight = 1.0

    def check(self, ctx: OperationContext) -> list[Finding]:
        findings: list[Finding] = []
        segments = _non_param_segments(ctx.path)
        for seg in segments:
            seg_lower = seg.lower()
            if seg_lower in _PATH_VERBS and seg_lower not in _FALSE_POSITIVES:
                findings.append(
                    self._finding(
                        ctx,
                        f"Path segment '{seg}' is a verb — prefer nouns in paths.",
                        suggestion="Use nouns for path segments; express actions via HTTP methods.",
                    )
                )
        return findings


class AI051_PathTooDeep(Rule):
    rule_id = "AI051"
    category = RuleCategory.PATH_DESIGN
    severity = Severity.WARNING
    short_description = "Path should not be too deeply nested (> 4 segments)"
    weight = 1.0

    def check(self, ctx: OperationContext) -> list[Finding]:
        segments = _non_param_segments(ctx.path)
        if len(segments) > 4:
            return [
                self._finding(
                    ctx,
                    f"Path has {len(segments)} non-parameter segments (> 4).",
                    suggestion="Consider flattening the path hierarchy.",
                )
            ]
        return []


class AI052_InconsistentNaming(Rule):
    rule_id = "AI052"
    category = RuleCategory.PATH_DESIGN
    severity = Severity.INFO
    short_description = "Path segments should use a consistent naming style"
    weight = 1.0

    def check(self, ctx: OperationContext) -> list[Finding]:
        return []

    def check_global(self, spec: dict) -> list[Finding]:
        all_segments: set[str] = set()
        paths = spec.get("paths", {})
        for path in paths:
            for seg in _non_param_segments(path):
                all_segments.add(seg)

        if not all_segments:
            return []

        styles: set[str] = set()
        for seg in all_segments:
            if _CAMEL_RE.search(seg):
                styles.add("camelCase")
            if _SNAKE_RE.search(seg):
                styles.add("snake_case")
            if _KEBAB_RE.search(seg):
                styles.add("kebab-case")

        if len(styles) > 1:
            return [
                Finding(
                    rule_id=self.rule_id,
                    severity=self.severity,
                    message=(
                        f"Inconsistent path naming styles detected: {', '.join(sorted(styles))}."
                    ),
                    path="/",
                    method="*",
                    suggestion="Pick one naming convention for all path segments.",
                )
            ]
        return []


class AI053_MissingTags(Rule):
    rule_id = "AI053"
    category = RuleCategory.PATH_DESIGN
    severity = Severity.WARNING
    short_description = "Operation should have at least one tag"
    weight = 1.0

    def check(self, ctx: OperationContext) -> list[Finding]:
        tags = ctx.operation.get("tags")
        if not tags:
            return [
                self._finding(
                    ctx,
                    f"{ctx.method.upper()} {ctx.path} has no tags.",
                    suggestion="Add 'tags' to group related operations.",
                )
            ]
        return []
