#!/usr/bin/env python3

from typing import Dict, List, Optional
from pathlib import Path

from instance import Instance
from schedulingfield import InstanceEnvironment

# Absolute Path of current file
# pylint: disable=invalid-name
SCRIPT_DIR = Path(__file__).resolve().parent


class DataLoader:
    """A class to load and manage scheduling instances from a directory structure."""

    def __init__(self, instance_environment: InstanceEnvironment, num_instances: int = 11) -> None:
        """
        Initialize the DataLoader by parsing the alpha|beta|gamma fields

        Args:
            instance_environment (InstanceEnvironment): the instance environment of generated instances
            num_instances (int): number of instances that are created for each instance size
        """
        if instance_environment is None:
            raise ValueError(
                "Specific instance_environment: InstanceEnvironment needed to create instances!")

        self._instance_environment: InstanceEnvironment = instance_environment
        self._number_of_instances: int = num_instances
        self._data_dir: Path = Path(SCRIPT_DIR, "instances")
        self._instances: Dict[str, List[Instance]] = {}
        self._instances_by_name: Dict[str, Instance] = {}
        self._create_instances()

    def _create_instances(self) -> None:
        """create the instances"""
        set_name = str(self._instance_environment)
        self._instances[set_name] = []
        for i in range(self._number_of_instances):
            instance = Instance(self._instance_environment, i)
            self._instances[set_name].append(instance)

    def get_instances(self) -> List[Instance]:
        """
        Retrieve a list of instances.
        Returns:
            List[Instance]: List of instances.
        """
        all_instances = []
        for instance_list in self._instances.values():
            all_instances.extend(instance_list)
        return all_instances

    def get_dataset_by_name(self, dataset_name: str) -> Optional[Instance]:
        """Returns an instance matching the instance dataset_name"""
        return self._instances_by_name.get(dataset_name, None)

    def __len__(self) -> int:
        """Return the total number of instances."""
        return sum(len(instances) for instances in self._instances.values())
