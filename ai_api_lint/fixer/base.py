"""Base class for auto-fixers."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ai_api_lint.models import Finding


class Fixer(ABC):
    """Abstract base for a rule-specific auto-fixer.

    Attributes
    ----------
    rule_id:
        The lint rule this fixer addresses (e.g. ``"AI042"``).
    level:
        1 = safe (only adds missing data), 2 = inferred (generates content from patterns).
    """

    rule_id: str
    level: int

    @abstractmethod
    def fix(self, spec: dict, finding: Finding) -> bool:
        """Mutate *spec* in-place to resolve *finding*.

        Returns True if a modification was made.
        """

    @abstractmethod
    def description(self) -> str:
        """Human-readable summary of what this fixer does."""
