"""DTOs for export workflows."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ArchiveFormatPayload:
    """Archive format availability prepared for delivery layers."""

    value: str
    name: str
    extension: str
    available: bool
    reason: str

    @property
    def display_name(self) -> str:
        status = "✓" if self.available else "✗"
        return f"{status} {self.name} ({self.extension})"
