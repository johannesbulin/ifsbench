.. (C) Copyright 2020- ECMWF.
.. This software is licensed under the terms of the Apache Licence Version 2.0
.. which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
.. In applying this licence, ECMWF does not waive the privileges and immunities
.. granted to it by virtue of its status as an intergovernmental organisation
.. nor does it submit to any jurisdiction.

.. _ifsbench.results:

=====================
Results Processing
=====================

Overview
--------

The ``ifsbench.results`` module provides utilities for handling benchmark results, including storage, 
formatting, and statistical analysis of benchmark output data. It leverages pandas DataFrames for flexible 
result management and supports ensemble statistics across multiple benchmark runs.

Core Concept
~~~~~~~~~~~~

Results in IFSBench are primarily stored as pandas DataFrames, which enables:

* Flexible data organization and querying
* Integration with scientific Python tools
* Statistical analysis and comparison
* Easy serialization to standard formats (CSV, HDF5, etc.)
* Efficient ensemble statistics across multiple runs

Key Classes
-----------

ResultData
~~~~~~~~~~

The :class:`ResultData` class is a generic container for numerical benchmark results:

.. code-block:: python

    @dataclass
    class ResultData:
        """Generic result class that can be serialised and validated"""
        frames: Dict[str, PydanticDataFrame]

The ``frames`` dictionary maps result names (e.g., "timing", "memory") to pandas DataFrames containing 
the actual numerical data.

Features:

* Flexible naming scheme for different result types
* Multiple results can be stored from a single benchmark run
* Serializable to JSON and other formats
* Type validation using Pydantic

ResultInfo
~~~~~~~~~~

The :class:`ResultInfo` class extends :class:`ResultData` with execution metadata:

.. code-block:: python

    @dataclass
    class ResultInfo(ResultData):
        """Generic result class with data and additional information"""
        stdout: Optional[str] = None    # Standard output
        stderr: Optional[str] = None    # Standard error
        walltime: Optional[float] = None  # Execution time in seconds

This class captures the complete execution information alongside numerical results.

EnsembleStats
~~~~~~~~~~~~~~

The :class:`EnsembleStats` class handles statistical analysis across multiple benchmark runs:

* **Input**: List of pandas DataFrames (one per ensemble member)
* **Grouping**: Automatically groups results by index
* **Statistics**: Calculates mean, median, min, max, std, sum, and percentiles
* **Output**: Dictionary of DataFrames with statistical results

Features:

* Supports percentiles (e.g., 'P10', 'p85') in addition to basic statistics
* Flexible statistics specification (single string or list)
* Case-insensitive percentile names
* Handles missing values and NaN appropriately

Available Statistics
~~~~~~~~~~~~~~~~~~~~

Basic statistics (from :const:`AVAILABLE_BASIC_STATS`):

* **min**: Minimum value
* **max**: Maximum value
* **mean**: Arithmetic mean
* **median**: Median value
* **sum**: Sum of all values
* **std**: Population standard deviation (ddof=0)

Percentiles:

* Specify as 'P##' or 'p##' (e.g., 'P10', 'p85', 'P50')
* Range: 0 to 100
* Examples: 'P25', 'P75', 'p95'

Example Usage
~~~~~~~~~~~~~

.. code-block:: python

    from ifsbench.results import EnsembleStats
    import pandas as pd

    # Create DataFrames for ensemble members
    member1 = pd.DataFrame({'time': [1.0, 1.1, 0.9], 'memory': [100, 110, 95]})
    member2 = pd.DataFrame({'time': [1.05, 1.15, 0.95], 'memory': [105, 115, 100]})
    member3 = pd.DataFrame({'time': [0.95, 1.05, 0.85], 'memory': [95, 105, 90]})

    # Create ensemble statistics
    ensemble = EnsembleStats(frames=[member1, member2, member3])

    # Calculate multiple statistics
    stats = ensemble.calc_stats(['mean', 'std', 'P25', 'P75'])
    
    # Access results
    mean_times = stats['mean']
    std_times = stats['std']
    p25_times = stats['P25']

Workflow for Result Processing
-------------------------------

1. **Run Benchmarks**: Execute benchmarks and collect output
2. **Parse Results**: Extract numerical data into pandas DataFrames
3. **Store Results**: Create :class:`ResultInfo` objects with data and metadata
4. **Multiple Runs**: Repeat steps 1-3 for ensemble or parameter sweep
5. **Statistical Analysis**: Use :class:`EnsembleStats` to compute aggregate statistics
6. **Export Results**: Save DataFrames to CSV, HDF5, or other formats
7. **Compare**: Use statistical results for performance analysis and comparison

Result Storage and Format
-------------------------

Results can be stored in various formats:

* **JSON**: Default serialization format (human-readable)
* **HDF5**: Efficient binary format for large datasets
* **CSV**: For easy inspection and sharing
* **YAML**: Human-readable alternative to JSON

Integration with Benchmark Module
----------------------------------

The :class:`BenchmarkSummary` from ``ifsbench.benchmark`` captures basic result information, 
while :class:`ResultInfo` from this module can store more detailed numerical results alongside it.

Best Practices
--------------

1. **Organize Results**: Use meaningful keys in the frames dictionary ("timing", "energy", etc.)
2. **Include Metadata**: Always store stdout, stderr, and walltime for debugging
3. **Ensemble Size**: Use sufficient ensemble members for stable statistics
4. **Tolerance Values**: Document tolerances when comparing results
5. **Version Control**: Store result definitions and tolerances in configuration files

Comparison and Validation
--------------------------

Results can be compared using the :mod:`ifsbench.validation` module:

* :class:`FrameCloseValidation` for near-equality checks
* Custom comparison tolerances (absolute and relative)
* Detailed mismatch reporting

API Reference
--------------

For complete API documentation, see :ref:`ifsbench.results in the API reference <ifsbench.results>`.
