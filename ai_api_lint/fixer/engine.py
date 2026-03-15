"""Fix engine — applies fixers to a spec based on lint findings."""

from __future__ import annotations

import copy
import difflib
import json

from ai_api_lint.models import Finding, FixRecord, FixResult

from .base import Fixer


class FixEngine:
    """Orchestrates fixer application on an OpenAPI spec."""

    def __init__(self, fixers: list[Fixer], max_level: int = 2) -> None:
        self._fixers = {f.rule_id: f for f in fixers if f.level <= max_level}

    def fix(self, spec: dict, findings: list[Finding], *, dry_run: bool = False) -> FixResult:
        """Apply matching fixers to *spec* in-place.

        When *dry_run* is True the spec is not modified; only the result is computed.
        """
        target = spec if not dry_run else copy.deepcopy(spec)

        result = FixResult()
        for finding in findings:
            fixer = self._fixers.get(finding.rule_id)
            if fixer is None:
                continue
            record = FixRecord(
                rule_id=finding.rule_id,
                path=finding.path,
                method=finding.method,
                description=fixer.description(),
            )
            try:
                changed = fixer.fix(target, finding)
            except Exception as exc:  # noqa: BLE001
                record.reason = f"{type(exc).__name__}: {exc}"
                result.skipped.append(record)
                continue
            if changed:
                result.applied.append(record)
            else:
                record.reason = "No changes were needed for the current spec state."
                result.skipped.append(record)

        if dry_run:
            before = self._serialize_spec(spec)
            after = self._serialize_spec(target)
            if before != after:
                result.diff_preview = "\n".join(
                    difflib.unified_diff(
                        before.splitlines(),
                        after.splitlines(),
                        fromfile="before",
                        tofile="after",
                        lineterm="",
                    )
                )

        return result

    @staticmethod
    def _serialize_spec(spec: dict) -> str:
        return json.dumps(spec, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
