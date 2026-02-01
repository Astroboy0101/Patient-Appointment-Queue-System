"""
Each node represents **one patient appointment**. The list supports:
- inserting a new patient at the end,
- traversing the list (visit every patient),
- removing a patient node once the appointment is completed.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class PatientNode:
    """
    A single node in the patient linked list.

    Storing the key appointment fields keeps the data structure focused and
    easy to reason about when teaching linked lists.
    """

    appointment_id: int
    name: str
    priority: str
    appointment_date: str
    appointment_time: str
    created_at: Any    # string or datetime from DB; scheduler normalizes this
    next: Optional["PatientNode"] = None


class PatientLinkedList:
    """
    Custom singly linked list for patient appointment records.

    - `insert_from_appointment_dict`  → INSERT
    - `to_list`                       → TRAVERSE
    - `remove_by_id`                  → REMOVE (after completion)

    The list is kept separate from any Flask/HTML logic so that the
    data‑structure implementation remains clean and self‑contained.
    """

    def __init__(self) -> None:
        self.head: Optional[PatientNode] = None

    # ------------------------------------------------------------------
    # INSERT
    # ------------------------------------------------------------------
    def insert_from_appointment_dict(self, a: Dict[str, Any]) -> None:
        """
        Insert a new patient node at the end of the list.

        `a` is a row/dict from the `appointments` table.
        """
        node = PatientNode(
            appointment_id=a["id"],
            name=a.get("name") or a.get("patient_name") or "",
            priority=(a.get("priority") or "normal").lower().strip(),
            appointment_date=a.get("appointment_date") or "",
            appointment_time=a.get("appointment_time") or "",
            created_at=a.get("created_at"),
        )

        if self.head is None:
            self.head = node
            return

        current = self.head
        while current.next is not None:
            current = current.next
        current.next = node

    # ------------------------------------------------------------------
    # TRAVERSE
    # ------------------------------------------------------------------
    def to_list(self) -> List[PatientNode]:
        """
        Traverse the linked list and return a Python list of nodes.

        This is convenient for algorithms (like the greedy scheduler) that
        want random access or sorting, while still demonstrating linked
        list traversal logic.
        """
        nodes: List[PatientNode] = []
        current = self.head
        while current is not None:
            nodes.append(current)
            current = current.next
        return nodes

    # ------------------------------------------------------------------
    # REMOVE
    # ------------------------------------------------------------------
    def remove_by_id(self, appointment_id: int) -> bool:
        """
        Remove the first node whose `appointment_id` matches.

        Returns True if a node was removed, False otherwise.
        """
        current = self.head
        prev: Optional[PatientNode] = None

        while current is not None:
            if current.appointment_id == appointment_id:
                # Removing the head node.
                if prev is None:
                    self.head = current.next
                else:
                    prev.next = current.next
                return True

            prev = current
            current = current.next

        return False

