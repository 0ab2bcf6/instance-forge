#!/usr/bin/env python3

from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from job import Job
    from machine import Machine
else:
    Job = Any
    Machine = Any


class Operation:
    def __init__(self, job: Optional[Job], machine: Optional[Machine] = None, processing_time: Optional[float] = None, eligible_machines: Optional[List[Machine]] = None, processing_times: Optional[Dict[Machine, float]] = None) -> None:
        """
        Initialize an Operation representing a single processing step in a scheduling problem.
        """
        self.name: Optional[str] = ""
        self.job: Optional[Job] = job
        self.machine: Optional[Machine] = machine
        self.processing_time: Optional[float] = processing_time
        self.eligible_machines: Optional[List[Machine]] = eligible_machines
        self.processing_times: Optional[Dict[Machine,
                                             float]] = processing_times

        self.preemption: bool = False
        self._is_initialized: bool = False
    
    def initialize_operation(self, job: Job, machine: Optional[Machine] = None) -> None:
        if not self._is_initialized:
            self.job = job
            self.machine = machine
            self.name = f"O(J{job.id}M{machine.id})" if machine else f"O(J{job.id})"
            self._is_initialized = True
