# (C) Copyright 2020- ECMWF.
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

"""
Architecture specifications
"""
from abc import ABC, abstractmethod
import os

from ..envhandler import EnvHandler, EnvOverride
from ..logging import debug, info
from .job import CpuConfiguration, CpuBinding, Job

__all__ = ['Arch', 'DefaultArch']


class Arch(ABC):
    """
    Machine and compiler architecture on which to run the IFS

    This provides compiler and environment assumptions for MPI-parallel runs.

    An implementation of this class must be provided for each target system.
    It must declare the CPU configuration in :attr:`cpu_config` and the
    launcher in :attr:`launcher` that is used for MPI-parallel execution.

    For multiple toolchains/runtime environments on a single physical system
    it can be beneficial to create an intermediate class describing common
    properties (such as :attr:`cpu_config`) and derived classes to specify
    the bespoke configuration.
    """


    @abstractmethod
    def get_default_launcher(self):
        return NotImplemented

    @abstractmethod
    def process(self, job, **kwargs):
        """
        Return Job and EnvHandler list.
        """
        return NotImplemented

class DefaultArch(Arch):

    def __init__(self, launcher, cpu_config, account=None, partition=None):
        self._cpu_config = cpu_config
        self._launcher = launcher
        self._account = account
        self._partition = partition

    def get_default_launcher(self):
        return self._launcher

    def process(self, job, **kwargs):
        env_handlers = []

        account = self._account
        partition = self._partition

        job = Job(job=job, **kwargs)

        if partition:
            job.set('partition', partition)
        if account:
            job.set('account', account)

        if job.get('cpus_per_task', None):
            override = EnvOverride('OMP_NUM_THREADS', EnvOverride.EnvOperation.SET, job.get('cpus_per_task', None))
            env_handlers.append(EnvHandler([override]))


        return job, env_handlers