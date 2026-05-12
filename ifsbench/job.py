# (C) Copyright 2020- ECMWF.
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

"""
Hardware and job resource description classes.
"""

from enum import Enum
from typing import List, Optional, Union

from pydantic import model_validator, TypeAdapter
from typing_extensions import Self

from ifsbench.serialisation_mixin import SerialisationMixin

__all__ = ['CpuBinding', 'CpuDistribution', 'CpuConfiguration', 'Job', 'JobOperation', 'JobOverride']


class CpuConfiguration(SerialisationMixin):
    """
    This class describes the hardware configuration of compute nodes.
    """

    #: The number of sockets (sometimes this is also used to describe NUMA domains)
    #: available on each node. This must be specified in a derived class.
    sockets_per_node: int = 1

    #: The number of physical cores per socket. This must be specified in a derived class.
    cores_per_socket: int = 1

    #: The number of logical cores per physical core (i.e. the number of SMT threads
    #: each core can execute). Typically, this is 1 (no hyperthreading), 2 or 4.
    #: This must be specified in a derived class.
    threads_per_core: int = 1

    #: The number of available GPUs per node.
    gpus_per_node: int = 0

    @property
    def cores_per_node(self):
        """
        The number of physical cores per node. This value is automatically derived
        from the above properties.
        """
        return self.sockets_per_node * self.cores_per_socket

    @property
    def threads_per_node(self):
        """
        The number of logical cores per node (threads). This value is automatically derived
        from the above properties.
        """
        return self.cores_per_node * self.threads_per_core


class CpuBinding(str, Enum):
    """
    Description of CPU binding strategy to use, for which the launch
    command should provide the appropriate options
    """

    BIND_NONE = 'none'
    """Disable all binding specification"""

    BIND_SOCKETS = 'sockets'
    """Bind tasks to sockets"""

    BIND_CORES = 'cores'
    """Bind tasks to cores"""

    BIND_THREADS = 'threads'
    """Bind tasks to hardware threads"""

    BIND_USER = 'user'
    """Indicate that a different user-specified strategy should be used"""


class CpuDistribution(str, Enum):
    """
    Description of CPU distribution strategy to use, for which the launch
    command should provide the appropriate options
    """

    DISTRIBUTE_DEFAULT = 'default'
    """Use the default distribution strategy"""

    DISTRIBUTE_BLOCK = 'block'
    """Allocate ranks/threads consecutively"""

    DISTRIBUTE_CYCLIC = 'cyclic'
    """Allocate ranks/threads in a round-robin fashion"""

    DISTRIBUTE_USER = 'user'
    """Indicate that a different user-specified strategy should be used"""


class Job(SerialisationMixin):
    """
    Description of a parallel job setup.
    """

    #: The number of tasks/processes.
    tasks: Optional[int] = None

    #: The number of nodes.
    nodes: Optional[int] = None

    #: The number of tasks per node.
    tasks_per_node: Optional[int] = None

    #: The number of tasks per socket.
    tasks_per_socket: Optional[int] = None

    #: The number of cpus assigned to each task.
    cpus_per_task: Optional[int] = None

    #: The number of threads that each CPU core should run.
    threads_per_core: Optional[int] = None

    #: The number of GPUs that are required by each node.
    gpus_per_node: Optional[int] = None

    #: The account that is passed to the scheduler.
    account: Optional[str] = None

    #: The partition that is passed to the scheduler.
    partition: Optional[str] = None

    #: Specify the binding strategy to use for pinning.
    bind: Optional[CpuBinding] = None

    #: Specify the distribution strategy to use for task distribution across nodes.
    distribute_remote: Optional[CpuDistribution] = None

    #: Specify the distribution strategy to use for task distribution across
    #: sockets within a node.
    distribute_local: Optional[CpuDistribution] = None

    def clone(self):
        """
        Return a deep copy of this object.
        """

        return self.model_copy(deep=True)

    def calculate_missing(self, cpu_configuration: CpuConfiguration) -> None:
        """
        Calculate missing attributes in :class:`Job`

        If at least one of

        * the total number of MPI tasks (:data:`tasks`)
        * the number of nodes (:data:`nodes`) and the number of tasks per node
          (:data:`tasks_per_node`)
        * the number of nodes (:data:`nodes`) and the number of tasks per socket
          (:data:`tasks_per_socket`)

        is specified, this function calculates missing values for

            * tasks
            * nodes
            * tasks_per_node

        given hardware configuration. The resulting values are stored in this
        object.

        Raises
        ------

        ValueError
            If not enough data is available to compute the missing values or if
            the given values contradict each other.
        """

        cpus_per_task = self.cpus_per_task
        if not cpus_per_task:
            cpus_per_task = 1

        threads_per_core = self.threads_per_core
        if not threads_per_core:
            threads_per_core = 1

        gpus_per_node = self.gpus_per_node or 0

        if not self.tasks_per_node:
            # If tasks_per_node wasn't specified, calculate it from the other
            # values.

            if self.tasks_per_socket:
                self.tasks_per_node = self.tasks_per_socket * cpu_configuration.sockets_per_node
            elif self.tasks:
                self.tasks_per_node = cpu_configuration.cores_per_node // cpus_per_task
            else:
                raise ValueError('The number of tasks per node could not be determined!')

            # If GPUs are used, make sure that tasks_per_node is compatible with
            # the number of available GPUs.
            if gpus_per_node > 0:
                self.tasks_per_node = min(
                    self.tasks_per_node,
                    cpu_configuration.gpus_per_node,
                )

            if self.tasks_per_node <= 0:
                raise ValueError('Failed to determine the number of tasks per node!')

        if self.nodes is None:
            threads_per_node = self.tasks_per_node * threads_per_core * cpus_per_task

            if not self.tasks:
                raise ValueError('The number of nodes could not be determined!')

            self.nodes = (self.tasks * cpus_per_task + threads_per_node - 1) // threads_per_node

        if self.tasks is None:
            self.tasks = self.nodes * self.tasks_per_node

        if gpus_per_node > cpu_configuration.gpus_per_node:
            raise ValueError(
                'The number of requested GPUs per node is '
                'higher than the available number of GPUs per node.'
            )


class JobOperation(str, Enum):
    """
    The type of operation to apply when overriding a Job attribute.
    """

    SET = 'set'
    """Set the attribute to a new value."""

    DELETE = 'delete'
    """Delete (reset to None) an attribute."""


class JobOverride(SerialisationMixin):
    """
    Specify changes that will be applied to a :class:`Job` object.

    Parameters
    ----------
    attribute: str
        The name of the Job field to override.

    mode: JobOperation
        What kind of operation is specified. Can be
            * SET: Set the attribute to a new value.
            * DELETE: Reset the attribute to None.

    value: Union[int, float, str, bool, List, None]
        The value that is set (SET operation).
        Ignored for DELETE.
    """

    attribute: str
    mode: JobOperation
    value: Union[int, float, str, bool, List, None] = None

    @model_validator(mode='after')
    def validate_value_for_mode(self) -> Self:
        if self.mode == JobOperation.SET:
            if self.value is None:
                raise ValueError(
                    f"SET operation requires a non-None value for attribute '{self.attribute}'."
                )
            # Validate that the value is compatible with the Job field's type
            field_info = Job.model_fields.get(self.attribute)
            if field_info is not None:
                try:
                    TypeAdapter(field_info.annotation).validate_python(self.value)
                except Exception as exc:
                    raise ValueError(
                        f"Value {self.value!r} is not valid for "
                        f"Job field '{self.attribute}' "
                        f"(expected {field_info.annotation}): {exc}"
                    ) from exc
        return self

    def override(self, job: Job) -> Job:
        """
        Apply the override to a Job object.

        Creates a copy of the given Job, applies the specified operation
        to the copy, and returns the modified copy.

        Parameters
        ----------
        job: :class:`Job`
            The Job object to override.

        Returns
        -------
        :class:`Job`
            A new Job object with the override applied.

        Raises
        ------
        ValueError
            If the attribute is not a valid Job field.
        """
        if self.attribute not in Job.model_fields:
            raise ValueError(
                f"'{self.attribute}' is not a valid field of Job."
            )

        result = job.clone()

        if self.mode == JobOperation.SET:
            setattr(result, self.attribute, self.value)
        elif self.mode == JobOperation.DELETE:
            setattr(result, self.attribute, None)

        return result
