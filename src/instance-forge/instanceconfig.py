#!/usr/bin/env python3

from dataclasses import dataclass, field
from typing import Optional, Tuple

from schedulingfield import InstanceEnvironment


@dataclass
class InstanceConfig:
    instance_environment: InstanceEnvironment

    job_seed: int = field(init=False, default=0)
    machine_seed: int = field(init=False, default=0)

    num_jobs: int = 1
    num_operations: int = 1
    num_centers: int = 1
    num_machines: int = 1

    release_factor: float = 0.5
    process_time: Tuple[int, int] = (2, 20)  # min, max
    machine_speed: Tuple[float, float] = (0.9, 1.1)  # min, max
    eligible_machines: Tuple[int, Optional[int]] = (1, None)
    due_date_factors: Tuple[float, float, float] = (1.5, 0.2, 2.0)
    due_date_penalty: Tuple[float, float] = (1, 5)  # min, max
    deadline_factor: float = 0.11
    predecessors: Tuple[int, int] = (0, 2) # min, max

    flowshop: bool = field(init=False, default=False)
    jobshop: bool = field(init=False, default=False)
    openshop: bool = field(init=False, default=False)
    p_different: bool = field(init=False, default=False)
    p_unrelated: bool = field(init=False, default=False)
    eligible: bool = field(init=False, default=False)
    same_mj: bool = field(init=False, default=False)
    release: bool = field(init=False, default=False)
    due: bool = field(init=False, default=False)
    deadline: bool = field(init=False, default=False)
    precedence: bool = field(init=False, default=False)
    setup_necessary: bool = field(init=False, default=False)
    breakdowns_possible: bool = field(init=False, default=False)

    def __post_init__(self):
        """initialize attributes and validates input values"""
        self.job_seed = self.instance_environment.job_seed
        self.machine_seed = self.instance_environment.machine_seed

        self.num_jobs = self.instance_environment.num_jobs
        self.num_centers = self.instance_environment.num_centers
        self.num_machines = self.instance_environment.num_machines
        self.num_operations = self.instance_environment.num_operations

        # Assigning boolean properties from instance environment
        self.flowshop = self.instance_environment.is_flowshop
        self.jobshop = self.instance_environment.is_jobshop
        self.openshop = self.instance_environment.is_openshop
        self.p_different = self.instance_environment.is_different
        self.p_unrelated = self.instance_environment.is_unrelated
        self.eligible = self.instance_environment.is_eligible
        self.same_mj = self.instance_environment.is_same_eligible_machines
        self.release = self.instance_environment.is_release
        self.due = self.instance_environment.is_due
        self.deadline = self.instance_environment.is_deadline
        self.precedence = self.instance_environment.is_precedence
        self.setup_necessary = self.instance_environment.is_setuptime_seq
        self.breakdowns_possible = self.instance_environment.is_breakdown

        self._validate_parameters()

    def _validate_parameters(self) -> None:
        """ensures all min/max constraints are valid and within allowed bounds"""
        min_pt, max_pt = self.process_time
        min_ms, max_ms = self.machine_speed
        min_em, max_em = self.eligible_machines
        min_ddp, max_ddp = self.due_date_penalty
        min_pre, max_pre = self.predecessors

        assert min_pt > 0 and max_pt > 0 and min_pt <= max_pt, "Invalid process time range"
        assert min_ms > 0 and max_ms <= 2 and min_ms <= max_ms, "Invalid machine speed range"
        assert min_em > 0 and (max_em is None or min_em <=
                               max_em), "Invalid eligible machines range"
        assert min_ddp > 0 and max_ddp > 0 and min_ddp <= max_ddp, "Invalid due date penalty range"
        assert min_pre >= 0 and min_pre <= max_pre, "Invalid predecessor range"
