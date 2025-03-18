#!/usr/bin/env python3

from typing import List, Optional, Tuple

from operation import Operation


class Job:
    def __init__(self, id: int, operations: List[Operation], sequence: Optional[List[int]] = None, release_time: Optional[float] = None, due_date: Optional[Tuple[float, float]] = None, deadline: Optional[float] = None, predecessors: Optional[List['Job']] = None) -> None:
        """
        Initialize a Job representing a unit of work in a scheduling problem.
        """

        # check for valid combinations done in InstanceEnvironment
        self.id: int = id
        self.name: str = f"J{id}"
        self.operations: List[Operation] = operations
        self.sequence: Optional[List[int]] = sequence

        # Job-specific constraints
        self.release_time: Optional[float] = release_time if release_time is not None else None
        # (date, penalty)
        self.due_date: Optional[Tuple[float, float]
                                ] = due_date if due_date is not None else None
        self.deadline: Optional[float] = deadline if deadline is not None else None
        self.predecessors: List['Job'] = predecessors if predecessors is not None else []
        self.no_wait: bool = False
        self._validate_sequence()

    def total_processing_time(self) -> float:
        """Calculate total processing time of scheduled operations."""
        res: float = sum(
            op.processing_time for op in self.operations if op.processing_time is not None)
        return res

    def get_operation(self, index: int) -> Operation:
        """Get operation at the specified index (considering sequence if provided)."""
        if self.sequence is None:
            return self.operations[index]
        return self.operations[self.sequence[index]]

    def _validate_sequence(self) -> None:
        # Validate sequence if provided
        if self.sequence is not None and len(self.sequence) != len(self.operations):
            raise ValueError(
                f"Sequence length {len(self.sequence)} does not match operations length {len(self.operations)}")

    def __str__(self) -> str:
        seq_str = "None" if self.sequence is None else str(self.sequence)
        return f"Job {self.name} (ops={len(self.operations)}, seq={seq_str}, total_proc={self.total_processing_time()})"
