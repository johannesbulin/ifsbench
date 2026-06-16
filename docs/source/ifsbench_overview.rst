.. (C) Copyright 2020- ECMWF.
.. This software is licensed under the terms of the Apache Licence Version 2.0
.. which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
.. In applying this licence, ECMWF does not waive the privileges and immunities
.. granted to it by virtue of its status as an intergovernmental organisation
.. nor does it submit to any jurisdiction.

===============
IFSBench Guide
===============

Overview
--------

IFSBench is a Python-based tool for testing and performance benchmarking of IFS (Integrated Forecasting System) 
development workflows. It provides a lightweight, pythonic framework for creating and managing benchmark scripts 
with improved command-line interfaces and data processing capabilities.

Key Features
~~~~~~~~~~~~

* **Configurable Benchmarking**: Create customizable benchmark scripts with an improved CLI for different test scenarios.

* **Data Management**: Efficiently handle benchmark data through downloading, extracting, and organizing input files 
  from predefined locations without requiring git-lfs or cmake-based symlinking.

* **Performance Profiling**: Parse DrHook profiles into accessible formats for performance analysis.

* **Reference Benchmarking**: Store reference benchmark results as pandas DataFrames in lightweight formats (e.g., .csv) 
  for version control without requiring complete log files.

* **Large-scale Benchmarks**: Support for large benchmark setups (e.g., tl159-fc, tco399-fc) with flexible data handling.

Core Modules
~~~~~~~~~~~~

The package is organized into several key modules:

* :doc:`ifsbench_data` - Comprehensive data pipeline management for benchmark setup
* :doc:`ifsbench_launch` - Execution of benchmark commands with various MPI launchers
* :doc:`ifsbench_api` - Complete API reference documentation

Getting Started
---------------

The typical workflow with IFSBench involves:

1. **Prepare Data**: Use data handlers to fetch, extract, and organize input files for your benchmarks.
2. **Configure Execution**: Set up launch configurations for your computational environment.
3. **Run Benchmarks**: Execute your benchmark suite with the configured data and launch parameters.
4. **Analyze Results**: Process and compare results using the built-in utilities.

For detailed information about data handling, see the :doc:`ifsbench_data` guide.

For detailed information about launching executables, see the :doc:`ifsbench_launch` guide.
