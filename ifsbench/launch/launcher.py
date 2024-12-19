# (C) Copyright 2020- ECMWF.
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

"""
Implementation of launch commands for various MPI launchers
"""
from abc import ABC, abstractmethod
import datetime

from .job import CpuBinding, CpuDistribution
from ..logging import debug, warning, info
from ..util import execute

__all__ = ['Launcher', 'SrunLauncher', 'MpirunLauncher', 'BashLauncher']


class Launcher(ABC):
    """
    Base class for launching parallel jobs.
    Subclasses should implement the following functions:
        * init_launch
        * cleanup_launch
        * get_command
    """

    job_options_map: dict
    """
    A mapping of :any:`Job` attributes to launch cmd options

    See :meth:`get_options_from_job` for how this is used to build
    launch command options.
    """

    bind_options_map: dict
    """
    A mapping of :any:`CpuBinding` values to launch cmd options

    See :meth:`get_options_from_binding` for how this is used to build
    launch command options.
    """

    def launch(self, run_dir, cmd, job, env=None, custom_flags=None, **kwargs):
        """
        Launch an application. This will
        1. Call init_launch.
        2. Actually run the output of get_command.
        3. Call cleanup_launch.

        Parameters
        ----------
        run_dir : `pathlib.Path`
            The directory in which the application is run.
        cmd: iterable of str
            The command that will be launched.
        env: dict
            Custom environment.
        custom_flags: iterable of str
            Any additional flags that should be passed to the launcher.
        """
        pre_data = self.pre_launch(run_dir, cmd, job, env, custom_flags, **kwargs)

        cmd = self.get_command(run_dir, cmd, job, env, custom_flags, **kwargs, **pre_data)
        info(f"Launch command {cmd} in {run_dir}")

        execute(
            command = cmd,
            cwd = run_dir,
            env = env
        )

        self.post_launch(run_dir, cmd, job, env, custom_flags, **kwargs)

    def pre_launch(self, run_dir, cmd, job, env=None, custom_flags=None, **kwargs):
        return {}

    def post_launch(self, run_dir, cmd, job, env=None, custom_flags=None, **kwargs):
        pass

    @abstractmethod
    def get_command(self, run_dir, cmd, job, env=None, custom_flags=None, **kwargs):
        return NotImplemented


    def get_options_from_job(self, job):
        """
        Build a list of launch command options from the provided :data:`job` specification

        This uses the :attr:`job_options_map` to compile all options according to what
        is specified in :data:`job`.
        The format of :attr:`job_options_map` should be a `dict` with the name of
        :any:`Job` attributes as keys and launch command-specific format strings as
        values, e.g., ``{'tasks': '--ntasks={}'}``.

        Only attributes from :attr:`job_options_map` that are defined (i.e. do not raise
        :any:`AttributeError`) are added to the list of options, thus this provides a
        direct mapping from the parameters provided to :any:`Job` to the launch command.

        Parameters
        ----------
        job : :any:`Job`
            The job description specifying required hardware resources

        Returns
        -------
        list
            A list of strings with the rendered job options
        """
        options = []
        for attr, option in self.job_options_map.items():
            value = job.get(attr, None)

            if value is not None:
                options += [option.format(value)]
        return options


class SrunLauncher(Launcher):
    """
    :any:`Launcher` implementation for Slurm's srun
    """

    job_options_map = {
        'nodes': '--nodes={}',
        'tasks': '--ntasks={}',
        'tasks_per_node': '--ntasks-per-node={}',
        'tasks_per_socket': '--ntasks-per-socket={}',
        'cpus_per_task': '--cpus-per-task={}',
        'threads_per_core': '--ntasks-per-core={}',
        'gpus_per_task': '--gpus-per-task={}',
        'account': '--acount={}',
        'partition': '--partition={}',
    }

    bind_options_map = {
        CpuBinding.BIND_NONE: ['--cpu-bind=none'],
        CpuBinding.BIND_SOCKETS: ['--cpu-bind=sockets'],
        CpuBinding.BIND_CORES: ['--cpu-bind=cores'],
        CpuBinding.BIND_THREADS: ['--cpu-bind=threads'],
        CpuBinding.BIND_USER: [],
    }

    distribution_options_map = {
        CpuDistribution.DISTRIBUTE_DEFAULT: '*',
        CpuDistribution.DISTRIBUTE_BLOCK: 'block',
        CpuDistribution.DISTRIBUTE_CYCLIC: 'cyclic',
    }

    def get_distribution_options(self, job):
        """Return options for task distribution"""
        if (job.get('distribute_remote', None) is None) and (job.get('distribute_local', None) is None):
            return []

        distribute_remote = job.get('distribute_remote', CpuDistribution.DISTRIBUTE_DEFAULT)
        distribute_local = job.get('distribute_local', CpuDistribution.DISTRIBUTE_DEFAULT)

        if distribute_remote is CpuDistribution.DISTRIBUTE_USER:
            debug(('Not applying task distribution options because remote distribution'
                   ' of tasks is set to use user-provided settings'))
            return []
        if distribute_local is CpuDistribution.DISTRIBUTE_USER:
            debug(('Not applying task distribution options because local distribution'
                   ' of tasks is set to use user-provided settings'))
            return []

        return [(f'--distribution={self.distribution_options_map[distribute_remote]}'
                 f':{self.distribution_options_map[distribute_local]}')]


    def get_command(self, run_dir, cmd, job, env=None, custom_flags=None, **kwargs):
        launch_cmd = ['srun'] + self.get_options_from_job(job)

        if job.get('bind', None):
            launch_cmd += list(self.bind_options_map[job.get('bind', None)])

        launch_cmd += self.get_distribution_options(job)

        if custom_flags is not None:
            launch_cmd += list(custom_flags)

        launch_cmd += ['--'] + cmd

        return launch_cmd

class MpirunLauncher(Launcher):
    """
    :any:`Launcher` implementation for a standard mpirun
    """

    job_options_map = {
        'tasks': '-np {}',
        'tasks_per_node': '-npernode {}',
        'tasks_per_socket': '-npersocket {}',
        'cpus_per_task': '-cpus-per-proc {}',
    }

    bind_options_map = {
        CpuBinding.BIND_NONE: ['--bind-to none'],
        CpuBinding.BIND_SOCKETS: ['--bind-to socket'],
        CpuBinding.BIND_CORES: ['--bind-to core'],
        CpuBinding.BIND_THREADS: ['--bind-to hwthread'],
        CpuBinding.BIND_USER: [],
    }

    distribution_options_map = {
        CpuDistribution.DISTRIBUTE_BLOCK: 'core',
        CpuDistribution.DISTRIBUTE_CYCLIC: 'numa',
    }

    def get_distribution_options(self, job):
        """Return options for task distribution"""
        do_nothing = [CpuDistribution.DISTRIBUTE_DEFAULT, CpuDistribution.DISTRIBUTE_USER]
        if hasattr(job, 'distribute_remote') and job.distribute_remote not in do_nothing:
            warning('Specified remote distribution option ignored in MpirunLauncher')

        if not hasattr(job, 'distribute_local') or job.distribute_local in do_nothing:
            return []

        return [f'--map-by {self.distribution_options_map[job.distribute_local]}']

    def get_command(self, run_dir, cmd, job, env=None, custom_flags=None, **kwargs):
        """
        Return the mpirun command for the provided :data:`job` specification
        """

        launch_cmd = ['mpirun'] + self.get_options_from_job(job)

        if job.get('bind', None):
            launch_cmd += list(self.bind_options_map[job.get('bind', None)])

        launch_cmd += self.get_distribution_options(job)

        if custom_flags is not None:
            launch_cmd += list(custom_flags)

        launch_cmd += ['--'] + cmd

        return launch_cmd

class BashLauncher(Launcher):

    def __init__(self, path, launcher):
        self._path = path
        self._launcher = launcher

    def pre_launch(self, run_dir, cmd, job, env=None, custom_flags=None, **kwargs):
        self._launcher.pre_launch(run_dir, cmd, job, env, **kwargs)

        script_dir = run_dir/self._path

        if script_dir.exists() and script_dir.is_file():
            script_dir.unlink()

        script_dir.mkdir(exist_ok=True, parents=True)

        current_datetime = datetime.datetime.now()
        timestamp = current_datetime.strftime('%Y-%m-%d.%H:%M:%S.%f')

        path = script_dir/f"run-{timestamp}.sh"

        if env is None:
            env = {}

        with path.open('w') as f:
            f.write('#! /bin/bash')
            f.write("\n")

            for key, value in env.items():
                f.write(f"export ${{key}}={value}\n")

            f.write("\n")

            f.write(' '.join(self._launcher.get_command(run_dir, cmd, job, env, **kwargs)))

        return {'script_path': path.resolve()}


    def post_launch(self, run_dir, cmd, job, env=None, custom_flags=None, **kwargs):
        self._launcher.post_launch(run_dir, cmd, job, env, **kwargs)

    def get_command(self, run_dir, cmd, job, env=None, custom_flags=None, **kwargs):
        script_path = kwargs.get('script_path')
        return ['/bin/bash', '-c', str(script_path)]