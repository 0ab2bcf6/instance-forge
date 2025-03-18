#!/usr/bin/env python3

from enum import Enum
import hashlib
from typing import List, Optional, Tuple


class SchedulingField(Enum):
    """
    Enum for alpha|beta|gamma field notation following the scheduling theory Pinedo (2016)  .
    """

    # alpha field
    SINGLE_MACHINE = "1"
    PARALLEL_IDENTICAL = "P"
    PARALLEL_DIFFERENT = "Q"
    PARALLEL_UNRELATED = "R"
    FLOWSHOP = "F"
    JOBSHOP = "J"
    OPENSHOP = "O"
    FLEXIBLE_FLOWSHOP = "FF"
    FLEXIBLE_JOBSHOP = "FJ"
    # DISTRIBUTED_FLOWSHOP = "DF"
    # DISTRIBUTED_JOBSHOP = "DJ"

    # beta field
    NO_CONSTRAINTS = ""
    PRECEDENCE = "prec"
    RELEASE_TIMES = "r_j"
    DUE_DATES = "d_j"
    DEADLINES = "bar_d_j"
    SETUP_TIMES = "s_ij"
    SEQUENCE_DEPENDENT_SETUP = "s_jk"
    MACHINE_ELIGIBILITY = "M_j"
    NO_WAIT = "nwt"
    PREEMPTION = "prmp"
    BLOCK = "block"
    BREAKDOWNS = "brkdwn"
    PERMUTATION = "perm"
    RECIRCULATION = "rcrc"
    # BATCH = "batch" # TODO n x m parameters possible, job-machine batch rules
    # JOB_FAMILIES = "fmls" # TODO n parameters for family assignments
    # TODO explicit prec (intree, outtree, chains, ..)

    # gamma field
    MAKESPAN = "C_max"
    TOTAL_COMPLETION_TIME = "sum_C_j"
    TOTAL_WEIGHTED_COMPLETION = "sum_w_j_C_j"
    EARLYNESS = "sum_E_j"
    WEIGHTED_EARLYNESS = "sum_w_j_E_j"
    MAX_LATENESS = "L_max"
    TOTAL_TARDINESS = "sum_T_j"
    WEIGHTED_TARDINESS = "sum_w_j_T_j"
    NUMBER_LATE_JOBS = "sum_U_j"
    WEIGHTED_LATE_JOBS = "sum_w_j_U_j"
    TOTAL_ABS_DEVIATION = "sum_d_j-C_j"
    # TODO electricity cost, energy consumption, emission?

    def __str__(self) -> str:
        """Return the string representation used in scheduling notation."""
        return self.value

    @classmethod
    def alpha_fields(cls) -> list:
        """Return all alpha field values."""
        return [f for f in cls if f.name in {"SINGLE_MACHINE", "PARALLEL_IDENTICAL", "PARALLEL_UNRELATED", "FLOWSHOP", "JOBSHOP", "OPENSHOP", "FLEXIBLE_FLOWSHOP", "FLEXIBLE_JOBSHOP"}]

    @classmethod
    def beta_fields(cls) -> list:
        """Return all beta field values."""
        return [f for f in cls if f.name in {"NO_CONSTRAINTS", "PRECEDENCE", "RELEASE_TIMES", "DUE_DATES", "DEADLINES", "SETUP_TIMES", "SEQUENCE_DEPENDENT_SETUP", "MACHINE_ELIGIBILITY", "NO_WAIT", "PREEMPTION", "BLOCK", "BREAKDOWNS", "PERMUTATION", "RECIRCULATION", "BATCH", "JOB_FAMILIES"}]

    @classmethod
    def gamma_fields(cls) -> list:
        """Return all gamma field values."""
        return [f for f in cls if f.name in {"MAKESPAN", "TOTAL_COMPLETION_TIME", "TOTAL_TARDINESS", "WEIGHTED_TARDINESS", "TOTAL_WEIGHTED_COMPLETION", "MAX_LATENESS", "NUMBER_TARDY_JOBS"}]


class InstanceEnvironment:
    """
    A class to define the scheduling environment using alpha|beta|gamma notation,
    with validation for nonsensical beta field combinations and gamma dependencies.
    """

    _CONFLICTING_ALPHA_BETA_PAIRS = {
        ("1", "M_j"),
        ("1", "rcrc"),
        ("1", "nwt"),
        ("P", "perm"),
        ("P", "nwt"),
        ("P", "rcrc"),
        ("Q", "perm"),
        ("Q", "nwt"),
        ("Q", "rcrc"),
        ("R", "perm"),
        ("R", "nwt"),
        ("R", "rcrc"),
        ("F", "prmp"),
        ("F", "M_j"),
        ("F", "rcrc"),
        ("J", "block"),
        ("J", "perm"),
        ("J", "M_j"),
        ("O", "block"),
        ("O", "perm"),
        ("O", "M_j"),
        ("O", "rcrc"),
        ("FF", "prmp"),
        ("FF", "M_j"),
        ("FF", "nwt"),
        ("FF", "rcrc"),
        ("FJ", "nwt")
    }

    _CONFLICTING_BETA_PAIRS = {
        ("nwt", "prmp"),
        ("nwt", "s_ij"),
        ("nwt", "s_jk"),
        ("nwt", "block"),
        ("s_ij", "s_jk"),
        ("perm", "rcrc"),
        ("perm", "block"),
        ("batch", "nwt"),
        ("batch", "prmp"),
    }

    _WEIGHTED_GAMMA_FIELDS = {
        "sum_w_j_C_j",
        "sum_w_j_E_j",
        "sum_w_j_T_j",
        "sum_w_j_U_j"
    }

    _TIME_GAMMA_FIELDS = {
        "L_max",
        "sum_E_j",
        "sum_w_j_E_j",
        "sum_T_j",
        "sum_w_j_T_j",
        "sum_U_j",
        "sum_w_j_U_j",
        "sum_d_j-C_j"
    }

    _CENTER_ALPHA_FIELDS = {
        "FF",
        "FJ"
    }

    # not sure what to do with deadline
    _REQUIRED_BETA_FOR_TARDINESS = {"d_j", "bar_d_j"}

    def __init__(self,
                 alpha: SchedulingField = SchedulingField.SINGLE_MACHINE,
                 beta: Optional[List[SchedulingField]] = None,
                 gamma: SchedulingField = SchedulingField.MAKESPAN,
                 num_jobs: int = 5,
                 num_machines: int = 1,
                 num_centers: int = 1) -> None:
        """Initialize the instance environment by selecting alpha|beta|gamma field, number of jobs and number of machines.

        Args:
            alpha (SchedulingField): Machine environment, defaults to SchedulingField.SINGLE_MACHINE.
            beta (Optional[List[SchedulingField]]): List of constraints.
            gamma (SchedulingField): Objective function, defaults to SchedulingField.MAKESPAN.
            num_jobs (int): Number of jobs, defaults to 5.
            num_machines (int): Number of machines, defaults to 1.

        Raises:
            ValueError: If beta contains conflicting or nonsensical combinations.
        """
        if num_jobs <= 0:
            raise ValueError(f"num_jobs must be greater-or-equal 1, got {num_jobs}")
        if num_machines <= 0:
            raise ValueError(
                f"num_machines must be greater-or-equal 1, got {num_machines}")
        if num_centers <= 0:
            raise ValueError(
                f"num_centers must be greater-or-equal 1, got {num_centers}")
        if num_machines > num_jobs:
            raise ValueError(
                f"num_machines must be smaller-or-equal to num_jobs, got {num_machines} machines with {num_jobs} jobs")

        self.alpha: SchedulingField = alpha
        self.beta: Optional[List[SchedulingField]
                            ] = beta if beta is not None else []
        self.gamma: SchedulingField = gamma
        self.num_jobs: int = num_jobs
        self.num_machines: int = num_machines
        self.num_centers: int = num_centers

        self._validate_alpha_field()
        self._validate_beta_field()
        self._validate_alpha_beta_dependencies()
        self._validate_beta_combinations()
        self._validate_gamma_field()
        self._validate_gamma_beta_dependencies()

        # beta setup
        self.is_breakdown: bool = False
        self.is_eligible: bool = False
        self.is_release: bool = False
        self.is_due: bool = False
        self.is_deadline: bool = False
        self.is_precedence: bool = False
        self.is_setuptime: bool = False
        self.is_setuptime_seq: bool = False
        self._get_beta_setup()

        # gamma setup
        self.is_weighted: bool = False
        self._get_gamma_setup()

        self.num_operations: int = self._get_num_operations()
        self.sequence_setup: Optional[Tuple[bool,
                                            bool]] = self._get_is_fixed_sequence()

        self.time_seed: int = self._generate_seed()
        self.machine_seed: int = self._generate_seed(True)  # unused this far

    def _get_num_operations(self) -> int:
        """returns number of operations depending on alpha field"""
        equal_to_machines = [
            SchedulingField.FLOWSHOP, SchedulingField.JOBSHOP, SchedulingField.OPENSHOP]
        if self.alpha in equal_to_machines:
            return self.num_machines
        return 1

    def _get_beta_setup(self) -> None:
        """get setup information regarding beta field"""
        if self.beta is None:
            return
        # conflicting beta fields are checked in _validate_beta_combinations()
        if SchedulingField.BREAKDOWNS in self.beta:
            self.is_breakdown = True
        if SchedulingField.MACHINE_ELIGIBILITY in self.beta:
            self.is_eligible = True
        if SchedulingField.RELEASE_TIMES in self.beta:
            self.is_release = True
        if SchedulingField.DUE_DATES in self.beta:
            self.is_due = True
        if SchedulingField.DEADLINES in self.beta:
            self.is_deadline = True
        if SchedulingField.PRECEDENCE in self.beta:
            self.is_precedence = True
        if SchedulingField.SETUP_TIMES in self.beta:
            self.is_setuptime = True
        if SchedulingField.SEQUENCE_DEPENDENT_SETUP in self.beta:
            self.is_setuptime_seq = True

    def _get_gamma_setup(self) -> None:
        """get setup information regarding gamma field"""
        if self.gamma in self._WEIGHTED_GAMMA_FIELDS:
            self.is_weighted = True

    def _get_is_fixed_sequence(self) -> Optional[Tuple[bool, bool]]:
        """returns if sequence is fixed and identical"""
        if self.alpha == SchedulingField.FLOWSHOP:
            return (True, True)
        elif self.alpha == SchedulingField.JOBSHOP:
            return (True, False)
        elif self.alpha == SchedulingField.OPENSHOP:
            return (False, False)
        return None

    def _generate_seed(self, reverse: bool = False) -> int:
        """
        Generate a deterministic seed based on the class attributes.

        Args:
            reverse Optional(bool): reverse input for hash

        Returns:
            int: A positive integer seed derived from alpha, beta, gamma, num_jobs and num_machines.
        """
        beta_val = tuple(sorted(b.value for b in self.beta)
                         ) if self.beta else tuple()

        # combine attributes into a tuple
        combined = (self.alpha.value, beta_val, self.gamma.value,
                    self.num_jobs, self.num_machines, self.num_centers)
        if reverse:
            combined = (self.num_centers, self.num_machines, self.num_jobs,
                        self.gamma.value, beta_val, self.alpha.value)

        # convert to a string and hash with SHA-256 for stability
        combined_str = str(combined).encode('utf-8')
        # convert hash to integer
        seed = int(hashlib.sha256(combined_str).hexdigest(), 16)

        # restrict to 32-bit unsigned integer range (0 to 2^32 - 1)
        seed = seed % (2**32)
        return seed

    def _validate_alpha_field(self) -> None:
        """checks for valid alpha fields."""

        if self.alpha not in SchedulingField.alpha_fields():
            raise ValueError(f"{self.alpha} is not a valid alpha field")

        # validate num_machines for single machine environment
        if self.alpha == SchedulingField.SINGLE_MACHINE and self.num_machines != 1:
            raise ValueError(
                f"num_machines must be 1 for SINGLE_MACHINE, got {self.num_machines}")
        elif self.alpha != SchedulingField.SINGLE_MACHINE and self.num_machines == 1:
            raise ValueError(
                f"alpha must be SINGLE_MACHINE, if num_machines is 1")

        # validate alpha field for num_centers
        if self.alpha in self._CENTER_ALPHA_FIELDS and self.num_centers != 1:
            raise ValueError(
                f"num_centers must be >1 for alpha field {self.alpha}, got {self.num_centers}")
        elif self.alpha not in self._CENTER_ALPHA_FIELDS and self.num_centers > 1:
            raise ValueError(
                f"num_centers must be 1 for for alpha field {self.alpha}, got {self.num_centers}")

    def _validate_beta_field(self) -> None:
        """checks for valid beta fields."""
        if self.beta is None:
            return
        invalid_beta_fields: List[SchedulingField] = []
        for beta in self.beta:
            if beta not in SchedulingField.beta_fields():
                invalid_beta_fields.append(beta)
        if len(invalid_beta_fields) > 0:
            val_err: str = ",".join(
                [entry.value for entry in invalid_beta_fields])
            raise ValueError(f"{val_err} are not a valid beta fields")

    def _validate_gamma_field(self) -> None:
        """checks for valid gamma fields."""
        if self.gamma is None:
            raise ValueError("gamma field cannot be None")

        if self.gamma not in SchedulingField.gamma_fields():
            raise ValueError(f"{self.gamma} is not a valid gamma field")

    def _validate_beta_combinations(self) -> None:
        """Check for nonsensical or conflicting beta field combinations."""
        if not self.beta:
            return

        beta_set = set(b.value for b in self.beta)

        if "" in beta_set and len(beta_set) > 1:
            raise ValueError(
                "NO_CONSTRAINTS cannot be combined with other beta constraints")

        # Check for conflicting pairs
        for conflict_pair in self._CONFLICTING_BETA_PAIRS:
            if conflict_pair[0] in beta_set and conflict_pair[1] in beta_set:
                raise ValueError(
                    f"Conflicting beta constraints: {conflict_pair[0]} and {conflict_pair[1]} cannot be combined")

    def _validate_alpha_beta_dependencies(self) -> None:
        """Ensure sensical alpha and beta fields."""
        if self.beta is None:
            return
        alpha_value = self.alpha.value
        beta_set = set(b.value for b in self.beta)

        for beta_value in beta_set:
            if (alpha_value, beta_value) in self._CONFLICTING_ALPHA_BETA_PAIRS:
                raise ValueError(
                    f"Conflicting alpha-beta pair: ({alpha_value}, {beta_value}) cannot be combined."
                )

    def _validate_gamma_beta_dependencies(self) -> None:
        """Ensure the gamma field has necessary beta fields."""
        if self.gamma is None or self.beta is None:
            return

        gamma_value = self.gamma.value
        beta_set = set(b.value for b in self.beta)

        # check tardiness related objectives
        if gamma_value in self._TIME_GAMMA_FIELDS:
            if not beta_set & self._REQUIRED_BETA_FOR_TARDINESS:
                raise ValueError(
                    f"Gamma field '{gamma_value}' requires DUE_DATES (d_j) or DEADLINES (bar_d_j) in beta")

    def __str__(self) -> str:
        """Return a string representation of the environment."""
        alpha_str = self.alpha.value
        beta_str = ",".join(b.value for b in self.beta) if self.beta else ""
        gamma_str = self.gamma.value
        machines_str = str(
            self.num_machines) if self.num_machines is not None else "Unspecified"
        alpha_full = f"{alpha_str}{machines_str if self.num_machines and self.num_machines > 1 else ''}"
        # , time_seed={self.time_seed}, machine_seed={self.machine_seed}"
        return f"{alpha_full}|{beta_str}|{gamma_str}_n{self.num_jobs}"


if __name__ == "__main__":
    # valid: Jobshop with precedence and 5 machines
    env1 = InstanceEnvironment(
        alpha=SchedulingField.JOBSHOP,
        beta=[SchedulingField.PRECEDENCE, SchedulingField.DUE_DATES],
        gamma=SchedulingField.MAKESPAN,
        num_jobs=31,
        num_machines=7
    )
    print(env1)  # J7|prec,d_j|C_max
    print(f"time_seed: {env1.time_seed}")
    print(f"machine_seed: {env1.machine_seed}")

    # valid: Single machine with due dates since default is cmax
    env2 = InstanceEnvironment(
        alpha=SchedulingField.SINGLE_MACHINE,
        beta=[SchedulingField.DUE_DATES]
    )
    print(env2)  # 1|d_j|Cmax
    print(f"time_seed: {env2.time_seed}")
    print(f"machine_seed: {env2.machine_seed}")

    # invalid: nwt and preemption
    try:
        env3 = InstanceEnvironment(
            alpha=SchedulingField.FLOWSHOP,
            beta=[SchedulingField.NO_WAIT, SchedulingField.PREEMPTION],
            num_machines=3
        )
    except ValueError as e:
        print(f"Error: {e}")

    # invalid: no constraints and others
    try:
        env4 = InstanceEnvironment(
            alpha=SchedulingField.JOBSHOP,
            beta=[SchedulingField.NO_CONSTRAINTS,
                  SchedulingField.RELEASE_TIMES]
        )
    except ValueError as e:
        print(f"Error: {e}")

    # Invalid:
    try:
        env5 = InstanceEnvironment(
            alpha=SchedulingField.JOBSHOP,
            beta=[SchedulingField.PRECEDENCE, SchedulingField.DUE_DATES],
            gamma=SchedulingField.MAKESPAN,
            num_jobs=9,
            num_machines=11
        )
        print(env5)
    except ValueError as e:
        print(f"Error: {e}")

    # Invalid:
    try:
        env6 = InstanceEnvironment(
            alpha=SchedulingField.JOBSHOP,
            beta=[SchedulingField.BLOCK],
            gamma=SchedulingField.TOTAL_TARDINESS,
            num_jobs=31,
            num_machines=7
        )
        print(env6)
    except ValueError as e:
        print(f"Error: {e}")

    # alpha = SchedulingField.JOBSHOP,
    # beta = [SchedulingField.PRECEDENCE, SchedulingField.DUE_DATES],
    # gamma = SchedulingField.MAKESPAN,

    # Invalid:
    try:
        env7 = InstanceEnvironment(
            alpha=SchedulingField.TOTAL_COMPLETION_TIME,
            beta=[SchedulingField.JOBSHOP, SchedulingField.FLOWSHOP],
            gamma=SchedulingField.BLOCK,
            num_jobs=31,
            num_machines=7
        )
        print(env7)
    except ValueError as e:
        print(f"Error: {e}")

    # Invalid:
    try:
        env8 = InstanceEnvironment(
            alpha=SchedulingField.JOBSHOP,
            beta=[SchedulingField.JOBSHOP, SchedulingField.FLOWSHOP],
            gamma=SchedulingField.TOTAL_COMPLETION_TIME,
            num_jobs=31,
            num_machines=7
        )
        print(env8)
    except ValueError as e:
        print(f"Error: {e}")

    # Invalid:
    try:
        env9 = InstanceEnvironment(
            alpha=SchedulingField.FLOWSHOP,
            beta=[SchedulingField.DUE_DATES, SchedulingField.PERMUTATION],
            gamma=SchedulingField.BLOCK,
            num_jobs=31,
            num_machines=7
        )
        print(env9)
    except ValueError as e:
        print(f"Error: {e}")

    # Invalid:
    try:
        env10 = InstanceEnvironment(
            alpha=SchedulingField.JOBSHOP,
            beta=[SchedulingField.DUE_DATES, SchedulingField.PERMUTATION],
            gamma=SchedulingField.MAKESPAN,
            num_jobs=31,
            num_machines=7
        )
        print(env10)
    except ValueError as e:
        print(f"Error: {e}")
