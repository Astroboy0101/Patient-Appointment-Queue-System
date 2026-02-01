"""
Greedy Scheduling for doctor queue.

The scheduler always serves:

1. **Highest priority first**:
   Critical → Emergency → Accident → Normal
2. **Earliest appointment time** within the same priority:
   earlier (`appointment_date` + `appointment_time`) is served first.

Implementation notes (for DSA presentation):
-------------------------------------------
- `PatientLinkedList` is used to store **patient records** as a linked list.
  We insert each appointment node, then **traverse** the list.
- A `PriorityQueue` is then used to build the final serving order.
  Each priority level keeps patients in increasing appointment time.
"""

from typing import List
from datetime import datetime

from .queue import PriorityQueue, QueueItem, PRIORITY_ORDER, priority_rank
from .linked_list import PatientLinkedList


def _parse_created_at(value) -> datetime:
    """Parse created_at from DB (string/None) into a datetime."""
    if isinstance(value, datetime):
        return value
    if isinstance(value, str) and value:
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return datetime.min
    return datetime.min


def _parse_appointment_datetime(date_str: str, time_str: str, fallback: datetime) -> datetime:
    """
    Combine separate date + time fields into a single datetime object.
    Used for greedy comparison (earliest appointment time wins inside a priority).
    """
    date_str = (date_str or "").strip()
    time_str = (time_str or "").strip()
    if not date_str or not time_str:
        return fallback
    try:
        # Example format: 2025-02-02 and 09:30
        return datetime.fromisoformat(f"{date_str}T{time_str}")
    except ValueError:
        return fallback


def build_queue_item(
    appointment_id: int,
    name: str,
    priority: str,
    appointment_date: str,
    appointment_time: str,
    created_at: datetime,
) -> QueueItem:
    """Create a `QueueItem` from raw appointment fields."""
    return QueueItem(
        appointment_id=appointment_id,
        name=name,
        priority=(priority or "normal").lower().strip(),
        appointment_date=appointment_date or "",
        appointment_time=appointment_time or "",
        created_at=created_at,
    )


def get_optimized_queue_list(appointments: List[dict]) -> List[dict]:
    """
    Build the doctor's serving queue using a **greedy algorithm**:

    - Step 1: Insert all appointments into a `PatientLinkedList` (linked list of records).
    - Step 2: Traverse the list and compute a sort key for each patient:
              (priority_rank, appointment_date+time, created_at).
    - Step 3: Feed patients into a `PriorityQueue` *in increasing appointment time* so that
              each internal queue is FIFO by earliest appointment.

    Result: patients are always served by priority first, then by earliest appointment time.
    """
    # 1) Build linked list of patient records (insert new patient nodes).
    patient_list = PatientLinkedList()
    for a in appointments:
        patient_list.insert_from_appointment_dict(a)

    # 2) Traverse list to a Python list for greedy sorting.
    nodes = patient_list.to_list()

    enriched_items = []
    for node in nodes:
        prio = (node.priority or "normal").lower().strip()
        if prio not in PRIORITY_ORDER:
            prio = "normal"
        created = _parse_created_at(node.created_at)
        appt_dt = _parse_appointment_datetime(node.appointment_date, node.appointment_time, created)

        enriched_items.append(
            (
                priority_rank(prio),  # used only for readability of algorithm
                appt_dt,
                created,
                node,
            )
        )

    # Greedy sort: lowest (best) priority_rank, then earliest appointment time.
    enriched_items.sort(key=lambda x: (x[0], x[1], x[2]))

    # 3) Load into PriorityQueue in sorted order so each internal queue is FIFO by appointment.
    pq = PriorityQueue()
    for _, _, _, node in enriched_items:
        item = build_queue_item(
            appointment_id=node.appointment_id,
            name=node.name,
            priority=node.priority,
            appointment_date=node.appointment_date,
            appointment_time=node.appointment_time,
            created_at=_parse_created_at(node.created_at),
        )
        pq.enqueue(item)

    # Convert QueueItems back to dicts for the Flask templates.
    return [x.to_dict() for x in pq.to_list()]
