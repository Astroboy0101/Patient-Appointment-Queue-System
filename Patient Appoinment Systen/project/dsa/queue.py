"""
Queue and Priority Queue implementations for patient flow.
DSA: FIFO Queue; 4-level Priority Queue (Critical > Emergency > Accident > Normal).
"""

from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime

# Priority order: critical=0 (highest), emergency=1, accident=2, normal=3 (lowest)
PRIORITY_ORDER = ("critical", "emergency", "accident", "normal")


def priority_rank(p: str) -> int:
    """Lower rank = higher priority."""
    p = (p or "normal").lower().strip()
    for i, x in enumerate(PRIORITY_ORDER):
        if x == p:
            return i
    return 3  # normal


@dataclass
class QueueItem:
    """Item in the queue: holds appointment/patient data."""
    appointment_id: int
    name: str
    priority: str  # normal | accident | emergency | critical
    appointment_date: str
    appointment_time: str
    created_at: datetime

    def to_dict(self) -> dict:
        return {
            "appointment_id": self.appointment_id,
            "name": self.name,
            "priority": self.priority,
            "appointment_date": self.appointment_date,
            "appointment_time": self.appointment_time,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Queue:
    """FIFO Queue implemented using a list."""

    def __init__(self):
        self._items: List[QueueItem] = []

    def is_empty(self) -> bool:
        return len(self._items) == 0

    def enqueue(self, item: QueueItem) -> None:
        self._items.append(item)

    def dequeue(self) -> Optional[QueueItem]:
        if self.is_empty():
            return None
        return self._items.pop(0)

    def peek(self) -> Optional[QueueItem]:
        if self.is_empty():
            return None
        return self._items[0]

    def __len__(self) -> int:
        return len(self._items)

    def to_list(self) -> List[QueueItem]:
        return list(self._items)


class PriorityQueue:
    """
    4-level Priority Queue: Critical > Emergency > Accident > Normal.
    Within same priority, FIFO by arrival (created_at).
    """

    def __init__(self):
        self._queues: List[Queue] = [Queue() for _ in PRIORITY_ORDER]

    def _queue_for(self, priority: str) -> Queue:
        return self._queues[priority_rank(priority)]

    def is_empty(self) -> bool:
        return all(q.is_empty() for q in self._queues)

    def enqueue(self, item: QueueItem) -> None:
        q = self._queue_for(item.priority)
        q.enqueue(item)

    def dequeue(self) -> Optional[QueueItem]:
        for q in self._queues:
            if not q.is_empty():
                return q.dequeue()
        return None

    def peek(self) -> Optional[QueueItem]:
        for q in self._queues:
            if not q.is_empty():
                return q.peek()
        return None

    def __len__(self) -> int:
        return sum(len(q) for q in self._queues)

    def to_list(self) -> List[QueueItem]:
        """All items in priority order (critical first, then emergency, accident, normal)."""
        out: List[QueueItem] = []
        for q in self._queues:
            out.extend(q.to_list())
        return out
