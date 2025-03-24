#!/usr/bin/env python3

import math
import random
from typing import Dict, List, Optional, Tuple

from center import Center
from job import Job, JobInitializer
from instanceconfig import InstanceConfig
from machine import Machine
from operation import Operation, OperationInitializer
from schedulingfield import InstanceEnvironment


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
        self.config: InstanceConfig = InstanceConfig(instance_environment)
        self._seed: int = seed
        self.name: str = f"{str(instance_environment).replace("|", "-").replace(",", "-")}"
        self.jobs: List[Job] = []
        self.centers: List[Center] = []
        self._create_instance()

    def __str__(self) -> str:
        return f"{str(self.name)}_s{self._seed}"
    
    def print_to_file(self) -> None:
        """prints instance with config parameters to file"""
        pass

    def _create_centers_machines(self, machine_rand: random.Random) -> None:
        """creates centers and machines according to instanceConfig"""
        num_centers = self.config.num_centers
        num_machines = self.config.num_machines
        is_p_different: bool = self.config.p_different
        is_p_unrelated: bool = self.config.p_unrelated
        setup_necessary: bool = self.config.setup_necessary
        breakdowns_possible: bool = self.config.breakdowns_possible

        self.centers: List[Center] = []
        for i in range(num_centers):
            self.centers.append(Center(i))
            for j in range(num_machines):
                speed: float = 1.0
                if is_p_different or is_p_unrelated:
                    min_speed = self.config.machine_speed[0]
                    max_speed = self.config.machine_speed[1]
                    speed = round(machine_rand.uniform(min_speed, max_speed), 1)
                setup_times: Optional[Dict] = None
                if setup_necessary:
                    setup_times = {}
                breakdowns: Optional[List] = None
                if breakdowns_possible:
                    breakdowns = []
                machine = Machine(
                    j, self.centers[i], speed, setup_times, breakdowns)
                self.centers[i].machines.append(machine)
    
    def _create_operations_per_job(self, job_rand: random.Random) -> List[OperationInitializer]:
        num_operations = self.config.num_operations
        is_p_unrelated: bool = self.config.p_unrelated
        is_eligible: bool = self.config.eligible
        # TODO implement case that only one center is eligible
        # is_same_mj: bool = self.config.same_mj
        min_processtime, max_processtime = self.config.process_time
        eligible_machines: List[Machine] = []

        for center in self.centers:
            eligible_machines.extend(center.machines)

        operation_initializers: List[OperationInitializer] = []
        # initialize
        for o in range(num_operations):
            new_operation = OperationInitializer(id=o)
            operation_initializers.append(new_operation)
        
        if is_eligible:
            for o, _ in enumerate(operation_initializers):
                machines_at_index = [center.machines[o] for center in self.centers if center.machines[o]]
                if machines_at_index:
                    # change minimum to 0 in case for openshop?
                    num_selected = job_rand.randint(1, len(machines_at_index))
                    selected_machines = job_rand.sample(machines_at_index, num_selected)
                    eligible_machines.extend(selected_machines)
                else:
                    raise ValueError(
                        f"No valid machines found at index {o} across centers!")
                new_operation.eligible_machines = eligible_machines
        else:
            for o, _ in enumerate(operation_initializers):
                new_operation.eligible_machines = [center.machines[o]
                                     for center in self.centers if center.machines[o]]
    
        for op in operation_initializers:
            processing_times: Dict[Machine, float] = {}
            if is_p_unrelated:
                processing_times = {m: round(job_rand.randint(min_processtime, max_processtime) / m.processing_speed, 1) for m in eligible_machines if m}
            else:
                processing_time = job_rand.randint(min_processtime, max_processtime)
                processing_times = {m: round(processing_time / m.processing_speed, 1) for m in eligible_machines if m}

            new_operation.processing_times = processing_times
            operation_initializers.append(new_operation)

        return operation_initializers

    def _create_jobs(self, job_rand: random.Random) -> None:
        # jobs and operations
        self.jobs: List[Job] = []
        job_initializers: List[JobInitializer] = []
        operation_initializers: List[OperationInitializer] = []
        num_jobs: int = self.config.num_jobs
        num_operations: int = self.config.num_operations
        num_machines: int = self.config.num_machines
        num_centers: int = self.config.num_centers
        min_processtime, max_processtime = self.config.process_time
        min_predecessors, max_predecessors = self.config.predecessors

        # alpha field parameters
        is_flowshop: bool = self.config.flowshop
        is_jobshop: bool = self.config.jobshop
        is_openshop: bool = self.config.openshop
        
        # beta field parameters
        is_release: bool = self.config.release
        is_due: bool = self.config.due
        is_deadline: bool = self.config.deadline
        is_precedence: bool = self.config.precedence

        average_processingtime: float = (min_processtime + max_processtime)/2
        makespan_estimation = float(math.ceil(num_jobs * average_processingtime/num_centers))

        for j in range(num_jobs):
            operation_initializers = self._create_operations_per_job(job_rand)
            job_initializers.append(JobInitializer(id=j))

        for job_init in job_initializers:
            if is_flowshop:
                sequence = list(range(num_machines))
            elif is_openshop:
                sequence = [] # determined when solving
            elif not is_jobshop:
                sequence = job_rand.sample(range(num_machines), num_machines)
                makespan_estimation = math.ceil(makespan_estimation / num_machines)
        
            release_time = float(job_rand.randint(0, math.ceil(makespan_estimation*self.config.release_factor))) if is_release else None
            duedate_estimation = float((release_time or 0) + math.ceil(num_operations * average_processingtime * self.config.due_date_factors[0]))
            due_date = (float(math.ceil(duedate_estimation + job_rand.randint(0, math.ceil(makespan_estimation*self.config.due_date_factors[1])))),
                        float(job_rand.randint(int(self.config.due_date_penalty[0]), int(self.config.due_date_penalty[1])))) if is_due else None
            deadline_estimation = float(
                (release_time or 0) + math.ceil(num_operations * average_processingtime * self.config.due_date_factors[2]))
            if due_date:
                    deadline_estimation = max(deadline_estimation, due_date[0])
            deadline = math.ceil(deadline_estimation + job_rand.randint(0, math.ceil(
                makespan_estimation * self.config.deadline_factor))) if is_deadline else None
            
            predecessors: List[Job] = []
            if is_precedence:
                possible_pred: List[Job] = []
                for job in self.jobs:
                    pred_earliest_possible = (
                        job.release_time or 0) + job.total_processing_time()
                    if not release_time or release_time > pred_earliest_possible:
                        possible_pred.append(job)
                    num_pred: int = min(
                        len(possible_pred), job_rand.randint(min_predecessors, max_predecessors))
                if num_pred > 0:
                    predecessors = job_rand.sample(possible_pred, k=num_pred)

            job_init.release_time = release_time
            job_init.due_date = due_date
            job_init.deadline = deadline
            job_init.predecessors = predecessors

            

    def _create_instance(self) -> None:
        """Generate parameters for the scheduling instance, including jobs, machines, and operations."""
        if len(self.jobs) != 0 and len(self.centers) != 0:
            return

        job_seed: int = self.config.job_seed + self._seed
        job_rand = random.Random(job_seed)
        machine_seed: int = self.config.machine_seed + self._seed
        machine_rand = random.Random(machine_seed)

        # some parameter for further use few lines down
        setup_necessary: bool = self.config.setup_necessary
        breakdowns_possible: bool = self.config.breakdowns_possible

        # Cases for Hybrids
        # to avoid recalculating job sequences, releasedates, duedates ..
        prev_center: Optional[Center] = None

        self._create_centers_machines(machine_rand)
        self._create_jobs(job_rand)

        

        for center in self.centers:
            if center.machines is None or (center.machines and len(center.machines) == 0):
                raise ValueError("Machines not assigned to center!")

            machines = center.machines
            for j in range(num_jobs):
                for op_idx in range(num_operations):
                    

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
                
                # TODO here jobinitializer
                # create job parameters
                release_time = float(job_rand.randint(0, math.ceil(
                    makespan_estimation*self.config.release_factor))) if is_release else None
                duedate_estimation = float(
                    (release_time or 0) + math.ceil(num_operations * average_processingtime * self.config.due_date_factors[0]))
                due_date = (float(math.ceil(duedate_estimation + job_rand.randint(0, math.ceil(makespan_estimation*self.config.due_date_factors[1])))),
                            float(job_rand.randint(int(self.config.due_date_penalty[0]), int(self.config.due_date_penalty[1])))) if is_due else None
                deadline_estimation = float(
                    (release_time or 0) + math.ceil(num_operations * average_processingtime * self.config.due_date_factors[2]))
                if due_date:
                    deadline_estimation = max(deadline_estimation, due_date[0])
                deadline = math.ceil(deadline_estimation + job_rand.randint(0, math.ceil(
                    makespan_estimation * self.config.deadline_factor))) if is_deadline else None
                operations: List[Operation] = []

                predecessors: List[Job] = []
                # TODO think about better approach this only creates outtrees
                # also: satisfiability <-> deadlines
                if is_precedence:
                    possible_pred: List[Job] = []
                    for job in self.jobs:
                        pred_earliest_possible = (
                            job.release_time or 0) + job.total_processing_time()
                        if not release_time or release_time >= pred_earliest_possible:
                            possible_pred.append(job)
                        num_pred: int = min(
                        len(possible_pred), job_rand.randint(self.config.predecessors[0], self.config.predecessors[1]))
                    if num_pred > 0:
                        predecessors = job_rand.sample(
                            possible_pred, k=num_pred)

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
