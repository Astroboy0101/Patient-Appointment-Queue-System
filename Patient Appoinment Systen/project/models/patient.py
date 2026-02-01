"""
Patient model using Linked List for dynamic patient records storage.
Each node holds a patient record; the list supports add, traversal, and lookup.
DSA: Singly Linked List implementation.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


@dataclass
class PatientRecord:
    """Single patient record (data stored in a linked list node)."""
    id: int
    name: str
    priority: str  # "normal" | "emergency"
    created_at: datetime
    doctor_id: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "priority": self.priority,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "doctor_id": self.doctor_id,
        }


class PatientNode:
    """
    Node for the patient linked list.
    Each node contains a PatientRecord and a reference to the next node.
    """

    def __init__(self, record: PatientRecord):
        self.record: PatientRecord = record
        self.next: Optional["PatientNode"] = None


class PatientLinkedList:
    """
    Singly Linked List for storing patient records dynamically.
    Used for in-memory patient registry; supports add, traverse, find.
    """

    def __init__(self):
        self.head: Optional[PatientNode] = None
        self._size: int = 0

    def is_empty(self) -> bool:
        return self.head is None

    def __len__(self) -> int:
        return self._size

    def append(self, record: PatientRecord) -> None:
        """Add a new patient record at the end of the list."""
        new_node = PatientNode(record)
        if self.head is None:
            self.head = new_node
        else:
            current = self.head
            while current.next is not None:
                current = current.next
            current.next = new_node
        self._size += 1

    def find_by_id(self, patient_id: int) -> Optional[PatientRecord]:
        """Traverse the list and return the record with given id, or None."""
        current = self.head
        while current is not None:
            if current.record.id == patient_id:
                return current.record
            current = current.next
        return None

    def to_list(self) -> List[PatientRecord]:
        """Traverse the list and return all records as a list."""
        result: List[PatientRecord] = []
        current = self.head
        while current is not None:
            result.append(current.record)
            current = current.next
        return result

    def clear(self) -> None:
        """Remove all nodes from the list."""
        self.head = None
        self._size = 0
