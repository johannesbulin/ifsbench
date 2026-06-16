.. (C) Copyright 2020- ECMWF.
.. This software is licensed under the terms of the Apache Licence Version 2.0
.. which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
.. In applying this licence, ECMWF does not waive the privileges and immunities
.. granted to it by virtue of its status as an intergovernmental organisation
.. nor does it submit to any jurisdiction.

.. _ifsbench.launch:

=================
Launch Handling
=================

Overview
--------

The ``ifsbench.launch`` module provides a flexible framework for launching executables with various MPI 
job schedulers and launchers. It abstracts the details of different job scheduling systems (SLURM, OpenMPI, etc.) 
into a unified interface, making it easy to run benchmarks across different HPC environments.

Core Concept
~~~~~~~~~~~~

The launch system is built around two main components:

* :class:`LaunchData` - A dataclass that encapsulates all information needed to launch a command
* :class:`Launcher` - An abstract base class for environment-specific launcher implementations

This design allows benchmark scripts to define launch requirements once and execute them on different systems 
by simply selecting the appropriate launcher.

LaunchData
----------

The :class:`LaunchData` dataclass contains all the information necessary to execute a command:

* **run_dir**: The working directory where the command will be executed
* **cmd**: The command to execute (as a list of strings)
* **env**: A dictionary of environment variables to set

Example:

.. code-block:: python

    from pathlib import Path
    from ifsbench.launch import LaunchData

    launch_data = LaunchData(
        run_dir=Path("/work/benchmark"),
        cmd=["./ifs", "config.nml"],
        env={"OMP_NUM_THREADS": "4", "MALLOC_TRIM_THRESHOLD": "-1"}
    )

    result = launch_data.launch()

The :meth:`launch` method executes the command with the specified environment variables in the 
given working directory and returns an :class:`ExecuteResult` containing the exit code and output.

Launcher Classes
----------------

The :class:`Launcher` base class defines the interface that all specific launchers implement. 
Concrete launcher implementations handle environment-specific launch logic.

MpirunLauncher
~~~~~~~~~~~~~~

The :class:`MpirunLauncher` launches commands using the OpenMPI ``mpirun`` launcher. It allows you to:

* Specify the number of MPI processes to launch
* Configure process and thread binding
* Set up per-process environment variables
* Control MPI-specific settings

Use cases:

* Execute MPI-parallelized IFS benchmarks
* Run on systems with OpenMPI installed
* Fine-tune MPI process placement and binding

Configuration options include:

* Process count and per-process thread count
* Binding strategies (socket, core, etc.)
* Environment variable overrides

SrunLauncher
~~~~~~~~~~~~

The :class:`SrunLauncher` launches commands using the SLURM ``srun`` launcher. It integrates with 
SLURM job scheduling systems to:

* Launch tasks within SLURM job allocations
* Specify process and thread layout
* Manage resource constraints
* Optimize process placement

Use cases:

* Execute benchmarks on SLURM-managed HPC clusters
* Launch multi-node MPI jobs
* Control resource allocation per task

Configuration options include:

* Number of tasks and CPUs per task
* Memory per task
* Process affinity and binding
* OpenMP and MPI settings

Launcher Base Class
~~~~~~~~~~~~~~~~~~~

The :class:`Launcher` is the abstract base class for all launcher implementations. It provides:

* A standard interface for launching commands
* Serialization support for launcher configurations
* Environment and command manipulation capabilities

Custom Launcher Implementation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To implement a custom launcher for a specific scheduling system:

.. code-block:: python

    from ifsbench.launch import Launcher
    from pathlib import Path
    from typing import List

    class CustomLauncher(Launcher):
        """Custom launcher for specific scheduling system"""
        
        def launch(self, launch_data: LaunchData) -> ExecuteResult:
            # Prepare command with system-specific wrapper
            cmd = ["custom_exec"] + launch_data.cmd
            # Execute and return result
            ...

Typical Workflow
----------------

1. **Create LaunchData**: Define the command, working directory, and environment
2. **Select Launcher**: Choose the appropriate launcher for your HPC environment
3. **Execute**: Run the command through the launcher
4. **Process Results**: Analyze the execution results

Example workflow:

.. code-block:: python

    from pathlib import Path
    from ifsbench.launch import SrunLauncher, LaunchData
    from ifsbench.env import EnvPipeline

    # Create launch data
    launch_data = LaunchData(
        run_dir=Path("/work/benchmark"),
        cmd=["./ifs", "model.nml"],
        env={
            "OMP_NUM_THREADS": "2",
            "MALLOC_TRIM_THRESHOLD": "-1"
        }
    )

    # Create launcher
    launcher = SrunLauncher(ntasks=64, cpus_per_task=2)

    # Execute
    result = launcher.launch(launch_data)
    print(f"Exit code: {result.returncode}")
    print(f"Output:\n{result.stdout}")

Environment Management
----------------------

Launchers integrate with the :class:`EnvPipeline` (from ``ifsbench.env``) for advanced 
environment variable management:

* Pre-configured environment templates
* Environment variable composition
* System-specific settings

Serialization
~~~~~~~~~~~~~~

All launchers support serialization, allowing launcher configurations to be:

* Saved in JSON or YAML format
* Version-controlled in benchmark repositories
* Reused across multiple benchmark runs
* Shared between team members

This enables reproducible benchmark configurations across different HPC systems.

Job Integration
~~~~~~~~~~~~~~~

Launchers work seamlessly with the :class:`Job` class (from ``ifsbench.job``) to:

* Track job execution and status
* Capture performance metrics
* Log execution details
* Manage job lifecycle

Error Handling
--------------

The launch system provides robust error handling:

* Command execution failures are captured in :class:`ExecuteResult`
* Invalid launcher configurations are detected early
* Environment variables are validated before execution
* Working directory existence is verified

API Reference
--------------

For complete API documentation, see :ref:`ifsbench.launch in the API reference <ifsbench.launch>`.
