#!/usr/bin/env python3

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

from job import Job
from operation import Operation

if TYPE_CHECKING:
    from center import Center
else:
    Center = Any

class Machine:
    def __init__(self, id: int, center: Center, processing_speed: float = 1.0, setup_times: Optional[Dict[Tuple[Job, Job], float]] = None, breakdowns: Optional[List[Tuple[float, float]]] = None) -> None:
        """
        Initialize a Machine representing a resource for processing operations in a scheduling problem.
        """
        self.id: int = id # change to tuple(i, k) ?
        self.name: str = f"{center.name}M{id}"
        self.center: Center = center
        self.processing_speed: float = processing_speed
        self.schedule: List[Operation] = []
        # (Job1, Job2) -> setup_time, setuptimes(Job, None) for non-sequence
        self.setup_times: Optional[Dict[Tuple[Job, Job], float]] = setup_times
        # (start, end)
        self.breakdowns: Optional[List[Tuple[float, float]]] = breakdowns

    def add_operation(self, operation: Operation) -> None:
        """Add an operation to this machine's schedule."""
        if operation.machine is not None and operation.machine.id != self.id:
            raise ValueError(
                f"Operation machine_id {operation.machine.id} does not match Machine {self.id}")
        self.schedule.append(operation)

    def total_processing_time(self) -> float:
        """Calculate total processing time of scheduled operations."""
        res: float = sum(
            op.processing_time for op in self.schedule if op.processing_time is not None)
        return res

    def __str__(self) -> str:
        return self.name
