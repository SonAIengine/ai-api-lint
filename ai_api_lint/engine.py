from __future__ import annotations

from collections.abc import Callable

from ai_api_lint.models import Finding, LintReport, OperationContext
from ai_api_lint.rules.base import Rule
from ai_api_lint.scorer import calculate_score

_HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options", "trace"}


class RuleEngine:
    def __init__(self) -> None:
        self._rules: list[Rule] = []
        self._global_checks: list[Callable[[dict], list[Finding]]] = []

    def register(self, rule: Rule) -> None:
        self._rules.append(rule)

    def register_global(self, check: Callable[[dict], list[Finding]]) -> None:
        self._global_checks.append(check)

    def lint(self, spec: dict, spec_path: str = "<stdin>") -> LintReport:
        findings: list[Finding] = []
        operation_count = 0

        for check in self._global_checks:
            findings.extend(check(spec))

        paths = spec.get("paths", {})
        for path, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue
            path_params = path_item.get("parameters", [])

            for method in _HTTP_METHODS:
                if method not in path_item:
                    continue
                operation = path_item[method]
                if not isinstance(operation, dict):
                    continue
                operation_count += 1

                op_params = operation.get("parameters", [])
                merged_params = path_params + op_params

                ctx = OperationContext(
                    path=path,
                    method=method,
                    operation=operation,
                    operation_id=operation.get("operationId"),
                    spec=spec,
                    parameters=merged_params,
                )

                for rule in self._rules:
                    if rule.applies_to(ctx):
                        findings.extend(rule.check(ctx))

        score, grade = calculate_score(findings, operation_count)
        return LintReport(
            spec_path=spec_path,
            total_operations=operation_count,
            findings=findings,
            overall_score=score,
            grade=grade,
        )
