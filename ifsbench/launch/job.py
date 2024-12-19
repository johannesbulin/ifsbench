# (C) Copyright 2020- ECMWF.
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

"""
Hardware and job resource description classes
"""
from abc import ABC
from collections import UserDict
from enum import Enum, auto
from ..logging import error


__all__ = ['CpuBinding', 'CpuDistribution', 'Job']

class CpuConfiguration:
    """
    Abstract base class to describe the hardware configuration of compute nodes

    :any:`Arch` should provide an implementation of this class to describe the
    CPU configuration of the available nodes.

    Attributes
    ----------
    sockets_per_node : int
        The number of sockets (sometimes this is also used to describe NUMA domains)
        available on each node. This must be specified in a derived class.
    cores_per_socket : int
        The number of physical cores per socket. This must be specified in a derived class.
    threads_per_core : int
        The number of logical cores per physical core (i.e. the number of SMT threads
        each core can execute). Typically, this is 1 (no hyperthreading), 2 or 4.
        This must be specified in a derived class.
    cores_per_node : int
        The number of physical cores per node. This value is automatically derived
        from the above properties.
    threads_per_node : int
        The number of logical cores per node (threads). This value is automatically derived
        from the above properties.
    gpus_per_node : int
        The number of available GPUs per node.
    """

    sockets_per_node: int

    cores_per_socket: int

    threads_per_core: int

    gpus_per_node = 0

    def cores_per_node(self):
        """
        The number of physical cores per node
        """
        return self.sockets_per_node * self.cores_per_socket

    def threads_per_node(self):
        """
        The number of logical cores (threads) per node
        """
        return self.cores_per_node * self.threads_per_core

class CpuBinding(Enum):
    """
    Description of CPU binding strategy to use, for which the launch
    command should provide the appropriate options
    """
    BIND_NONE = auto()
    """Disable all binding specification"""

    BIND_SOCKETS = auto()
    """Bind tasks to sockets"""

    BIND_CORES = auto()
    """Bind tasks to cores"""

    BIND_THREADS = auto()
    """Bind tasks to hardware threads"""

    BIND_USER = auto()
    """Indicate that a different user-specified strategy should be used"""


class CpuDistribution(Enum):
    """
    Description of CPU distribution strategy to use, for which the launch
    command should provide the appropriate options
    """
    DISTRIBUTE_DEFAULT = auto()
    """Use the default distribution strategy"""

    DISTRIBUTE_BLOCK = auto()
    """Allocate ranks/threads consecutively"""

    DISTRIBUTE_CYCLIC = auto()
    """Allocate ranks/threads in a round-robin fashion"""

    DISTRIBUTE_USER = auto()
    """Indicate that a different user-specified strategy should be used"""

class Job(UserDict):
    """
    Description of a parallel job's resource requirements. It is a dictionary
    (UserDict).

    Parameters
    ----------
    job : Job, optional
        If given, a copy of this job will be created.
    tasks : int, optional
        The total number of MPI tasks to be used.
    nodes : int, optional
        The total number of nodes to be used.
    tasks_per_node : int, optional
        Launch a specific number of tasks per node.
    tasks_per_socket : int, optional
        Launch a specific number of tasks per socket.
    cpus_per_task : int, optional
        The number of computing elements (threads) available to each task for hybrid jobs.
    threads_per_core : int, optional
        Enable symmetric multi-threading (hyperthreading).
    gpus_per_task : int, optional
        The number of GPUs that are used per task.
    account : str, optional
        The account that is passed to the scheduler.
    partition: str, optional
        The partition that is passed to the scheduler.
    bind : :any:`CpuBinding`, optional
        Specify the binding strategy to use for pinning.
    distribute_remote : :any:`CpuDistribution`, optional
        Specify the distribution strategy to use for task distribution across nodes.
    distribute_local : :any:`CpuDistribution`, optional
        Specify the distribution strategy to use for task distribution across
        sockets within a node.
    """

    def __init__(self, job=None, **kwargs):
        if job:
            super().__init__(job, **kwargs)
        else:
            super().__init__(**kwargs)

