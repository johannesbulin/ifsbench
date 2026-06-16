.. (C) Copyright 2020- ECMWF.
.. This software is licensed under the terms of the Apache Licence Version 2.0
.. which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
.. In applying this licence, ECMWF does not waive the privileges and immunities
.. granted to it by virtue of its status as an intergovernmental organisation
.. nor does it submit to any jurisdiction.

.. _ifsbench.data:

==================
Data Handling
==================

Overview
--------

The ``ifsbench.data`` module provides a flexible pipeline architecture for managing data preparation and 
processing tasks. It allows you to compose multiple data handling operations sequentially to prepare 
benchmark environments with the necessary input files, configurations, and resources.

Core Concept
~~~~~~~~~~~~

The data handling system is based on the :class:`DataHandler` base class, which defines the interface 
for individual data processing steps. Each handler implements the ``execute`` method to perform a specific 
data operation within a working directory. Multiple handlers can be chained together to create a complete 
data preparation pipeline.

Available Handlers
------------------

DataHandler (Base Class)
~~~~~~~~~~~~~~~~~~~~~~~~~

The :class:`DataHandler` is the abstract base class for all data pipeline steps. It provides the interface 
that all concrete handlers implement.

FetchHandler
~~~~~~~~~~~~

The :class:`FetchHandler` downloads files from remote URLs. It supports:

* Downloading files to a specified local path
* Conditional downloading (can skip if file already exists)
* Optional error handling (continue or fail on download failures)
* HTTP and HTTPS protocols

Use cases:

* Download benchmark input datasets from remote servers
* Fetch configuration files or executables
* Retrieve model data or initial conditions

ExtractHandler
~~~~~~~~~~~~~~

The :class:`ExtractHandler` extracts archive files (tar.gz, zip, etc.) to specified directories. It supports:

* Automatic detection of archive format
* Optional target directory specification
* In-place extraction or extraction to custom locations

Use cases:

* Extract downloaded datasets
* Unpack pre-configured benchmark environments
* Prepare large data files stored in compressed form

RenameHandler
~~~~~~~~~~~~~~

The :class:`RenameHandler` reorganizes files using regular expression pattern matching. It supports:

* **Copy**: Duplicate files from source to target locations
* **Symlink**: Create symbolic links
* **Move**: Relocate files

The handler uses :func:`re.sub` for pattern matching, allowing flexible file organization:

* Rename files based on patterns
* Organize files into directory structures
* Create symbolic links for convenient access

Use cases:

* Organize downloaded files into benchmark directory structures
* Create convenient symbolic links to input datasets
* Apply naming conventions to benchmark files

NamelistHandler
~~~~~~~~~~~~~~~~

The :class:`NamelistHandler` manages Fortran namelists (used extensively in IFS). It can:

* Parse and modify namelists for different benchmark scenarios
* Apply parameter overrides
* Support complex namelist operations

Use cases:

* Configure model parameters for different benchmark scenarios
* Override default settings for specific test cases
* Manage multiple benchmark configurations

NamelistSanitiseHandler
~~~~~~~~~~~~~~~~~~~~~~~

The :class:`NamelistSanitiseHandler` validates and cleans namelists. It ensures:

* Namelists conform to expected formats
* Invalid entries are handled appropriately
* Configurations are ready for execution

Use cases:

* Validate user-provided configurations
* Clean up namelists after modifications
* Ensure compatibility with model versions

Building Data Pipelines
------------------------

Creating a data pipeline involves instantiating handlers and executing them sequentially:

.. code-block:: python

    from ifsbench.data import FetchHandler, ExtractHandler, RenameHandler
    from pathlib import Path

    # Create handlers
    fetch = FetchHandler(
        source_url="https://example.com/data.tar.gz",
        target_path=Path("data.tar.gz")
    )
    
    extract = ExtractHandler(
        archive_path=Path("data.tar.gz"),
        target_dir=Path("data")
    )
    
    rename = RenameHandler(
        pattern=r"input_(\w+)",
        repl=r"benchmark_\1"
    )

    # Execute in sequence
    work_dir = Path("/path/to/benchmark")
    fetch.execute(work_dir)
    extract.execute(work_dir)
    rename.execute(work_dir)

The handlers are also serializable, allowing pipelines to be saved as configuration files 
(JSON, YAML, etc.) and loaded for reuse across multiple benchmark runs.

Serialization
~~~~~~~~~~~~~

All data handlers inherit from :class:`SubclassableSerialisationMixin`, enabling:

* Serialization to JSON/YAML formats
* Deserialization from configuration files
* Portability of benchmark configurations

This makes it easy to version control and reproduce data preparation steps across different environments.

Error Handling
--------------

Most handlers provide graceful error handling:

* **FetchHandler**: Optional ``ignore_errors`` flag to continue on download failures
* **RenameHandler**: Handles missing source files appropriately
* **ExtractHandler**: Validates archive integrity before extraction

Path Resolution
---------------

The data handling system supports both relative and absolute paths:

* **Relative paths**: Resolved relative to the working directory passed to ``execute()``
* **Absolute paths**: Used as-is, unchanged

This flexibility allows handlers to work in different directory contexts while maintaining 
portable pipeline definitions.

API Reference
--------------

For complete API documentation, see :ref:`ifsbench.data in the API reference <ifsbench.data>`.
