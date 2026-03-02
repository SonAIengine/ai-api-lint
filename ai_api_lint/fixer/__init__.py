"""Auto-fix package for ai-api-lint."""

from __future__ import annotations

from .base import Fixer
from .engine import FixEngine


def create_default_fixers() -> list[Fixer]:
    """Return all built-in fixers."""
    from .fixers import (
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

    return [
        FixAI042(),
        FixAI034(),
        FixAI031(),
        FixAI014(),
        FixAI022(),
        FixAI010(),
        FixAI041(),
        FixAI032(),
        FixAI043(),
        FixAI053(),
        FixAI011(),
        FixAI001(),
        FixAI033(),
        FixAI040(),
    ]


__all__ = ["FixEngine", "Fixer", "create_default_fixers"]
