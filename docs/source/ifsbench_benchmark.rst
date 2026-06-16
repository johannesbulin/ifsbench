.. (C) Copyright 2020- ECMWF.
.. This software is licensed under the terms of the Apache Licence Version 2.0
.. which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
.. In applying this licence, ECMWF does not waive the privileges and immunities
.. granted to it by virtue of its status as an intergovernmental organisation
.. nor does it submit to any jurisdiction.

.. _ifsbench.benchmark:

====================
Benchmark Framework
====================

Overview
--------

The ``ifsbench.benchmark`` module provides a comprehensive framework for defining, managing, and executing 
benchmarks. It separates the scientific aspects of a benchmark (what and how something is benchmarked) from 
the technical implementation details (optimization flags, debug settings, etc.).

Core Concept
~~~~~~~~~~~~

The benchmark system is built on the principle of composability, allowing benchmarks to be configured from 
reusable components. This enables complex benchmark scenarios to be built from simple, well-defined pieces.

Key Classes
-----------

ScienceSetup
~~~~~~~~~~~~

The :class:`ScienceSetup` class defines the scientific aspects of a benchmark:

* **Application**: The executable or application being benchmarked
* **Data Handlers (Init)**: Data preparation steps run once during setup (fetch, extract, organize files)
* **Data Handlers (Runtime)**: Data preparation steps run before each benchmark execution
* **Environment Handlers**: Environment variable configuration for the benchmark run

This class encapsulates the "what and how" of benchmarking - it describes the benchmark scenario and the 
application being tested without implementation details.

Example:

.. code-block:: python

    from ifsbench.benchmark import ScienceSetup
    from ifsbench.application import Application
    from ifsbench.data import FetchHandler, ExtractHandler

    science_setup = ScienceSetup(
        application=Application(...),
        data_handlers_init=[
            FetchHandler(source_url="http://example.com/data.tar.gz", 
                        target_path="data.tar.gz"),
            ExtractHandler(archive_path="data.tar.gz", target_dir="data")
        ],
        data_handlers_runtime=[...],
        env_handlers=[...]
    )

TechSetup
~~~~~~~~~

The :class:`TechSetup` class defines technical details that don't affect benchmark results:

* **Optional Application Override**: Substitute a different executable (e.g., a debug version)
* **Additional Data Handlers**: Extra data preparation steps specific to this run
* **Additional Environment Handlers**: Performance-tuning environment variables

Use cases:

* Test with debug builds while keeping the same data and configuration
* Add performance-monitoring tools (profilers, tracers)
* Optimize environment variables specific to a particular HPC system
* Enable additional logging or instrumentation

Example:

.. code-block:: python

    from ifsbench.benchmark import TechSetup
    
    tech_setup = TechSetup(
        application=debug_application,  # Debug version instead
        env_handlers=[debug_env_handler],  # Add debugging flags
    )

BenchmarkSummary
~~~~~~~~~~~~~~~~

The :class:`BenchmarkSummary` class captures the results of a benchmark execution:

* **stdout**: Standard output from the benchmark run
* **stderr**: Standard error from the benchmark run
* **walltime**: Execution time in seconds

This provides a concise summary of benchmark execution results.

Benchmark
~~~~~~~~~

The :class:`Benchmark` class ties together the scientific and technical setups. It coordinates:

* Data preparation (both init and runtime handlers)
* Environment setup
* Application execution
* Result collection

The benchmark class handles:

* Sequential execution of data handlers
* Environment variable composition
* Application launch
* Result aggregation and summary

Workflow
~~~~~~~~

A typical benchmark workflow:

1. Define :class:`ScienceSetup` with the application, data handlers, and environment
2. Optionally define :class:`TechSetup` for technical variations
3. Create a :class:`Benchmark` combining both setups
4. Execute the benchmark
5. Retrieve the :class:`BenchmarkSummary` with results

Composition and Reusability
----------------------------

The modular design enables:

* **Benchmark Suites**: Group related benchmarks with different configurations
* **Parameter Sweeps**: Test the same application with different inputs or settings
* **Multi-variant Testing**: Compare results across debug vs. optimized builds
* **Configuration Reuse**: Share common setup components across multiple benchmarks

Best Practices
--------------

1. **Separate Concerns**: Keep scientific setup separate from technical details
2. **Reuse Components**: Define common data handlers and environment handlers once
3. **Version Control**: Store benchmark configurations as serializable JSON/YAML
4. **Document Assumptions**: Include comments about why certain handlers or settings are used
5. **Track Variations**: When creating tech setups, document the specific differences

Integration with Other Modules
------------------------------

The benchmark module integrates with:

* **ifsbench.application**: The executable being benchmarked
* **ifsbench.data**: Data preparation handlers
* **ifsbench.env**: Environment variable management
* **ifsbench.launch**: Execution of the benchmark
* **ifsbench.arch**: Architecture-specific configurations

API Reference
--------------

For complete API documentation, see :ref:`ifsbench.benchmark in the API reference <ifsbench.benchmark>`.
