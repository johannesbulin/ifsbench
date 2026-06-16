.. (C) Copyright 2020- ECMWF.
.. This software is licensed under the terms of the Apache Licence Version 2.0
.. which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
.. In applying this licence, ECMWF does not waive the privileges and immunities
.. granted to it by virtue of its status as an intergovernmental organisation
.. nor does it submit to any jurisdiction.

.. _ifsbench.command_line:

====================
Command Line Tools
====================

Overview
--------

The ``ifsbench.command_line`` module provides a Click-based command-line interface and utilities for 
IFSBench functionality. It includes the main CLI group for building custom benchmark scripts, as well as 
utility commands like namelist comparison.

Core Concept
~~~~~~~~~~~~

The module is built on `Click <https://click.palletsprojects.com/>`_, a Python package for creating 
beautiful command line interfaces. It provides:

* A hierarchical command structure for organizing benchmark commands
* Common options for debugging, logging, and exception handling
* Utilities for benchmark-specific operations (e.g., namelist diffs)

Key Features
-----------

**Hierarchical Commands**
  Build nested command groups for intuitive command organization

**Debug Support**
  Enable debug logging and Python debugger integration

**File Logging**
  Capture debug output to files for troubleshooting

**Exception Handling**
  Automatic post-mortem debugging on exceptions

The ``cli`` Group
-----------------

The :func:`cli` function is a Click group that serves as the entry point for benchmark CLI applications:

.. code-block:: python

    from ifsbench import cli
    
    @cli.group()
    def mybench():
        """My benchmark group"""
        pass
    
    @mybench.command('run')
    def run_benchmark():
        """Run the benchmark"""
        pass

CLI Options
~~~~~~~~~~~

The main CLI group provides the following options:

**--debug / --no-debug**
  Enable verbose logging (default: disabled)

**--log <PATH>**
  Write debug-level information to a log file

**--pdb**
  Attach Python debugger on exceptions (default: disabled)

Example Usage:

.. code-block:: bash

    # Run benchmark with debug logging
    my_benchmark.py --debug run
    
    # Run with output logged to file
    my_benchmark.py --log debug.log run
    
    # Run with debugger on exception
    my_benchmark.py --pdb run

RunOptions
~~~~~~~~~~

The :class:`RunOptions` class provides common command-line options for benchmark run commands:

.. code-block:: python

    from ifsbench.command_line import RunOptions, run_options
    
    @cli.command()
    @run_options
    @click.pass_context
    def run(ctx, **kwargs):
        """Run a benchmark"""
        options = RunOptions.from_dict(kwargs)
        # Use options for benchmark execution

Typical options include:

* Number of runs
* Output directory
* Configuration file path
* Benchmark selection
* Parameter overrides

ReferenceOptions
~~~~~~~~~~~~~~~~

The :class:`ReferenceOptions` class provides common options for commands that compare against reference 
results:

.. code-block:: python

    from ifsbench.command_line import ReferenceOptions, reference_options
    
    @cli.command()
    @reference_options
    @click.pass_context
    def validate(ctx, **kwargs):
        """Validate against reference results"""
        options = ReferenceOptions.from_dict(kwargs)
        # Use options for comparison

Typical options include:

* Reference result path
* Tolerance settings
* Comparison mode (absolute, relative, etc.)
* Output format for comparison results

Namelist Utilities
------------------

The :mod:`ifsbench.command_line.nml_diff` module provides utilities for comparing Fortran namelists:

.. code-block:: python

    from ifsbench.command_line import nml_diff
    
    # Compare two namelist files
    result = nml_diff.compare_namelists("namelist1.nml", "namelist2.nml")

Features:

* Parse namelist files
* Compare namelist contents
* Report differences
* Format output for CLI display
* Handle complex nested namelist structures

Common Workflow
---------------

Creating a Benchmark Script with CLI
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from ifsbench import cli
    import click
    
    # Create a benchmark group
    @cli.group()
    def my_benchmarks():
        """My IFS benchmarks"""
        pass
    
    # Create a nested group for a specific configuration
    @my_benchmarks.group()
    def tco399():
        """TCO399 benchmarks"""
        pass
    
    # Add specific benchmark commands
    @tco399.command('forecast')
    @click.option('--hours', type=int, default=240)
    def forecast(hours):
        """Run a forecast benchmark"""
        print(f"Running {hours}-hour forecast")
    
    @tco399.command('data-assimilation')
    def data_assimilation():
        """Run a data assimilation benchmark"""
        print("Running data assimilation benchmark")
    
    if __name__ == '__main__':
        cli()

Usage:

.. code-block:: bash

    # List available commands
    python my_benchmarks.py --help
    
    # Run specific benchmark
    python my_benchmarks.py my_benchmarks tco399 forecast --hours 120
    
    # Debug mode
    python my_benchmarks.py --debug my_benchmarks tco399 forecast

Nesting Commands
~~~~~~~~~~~~~~~~

For complex benchmark suites, commands can be nested multiple levels:

.. code-block:: bash

    ./benchmarks.py                    # Show main help
    ./benchmarks.py --help             # Detailed help
    ./benchmarks.py ifs                # Show IFS benchmark commands
    ./benchmarks.py ifs tco399         # Show TCO399 commands
    ./benchmarks.py ifs tco399 fc      # Show forecast command details
    ./benchmarks.py --debug ifs tco399 fc  # Run with debug logging

Integration with Benchmarks
----------------------------

The CLI tools integrate with:

* **Benchmark Framework**: Execute :class:`Benchmark` instances from CLI
* **Results**: Display and export benchmark results
* **Configuration**: Load benchmark configurations from YAML/JSON
* **Validation**: Compare results against references

Best Practices
--------------

1. **Use Click Decorators**: Leverage Click for automatic help and argument validation
2. **Organize Hierarchically**: Group related benchmarks into command groups
3. **Document Commands**: Provide clear docstrings for all commands
4. **Handle Errors Gracefully**: Catch exceptions and provide helpful error messages
5. **Enable Logging**: Use the ``--log`` option for troubleshooting
6. **Version Information**: Include version info in help output

Advanced Topics
---------------

Context Objects
~~~~~~~~~~~~~~~

Use Click's context object to pass data between commands:

.. code-block:: python

    @cli.group()
    @click.pass_context
    def benchmarks(ctx):
        ctx.obj = {'config': load_config()}
    
    @benchmarks.command()
    @click.pass_context
    def run(ctx):
        config = ctx.obj['config']

Callback Validation
~~~~~~~~~~~~~~~~~~~

Use Click callbacks for argument validation:

.. code-block:: python

    def validate_path(ctx, param, value):
        if value and not Path(value).exists():
            raise click.BadParameter(f"Path does not exist: {value}")
        return value
    
    @cli.command()
    @click.option('--config', callback=validate_path)
    def run(config):
        pass

API Reference
--------------

For complete API documentation, see :ref:`ifsbench.command_line in the API reference <ifsbench.command_line>`.
