#!/usr/bin/env python3

import math
import random
from typing import Dict, List, Optional, Tuple

from center import Center
from job import Job
from machine import Machine
from operation import Operation
from schedulingfield import SchedulingField, InstanceEnvironment


class Instance:
    def __init__(self, instance_environment: InstanceEnvironment, seed: int) -> None:
        """
        Initialize a scheduling problem instance.

        Args:
            instance_environment: keeps information about the instance environment
            seed: the seed of the instance, used to create the instance parameters
        """
        if instance_environment is None:
            raise ValueError("instance_environment cannot be None")
        self._instance_environment: InstanceEnvironment = instance_environment
        self._seed: int = seed
        self.name: str = f"{str(instance_environment).replace("|", "-").replace(",", "-")}"
        self.jobs: List[Job] = []
        self.centers: List[Center] = []
        self._create_instance_parameters()

    def __str__(self) -> str:
        return f"{str(self.name)}_s{self._seed}"

    def _create_instance_parameters(self) -> None:
        """Generate parameters for the scheduling instance, including jobs, machines, and operations."""
        if len(self.jobs) != 0 and len(self.centers) != 0:
            # avoid regenerating if instance already exists
            return

        min_processtime: int = 3
        max_processtime: int = 23

        time_seed: int = self._instance_environment.time_seed + self._seed
        machine_seed: int = self._instance_environment.machine_seed + self._seed
        time_rand = random.Random(time_seed)
        machine_rand = random.Random(machine_seed)
        
        # centers
        first_center_passed: bool = False
        self.centers: List[Center] = []
        num_centers = self._instance_environment.num_centers

        is_flowshop: bool = self._instance_environment.alpha == SchedulingField.FLOWSHOP
        is_jobshop: bool = self._instance_environment.alpha == SchedulingField.JOBSHOP
        is_openshop: bool = self._instance_environment.alpha == SchedulingField.OPENSHOP
        is_p_different: bool = self._instance_environment.alpha == SchedulingField.PARALLEL_DIFFERENT
        is_p_unrelated: bool = self._instance_environment.alpha == SchedulingField.PARALLEL_UNRELATED
        is_eligible: bool = self._instance_environment.is_eligible

        setup_necessary: bool = self._instance_environment.is_setuptime_seq
        breakdowns_possible: bool = self._instance_environment.is_breakdown
        for i in range(num_centers):
            self.centers.append(Center(i, None))
            machines: List[Machine] = []
            num_machines = self._instance_environment.num_machines
            for j in range(num_machines):
                speed: float = 1.0
                if is_p_different:
                    speed = round(machine_rand.uniform(0.9, 1.1), 1)
                setup_times: Optional[Dict] = None
                if setup_necessary:
                    setup_times = {}
                breakdowns: Optional[List] = None
                if breakdowns_possible:
                    breakdowns = []
                machine = Machine(j, self.centers[i], speed, setup_times, breakdowns)
                machines.append(machine)
            self.centers[i].machines = machines

        # jobs and operations
        # TODO adjust estimators when stages/centers added
        self.jobs: List[Job] = []
        num_jobs = self._instance_environment.num_jobs
        num_operations = self._instance_environment.num_operations
        average_processingtime = ((max_processtime + min_processtime)/2)
        makespan_estimation: int = math.ceil(num_jobs * average_processingtime)

        if is_flowshop:
            sequence = list(range(num_operations))
        elif is_openshop:
            sequence = []
        # will need to be adjusted once more alpha fields are added
        elif not is_jobshop:
            sequence = None
            makespan_estimation = math.ceil(makespan_estimation / num_machines)

        for j in range(num_jobs):
            operations: List[Operation] = []

            # TODO for center in self.centers
            eligible_machines: List[Machine] = []
            if is_eligible:
                eligible_machines: List[Machine] = time_rand.sample(
                    self.machines, k=machine_rand.randint(1, len(self.machines)))
            else:
                eligible_machines = self.machines

            for _ in range(num_operations):
                processing_time: Optional[int] = None
                processing_times: Dict[Machine, float] = {}
                if is_p_unrelated:
                    processing_times = {m: round(time_rand.randint(
                        min_processtime, max_processtime)/m.processing_speed, 1) for m in eligible_machines}
                else:
                    # case of identital parallel machines
                    # check in prev center for sequence
                    processing_time = time_rand.randint(
                        min_processtime, max_processtime)
                    processing_times = {
                        m: round(processing_time/m.processing_speed, 1) for m in eligible_machines}

                operation = Operation(
                    job=None,
                    machine=None,
                    processing_time=processing_time,
                    eligible_machines=eligible_machines,
                    processing_times=processing_times
                )
                operations.append(operation)

            # will need to be adjusted once more alpha fields are added
            if is_jobshop:
                sequence = time_rand.sample(
                    range(num_operations), num_operations)

            # Create the job
            # TODO rethink these as soon as stages get added
            release_time = float(time_rand.randint(
                0, math.ceil(makespan_estimation*0.43))) if self._instance_environment.is_release else None
            duedate_estimation: float = (
                release_time or 0) + math.ceil(num_operations * average_processingtime * 1.49)
            due_date = (float(math.ceil(duedate_estimation + time_rand.randint(0, math.ceil(makespan_estimation*0.19)))), float(time_rand.randint(
                2, 7))) if self._instance_environment.is_due else None
            deadline_estimation = (
                release_time or 0) + math.ceil(num_operations * average_processingtime * 1.99)
            if due_date:
                deadline_estimation = max(deadline_estimation, due_date[0])
            deadline = math.ceil(deadline_estimation + time_rand.randint(0, math.ceil(
                makespan_estimation * 0.11))) if self._instance_environment.is_deadline else None

            predecessors: List[Job] = []
            # TODO think about better approach this only creates outtrees
            # also: satisfiability <-> deadlines
            if self._instance_environment.is_precedence:
                possible_pred: List[Job] = []
                for job in self.jobs:
                    pred_earliest_possible = (
                        job.release_time or 0) + job.total_processing_time()
                    if not release_time or release_time >= pred_earliest_possible:
                        possible_pred.append(job)
                min_num_pred: int = min(
                    len(possible_pred), time_rand.randint(0, 2))
                if min_num_pred > 0:
                    predecessors = time_rand.sample(
                        possible_pred, k=min_num_pred)

            job = Job(
                id=j,
                operations=operations,
                sequence=sequence,
                release_time=float(release_time) if release_time else None,
                due_date=due_date,
                deadline=float(deadline) if deadline else None,
                predecessors=predecessors
            )

            # set job reference in operations
            for idx, op in enumerate(operations):
                if not is_eligible:
                    machine: Optional[Machine] = self.machines[job.sequence[idx]
                                                               ] if job.sequence else None
                    # i couldnt figure out a better way to handle this lol
                    op.initialize_operation(job, machine)
            self.jobs.append(job)

            if breakdowns_possible:

            if setup_necessary:
                for machine in self.machines:
                    if machine.setup_times is not None:
                        for job_pair in [(job, other_job) for other_job in self.jobs if other_job != job]:
                            if machine_rand.random() < 0.19:  # 19% chance setup is important
                                machine.setup_times[job_pair] = time_rand.randint(
                                    2, 7)
            
            first_center_passed = True
