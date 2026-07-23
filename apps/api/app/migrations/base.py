"""Base class for formal migrations.

Each migration is a class with:
- version: unique identifier (e.g. "001")
- name: short slug (e.g. "staff_to_guide")
- description: human-readable summary
- apply(): the migration logic (idempotent)
- rollback(): optional reversal logic
"""

from __future__ import annotations

import hashlib
import inspect
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class Migration:
    """Base migration. Subclass and implement :meth:`apply`."""

    version: str = field(compare=True)
    name: str = field(compare=True)
    description: str = field(default="")

    def __post_init__(self) -> None:
        if not self.version:
            raise ValueError("Migration version is required")
        if not self.name:
            raise ValueError("Migration name is required")

    @property
    def qualified_name(self) -> str:
        """Full identifier e.g. '001_staff_to_guide'."""
        return f"{self.version}_{self.name}"

    @property
    def checksum(self) -> str:
        """Stable content hash of the apply() source code."""
        src = inspect.getsource(self.apply)
        return hashlib.sha256(src.encode()).hexdigest()[:16]

    async def apply(self) -> None:
        """Execute migration. Must be idempotent."""
        raise NotImplementedError(f"Migration {self.qualified_name} must implement apply()")

    async def rollback(self) -> None:
        """Reverse migration (optional). Default: no-op."""
        logger.warning("Migration %s has no rollback defined", self.qualified_name)
