.. (C) Copyright 2020- ECMWF.
.. This software is licensed under the terms of the Apache Licence Version 2.0
.. which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
.. In applying this licence, ECMWF does not waive the privileges and immunities
.. granted to it by virtue of its status as an intergovernmental organisation
.. nor does it submit to any jurisdiction.

.. _ifsbench.arch:

=====================
Architecture Support
=====================

Overview
--------

The ``ifsbench.arch`` module provides abstractions for describing different computational architectures 
and systems. It allows benchmarks to be configured appropriately for different HPC environments, handling 
system-specific details like CPU configurations, default job launchers, and environment variables.

Core Concept
~~~~~~~~~~~~

An architecture (or system) in IFSBench encapsulates:

* Hardware configuration (CPU counts, GPU availability, memory)
* Available job launchers (SLURM, OpenMPI, PBS, etc.)
* System-specific environment settings
* Optimization hints for the target system

This abstraction allows benchmark definitions to be portable across different HPC systems while adapting 
to local requirements.

Key Classes
-----------

Arch (Abstract Base Class)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :class:`Arch` base class defines the interface for architecture implementations. It provides three 
key methods:

**get_default_launcher()**
  Returns the launcher that is typically used on this system (SLURM, PBS, MPI, etc.)

**get_cpu_configuration()**
  Returns a :class:`CpuConfiguration` object describing the system's CPU topology and capabilities

**process_job(job)**
  Processes a job specification and returns an :class:`ArchResult` with architecture-specific adjustments

Architecture-Specific Processing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :meth:`process_job` method is where system-specific logic is applied:

* Adjust resource allocation based on hardware capabilities
* Add architecture-specific environment variables
* Configure launcher flags for optimal performance
* Optimize job parameters for the target system

It returns an :class:`ArchResult` containing:

* Updated :class:`Job` object with adjusted parameters
* Additional :class:`EnvHandler` objects for environment setup
* Default launcher configuration and flags

ArchResult
~~~~~~~~~~

The :class:`ArchResult` dataclass combines all architecture-specific information for a job:

.. code-block:: python

    @dataclass
    class ArchResult:
        job: Job                              # Updated job with arch adjustments
        env_handlers: List[EnvHandler] = []   # Architecture-specific environment handlers
        default_launcher: Launcher = None     # Default launcher for this architecture
        default_launcher_flags: List[str] = []  # Launcher-specific flags

DefaultArch
~~~~~~~~~~~

The :class:`DefaultArch` class is a concrete implementation suitable for generic systems:

* Accepts a :class:`Launcher` for the default job launcher
* Accepts a :class:`CpuConfiguration` for the hardware setup
* Provides basic architecture processing without system-specific optimizations

Use cases:

* Generic development systems
* Systems without specialized optimizations
* Testing and prototyping
* Fallback when specific architecture support is unavailable

Example:

.. code-block:: python

    from ifsbench.arch import DefaultArch
    from ifsbench.launch import SrunLauncher
    from ifsbench.job import CpuConfiguration

    arch = DefaultArch(
        launcher=SrunLauncher(ntasks=128, cpus_per_task=2),
        cpu_config=CpuConfiguration(cpus_per_node=64)
    )

System-Specific Architectures
------------------------------

While only :class:`DefaultArch` is included in the base package, custom architecture implementations 
can be created for specific systems:

* **ECMWF Systems**: Optimized configurations for ECMWF HPC clusters
* **HPC Centers**: Custom support for specific supercomputers
* **Cloud Environments**: Configurations for AWS, GCP, or Azure deployments
* **Local Systems**: Development machine configurations

Creating Custom Architectures
------------------------------

To create a custom architecture implementation:

.. code-block:: python

    from ifsbench.arch import Arch, ArchResult
    from ifsbench.job import Job, CpuConfiguration
    from ifsbench.launch import Launcher

    class CustomArch(Arch):
        """Custom architecture for specific HPC system"""
        
        def __init__(self, system_name: str):
            self.system_name = system_name
            
        def get_default_launcher(self) -> Launcher:
            # Return appropriate launcher for this system
            if self.system_name == "slurm_cluster":
                return SrunLauncher(...)
            else:
                return MpirunLauncher(...)
        
        def get_cpu_configuration(self) -> CpuConfiguration:
            # Return hardware configuration
            return CpuConfiguration(cpus_per_node=64, gpus_per_node=4)
        
        def process_job(self, job: Job, **kwargs) -> ArchResult:
            # Apply system-specific optimizations
            updated_job = job.copy()
            updated_job.cpus = min(job.cpus, 64)  # Cap at max CPUs
            
            return ArchResult(
                job=updated_job,
                env_handlers=[...],
                default_launcher=self.get_default_launcher(),
                default_launcher_flags=["-m", "cyclic"]
            )

Integration with Job Configuration
-----------------------------------

The architecture module works closely with the :class:`Job` class to:

* Validate job parameters against system capabilities
* Adjust resource allocation for optimal performance
* Apply system-specific optimizations
* Ensure jobs conform to system policies and limits

Typical Workflow
----------------

1. **System Setup**: Create an :class:`Arch` instance for the target system
2. **Job Definition**: Define a :class:`Job` with desired resources
3. **Architecture Processing**: Call :meth:`process_job` to adapt the job
4. **Launcher Selection**: Get the default launcher from :meth:`get_default_launcher`
5. **Execution**: Use the launcher to execute the optimized job

Example:

.. code-block:: python

    from ifsbench.arch import DefaultArch
    from ifsbench.job import Job, CpuConfiguration

    # Set up architecture
    arch = DefaultArch(
        launcher=SrunLauncher(ntasks=128, cpus_per_task=2),
        cpu_config=CpuConfiguration(cpus_per_node=64)
    )

    # Define a job
    job = Job(cpus=128, memory=256)

    # Process for this architecture
    result = arch.process_job(job)
    
    # Use the optimized job and launcher
    launcher = result.default_launcher
    optimized_job = result.job

Serialization
~~~~~~~~~~~~~

Architecture configurations can be serialized to JSON or YAML for:

* Version control of system configurations
* Sharing configurations across teams
* Reproducible benchmark runs
* Configuration management

API Reference
--------------

For complete API documentation, see :ref:`ifsbench.arch in the API reference <ifsbench.arch>`.
