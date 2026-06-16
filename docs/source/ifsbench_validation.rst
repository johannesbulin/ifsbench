.. (C) Copyright 2020- ECMWF.
.. This software is licensed under the terms of the Apache Licence Version 2.0
.. which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
.. In applying this licence, ECMWF does not waive the privileges and immunities
.. granted to it by virtue of its status as an intergovernmental organisation
.. nor does it submit to any jurisdiction.

.. _ifsbench.validation:

====================
Results Validation
====================

Overview
--------

The ``ifsbench.validation`` module provides utilities for comparing and validating benchmark results. 
It enables near-equality comparisons between pandas DataFrames using configurable tolerances, as well as 
frame utility functions for data extraction and filtering.

Core Concept
~~~~~~~~~~~~

Result validation is essential for:

* Comparing benchmark results across different runs
* Detecting performance regressions or improvements
* Validating numerical correctness within acceptable tolerances
* Building test suites for benchmark reproducibility

The module provides tools for both detailed frame manipulation and high-level comparison operations.

Key Classes and Functions
--------------------------

FrameCloseValidation
~~~~~~~~~~~~~~~~~~~~~

The :class:`FrameCloseValidation` dataclass compares pandas DataFrames for near-equality:

.. code-block:: python

    from ifsbench.validation import FrameCloseValidation
    import pandas as pd
    
    validator = FrameCloseValidation(atol=1e-10, rtol=1e-5)
    
    frame1 = pd.DataFrame({'value': [1.0, 2.0, 3.0]})
    frame2 = pd.DataFrame({'value': [1.0000001, 2.0, 3.0000001]})
    
    is_close, mismatches = validator.compare(frame1, frame2)

Features:

* **Absolute Tolerance (atol)**: Acceptable absolute difference between values
* **Relative Tolerance (rtol)**: Acceptable relative difference (as fraction)
* **Type Handling**: Automatically strips non-float columns before comparison
* **Detailed Reporting**: Returns specific mismatches for debugging

How It Works
~~~~~~~~~~~~

The comparison process:

1. Extract only float columns from both DataFrames (ignores integer and string columns)
2. Apply numpy.isclose with specified tolerances:
   
   .. code-block:: python
   
       numpy.isclose(a, b, rtol=rtol, atol=atol)

3. Aggregate results per row
4. Collect any rows where values don't match
5. Return boolean (all close?) and list of mismatches

Tolerance Guidelines
~~~~~~~~~~~~~~~~~~~~

**Absolute Tolerance (atol)**
  Use when comparing values that could be zero or near-zero:
  
  * 1e-15: Very strict (floating-point precision limit)
  * 1e-10: Strict (appropriate for double precision)
  * 1e-5: Moderate (for lossy formats or operations)

**Relative Tolerance (rtol)**
  Use when comparing values across different scales:
  
  * 1e-15: Very strict (identical results)
  * 1e-10: Strict (appropriate for reproducible computations)
  * 1e-5: Moderate (reasonable for different systems/compilers)
  * 0.01: Permissive (1% difference)

Frame Utility Functions
-----------------------

Frame Type Extraction
~~~~~~~~~~~~~~~~~~~~~

The module provides utility functions to extract specific column types:

**get_float_columns(frame)**
  Extract a sub-DataFrame containing only float columns:

  .. code-block:: python

      from ifsbench.validation import get_float_columns
      import pandas as pd
      
      frame = pd.DataFrame({
          'value': [1.0, 2.5, 3.1],
          'count': [10, 20, 30],
          'name': ['A', 'B', 'C']
      })
      
      float_frame = get_float_columns(frame)
      # Returns DataFrame with only 'value' column

**get_int_columns(frame)**
  Extract a sub-DataFrame containing only integer columns:

  .. code-block:: python

      from ifsbench.validation import get_int_columns
      
      int_frame = get_int_columns(frame)
      # Returns DataFrame with only 'count' column

Use Cases
~~~~~~~~~

Type-specific extraction is useful for:

* Separating numerical from categorical data
* Comparing only certain types of values
* Preprocessing data for specific analysis
* Handling mixed-type DataFrames

Typical Validation Workflow
---------------------------

Comparing Benchmark Results
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from ifsbench.validation import FrameCloseValidation
    from pathlib import Path
    import pandas as pd
    
    # Load reference and current results
    reference = pd.read_csv('reference_results.csv')
    current = pd.read_csv('benchmark_results.csv')
    
    # Set up validator
    validator = FrameCloseValidation(atol=1e-10, rtol=1e-5)
    
    # Compare
    is_close, mismatches = validator.compare(reference, current)
    
    if is_close:
        print("✓ Results match within tolerance")
    else:
        print(f"✗ {len(mismatches)} mismatches found:")
        for idx, (val1, val2) in mismatches[:5]:
            print(f"  Row {idx}: {val1} vs {val2}")

Validating Ensemble Statistics
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from ifsbench.results import EnsembleStats
    from ifsbench.validation import FrameCloseValidation
    
    # Calculate statistics from current runs
    ensemble = EnsembleStats(frames=[run1, run2, run3])
    current_stats = ensemble.calc_stats(['mean', 'std'])
    
    # Compare against reference
    validator = FrameCloseValidation(atol=1e-10, rtol=0.01)  # 1% tolerance
    
    is_close, mismatches = validator.compare(
        reference_stats['mean'],
        current_stats['mean']
    )

Multiple Frame Comparison
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from ifsbench.validation import FrameCloseValidation
    
    validator = FrameCloseValidation(atol=1e-10, rtol=1e-5)
    
    results = {}
    for key in ['timing', 'memory', 'flops']:
        is_close, mismatches = validator.compare(reference[key], current[key])
        results[key] = {
            'passed': is_close,
            'mismatches': len(mismatches)
        }
    
    if all(r['passed'] for r in results.values()):
        print("All validations passed!")

Building Test Suites
---------------------

Using validation in automated tests:

.. code-block:: python

    import pytest
    from ifsbench.validation import FrameCloseValidation
    
    @pytest.mark.parametrize("test_case", TEST_CASES)
    def test_benchmark_consistency(test_case):
        """Test that benchmark results are reproducible"""
        current = run_benchmark(test_case)
        reference = load_reference(test_case)
        
        validator = FrameCloseValidation(atol=1e-10, rtol=1e-5)
        is_close, mismatches = validator.compare(reference, current)
        
        assert is_close, f"Benchmark results differ: {len(mismatches)} mismatches"

Tolerance Configuration
-----------------------

Recommended Tolerances by Scenario
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Identical Builds on Same Machine**
  ``atol=0, rtol=1e-14``
  
  Expect bit-identical results

**Same Build, Different Runs**
  ``atol=1e-14, rtol=1e-10``
  
  Floating-point variability between runs

**Different Compilers or Optimization Levels**
  ``atol=1e-10, rtol=1e-6``
  
  More significant differences expected

**Different Architectures**
  ``atol=1e-8, rtol=1e-4``
  
  Different hardware and precision

**Different Implementations**
  ``atol=1e-5, rtol=0.01``
  
  Algorithmic variations allowed

Performance Considerations
--------------------------

* **Memory**: Comparisons work on in-memory DataFrames
* **Speed**: Vectorized operations using numpy for efficiency
* **Scalability**: Can handle large DataFrames with thousands of rows

For very large datasets, consider:

* Comparing subsets of data
* Using sampling for initial validation
* Chunking data into manageable pieces

Integration with Other Modules
------------------------------

Validation integrates with:

* **ifsbench.results**: Validates :class:`ResultData` and :class:`ResultInfo`
* **ifsbench.benchmark**: Validates benchmark run results
* **Test Suites**: Build reproducibility tests using validation

Best Practices
--------------

1. **Document Tolerances**: Clearly specify why you chose specific tolerances
2. **Use Appropriate Types**: Choose atol vs rtol based on value scales
3. **Fail Informatively**: Report detailed mismatch information for debugging
4. **Automate Testing**: Use validation in CI/CD pipelines
5. **Track History**: Monitor tolerances as code evolves

API Reference
--------------

For complete API documentation, see :ref:`ifsbench.validation in the API reference <ifsbench.validation>`.
