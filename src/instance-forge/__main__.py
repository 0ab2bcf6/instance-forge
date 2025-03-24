#!/usr/bin/env python3
"""
This is the main entry point for your module, if it is called as a scripts,
e.g.:
python -m your_module
This file contains the primary main() function for your entire project.
"""

from typing import List, Optional, Tuple
from dataloader import DataLoader
from schedulingfield import SchedulingField, InstanceEnvironment
from instance import Instance


if __name__ == "__main__":

    instance_env = InstanceEnvironment(
        alpha=SchedulingField.SINGLE_MACHINE,
        beta=[SchedulingField.PRECEDENCE],
        gamma=SchedulingField.MAKESPAN,
        num_jobs=10
    )
    print(str(instance_env))

    loader = DataLoader(instance_env, 10)
    for job in loader.get_instances()[0].jobs:
        print(job.name, [job1.name for job1 in job.predecessors])
