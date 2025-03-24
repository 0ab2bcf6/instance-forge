#!/usr/bin/env python3

from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from job import Job
    from machine import Machine
else:
    Job = Any
    Machine = Any

class OperationInitializer:
    """dummy class to hold inital operation parameters"""

    def __init__(self, id: int) -> None:
        self.id = id
        self.eligible_machines: List[Machine] = []
        self.processing_times: Dict[Machine, float] = {}

class Operation:
    def __init__(self, initializer: OperationInitializer) -> None:
        """
        Initialize an Operation representing a single processing step in a scheduling problem.
        """
        self.id = initializer.id
        self.name: str = ""
        self.eligible_machines: List[Machine] = initializer.eligible_machines
        self.processing_times: Dict[Machine, float] = initializer.processing_times
    
    def initialize_operation(self, job: Job, machine: Optional[Machine] = None) -> None:
        if not self._is_initialized:
            self.job = job
            self.machine = machine
            self.name = f"O(J{job.id}M{machine.id})" if machine else f"O(J{job.id})"
            self._is_initialized = True
