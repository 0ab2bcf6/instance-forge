#!/usr/bin/env python3

import math
from multiprocessing import Value
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

        # TODO create a dataclass for all instance generation parameters
        # most basic parameters
        min_processtime: int = 3
        max_processtime: int = 19
        job_seed: int = self._instance_environment.job_seed + self._seed
        machine_seed: int = self._instance_environment.machine_seed + self._seed
        job_rand = random.Random(job_seed)
        machine_rand = random.Random(machine_seed)

        # some parameter for further use few lines down
        is_flowshop: bool = self._instance_environment.is_flowshop
        is_jobshop: bool = self._instance_environment.is_jobshop
        is_openshop: bool = self._instance_environment.is_openshop
        is_p_different: bool = self._instance_environment.is_different
        is_p_unrelated: bool = self._instance_environment.is_unrelated
        is_eligible: bool = self._instance_environment.is_eligible
        is_same_mj: bool = self._instance_environment.is_same_eligible_machines
        setup_necessary: bool = self._instance_environment.is_setuptime_seq
        breakdowns_possible: bool = self._instance_environment.is_breakdown

        # Cases for Hybrids
        # to avoid recalculating job sequences, releasedates, duedates ..
        prev_center: Optional[Center] = None
        # probability_eligible: Dict[int, float] = {}
        # to avoid recalculating machine setup times, breakdowns,  ..
        prev_center_machines: Dict[Machine, List[int]] = {}

        # centers
        self.centers: List[Center] = []
        num_centers = self._instance_environment.num_centers

        for i in range(num_centers):
            self.centers.append(Center(i, None))
            machines: List[Machine] = []
            num_machines = self._instance_environment.num_machines
            for j in range(num_machines):
                speed: float = 1.0
                if is_p_different or is_p_unrelated:
                    speed = round(machine_rand.uniform(0.9, 1.1), 1)
                setup_times: Optional[Dict] = None
                if setup_necessary:
                    setup_times = {}
                breakdowns: Optional[List] = None
                if breakdowns_possible:
                    breakdowns = []
                machine = Machine(
                    j, self.centers[i], speed, setup_times, breakdowns)
                machines.append(machine)
            self.centers[i].machines = machines

        # jobs and operations
        self.jobs: List[Job] = []
        num_jobs: int = self._instance_environment.num_jobs
        num_operations: int = self._instance_environment.num_operations
        average_processingtime: float = ((max_processtime + min_processtime)/2)
        makespan_estimation = float(
            math.ceil(num_jobs * average_processingtime/num_centers))

        # job shop sequence is set later
        if is_flowshop:
            sequence = list(range(num_operations))
        elif is_openshop:
            sequence = []  # TODO not every job has to go through every machine
        elif not is_jobshop:
            sequence = None
            makespan_estimation = math.ceil(makespan_estimation / num_machines)

        for center in self.centers:
            if center.machines is None or (center.machines and len(center.machines) == 0):
                raise ValueError("Machines not assigned to center!")

            machines = center.machines
            for j in range(num_jobs):
                for op_idx in range(num_operations):
                    eligible_machines: List[Machine] = []
                    if is_eligible:
                        # case we have multi center shop problem
                        if (is_flowshop or is_jobshop or is_openshop) and prev_center is None:
                            # TODO make sure eligible machines align with required sequence
                            # make sure that when at least one machine per stage is eligible
                            if is_flowshop:
                                eligible_machines = machine_rand.sample(
                                    machines, k=machine_rand.randint(0, len(machines)))
                            elif is_jobshop:
                                eligible_machines = machine_rand.sample(
                                    machines, k=machine_rand.randint(0, len(machines)))
                            else:
                                eligible_machines = machine_rand.sample(
                                    machines, k=machine_rand.randint(0, len(machines)))
                            
                        elif (is_flowshop or is_jobshop or is_openshop) and prev_center is not None:
                            # case if we have the same eligibale machines across centers
                            if is_same_mj:
                                if self.jobs[j].operations[op_idx].eligible_machines:
                                    raise ValueError("Eligibale Machines not found in operations!")
                                eligible_machines = [
                                    machine for machine in center.machines
                                    if machine.id in (self.jobs[j].operations[op_idx].eligible_machines or [])
                                ]
                            else:  
                                # TODO make sure eligible machines align with required sequence
                                eligible_machines = machine_rand.sample(
                                    machines, k=machine_rand.randint(1, len(machines)))
                        else: # case for single center P, Q and R
                           eligible_machines = machine_rand.sample(
                               machines, k=machine_rand.randint(1, len(machines)))
                    else:
                        eligible_machines = machines

                    processing_time: Optional[int] = None
                    processing_times: Dict[Machine, float] = {}
                    if is_p_unrelated and prev_center is None:
                        processing_times = {m: round(job_rand.randint(
                            min_processtime, max_processtime)/m.processing_speed, 1) for m in eligible_machines}
                    else:
                        if prev_center is not None:
                            # case of identital and different parallel machines
                            processing_time = job_rand.randint(
                                min_processtime, max_processtime)
                            processing_times = {
                                m: round(processing_time/m.processing_speed, 1) for m in eligible_machines}

                    # if operations have been initialized before replace processing times and eligible machines
                    if len(prev_center_jobs.items()) != 0:
                        prev_center_operation: Operation = prev_center_jobs[self.jobs[j]
                                                                            ].operations[op_idx]
                        # processing_time =

                    # the operation is only initialized and will be finalized later in the code
                    operation = Operation(
                        job=None,
                        machine=None,
                        processing_time=processing_time,
                        eligible_machines=eligible_machines,
                        processing_times=processing_times
                    )
                    operations.append(operation)

                # will need to be adjusted once more alpha fields are added
                # make sure given sequence contains
                if is_jobshop:
                    sequence = job_rand.sample(range(num_operations), num_operations)

                # create job parameters
                release_time = float(job_rand.randint(0, math.ceil(
                    makespan_estimation*0.43))) if self._instance_environment.is_release else None
                duedate_estimation = float(
                    (release_time or 0) + math.ceil(num_operations * average_processingtime * 1.49))
                due_date = (float(math.ceil(duedate_estimation + job_rand.randint(0, math.ceil(makespan_estimation*0.19)))),
                            float(job_rand.randint(2, 7))) if self._instance_environment.is_due else None
                deadline_estimation = float(
                    (release_time or 0) + math.ceil(num_operations * average_processingtime * 1.99))
                if due_date:
                    deadline_estimation = max(deadline_estimation, due_date[0])
                deadline = math.ceil(deadline_estimation + job_rand.randint(0, math.ceil(
                    makespan_estimation * 0.11))) if self._instance_environment.is_deadline else None
                operations: List[Operation] = []

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
                        len(possible_pred), job_rand.randint(0, 2))
                    if min_num_pred > 0:
                        predecessors = job_rand.sample(
                            possible_pred, k=min_num_pred)

                # Create the job
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
                        machine: Optional[Machine] = machines[job.sequence[idx]
                                                              ] if job.sequence else None
                        # i couldnt figure out a better way to handle this lol
                        op.initialize_operation(job, machine)
                self.jobs.append(job)

                if breakdowns_possible:
                    pass

                if setup_necessary:
                    for machine in machines:
                        if machine.setup_times is not None:
                            for job_pair in [(job, other_job) for other_job in self.jobs if other_job != job]:
                                if machine_rand.random() < 0.19:  # 19% chance setup is important
                                    # check if same setup for all machines or
                                    machine.setup_times[job_pair] = machine_rand.randint(
                                        2, 7)

            if prev_center is None:
                prev_center = self.centers[0]
