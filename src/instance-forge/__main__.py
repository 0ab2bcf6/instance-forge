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

def prime_instance_params() -> Tuple[List[int], List[int]]:
    """
    returns: (num_jobs, num_machines) as Tuple

    numbers are selected based on primes
    7 is the 4th prime -> 7+4 = 11 -> 11th prime is 31
    choose the higher number of the first twin prime
    pair in the interval of 7 and 31 -> (11, 13) -> 13
    13 is the 6th prime ... (and so on)
    """
    return ([31, 67, 103, 181, 331], [7, 13, 19, 31, 43])
    

if __name__ == "__main__":
    
    instance_env = InstanceEnvironment(
        alpha=SchedulingField.SINGLE_MACHINE,
        beta=[SchedulingField.PRECEDENCE],
        gamma=SchedulingField.MAKESPAN,
        num_jobs=31,
    )
    print(str(instance_env))

    loader = DataLoader(instance_env, 10)
    for job in loader.get_instances()[0].jobs:
        print(job.name, [job1.name for job1 in job.predecessors])
