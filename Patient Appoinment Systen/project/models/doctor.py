"""
Doctor model - represents a doctor in the system.
Used for display and assignment; .
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Doctor:
    """Doctor record."""
    id: int
    name: str

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name}
