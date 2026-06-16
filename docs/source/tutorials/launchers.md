# Launchers

A {class}`~ifsbench.launch.Launcher` is responsible for building the command
line that will actually run a parallel executable.
Given a {class}`~ifsbench.job.Job` specification (number of tasks, nodes, CPU
binding, …) it produces a {class}`~ifsbench.launch.LaunchData` object containing
the final command and environment, which can then be executed.

---

## The Launcher hierarchy

```
Launcher  (abstract)
├── DirectLauncher   – runs the command directly, optionally via a wrapper binary
├── SrunLauncher     – builds a srun (SLURM) invocation
└── MpirunLauncher   – builds an mpirun invocation

LauncherWrapper  (abstract)
├── DDTLauncher      – wraps any launch command with Linaro DDT
└── BashLauncher     – writes the command to a bash script instead of running it directly

CompositeLauncher    – combines a base Launcher with one or more LauncherWrappers
```

---

## Basic launchers

### `DirectLauncher`

Runs the application directly.
An optional `executable` attribute lets you prepend a wrapper binary (e.g. a
profiler or a container runtime).

```python
from ifsbench.launch import DirectLauncher

# Execute the command as-is
launcher = DirectLauncher()

# Wrap it with an arbitrary binary
launcher = DirectLauncher(executable='time', flags=['-v'])
```

### `SrunLauncher`

Translates {class}`~ifsbench.job.Job` attributes into `srun` flags.

```python
from ifsbench.launch import SrunLauncher
from ifsbench.job import Job, CpuBinding

launcher = SrunLauncher(flags=['--time=02:00:00'])
job = Job(tasks=256, nodes=8, cpus_per_task=4, bind=CpuBinding.BIND_CORES)
```

When `cpus_per_task` is set, `OMP_NUM_THREADS` is automatically added to the
environment.

### `MpirunLauncher`

Similar to `SrunLauncher` but targets a standard `mpirun` binary.

```python
from ifsbench.launch import MpirunLauncher

launcher = MpirunLauncher(flags=['--oversubscribe'])
```

---

## Launcher wrappers

A {class}`~ifsbench.launch.launcher.LauncherWrapper` is not a standalone launcher —
it *wraps* the {class}`~ifsbench.launch.LaunchData` produced by a base launcher and
modifies it.

### `DDTLauncher`

Prepends `ddt --` to the existing command so that the application is launched
inside a [Linaro DDT](https://www.linaroforge.com/linaroDdt/) debug session.

```python
from ifsbench.launch.ddtlauncher import DDTLauncher

ddt = DDTLauncher(flags=['--offline'])
```

### `BashLauncher`

Instead of running the command directly, it writes it to a dated bash script
(under `run_dir/bash_scripts/`) and executes that.
This is useful for auditing — you always have a record of exactly what was run.

```python
from ifsbench.launch.bashlauncher import BashLauncher

bash_wrapper = BashLauncher()
```

---

## Combining launchers with `CompositeLauncher`

{class}`~ifsbench.launch.CompositeLauncher` takes a base launcher and an ordered
list of wrappers.
The base launcher builds the initial {class}`~ifsbench.launch.LaunchData`;
each wrapper then transforms it in sequence.

### Python example

```python
from ifsbench.launch import CompositeLauncher, SrunLauncher
from ifsbench.launch.bashlauncher import BashLauncher
from ifsbench.launch.ddtlauncher import DDTLauncher

# srun → record to bash script → open in DDT
launcher = CompositeLauncher(
    base_launcher=SrunLauncher(flags=['--time=01:00:00']),
    wrappers=[
        BashLauncher(),
        DDTLauncher(flags=['--offline']),
    ],
)
```

### YAML example

```yaml
launcher:
  class_name: CompositeLauncher
  base_launcher:
    class_name: SrunLauncher
    flags:
      - --time=01:00:00
  wrappers:
    - class_name: BashLauncher
    - class_name: DDTLauncher
      flags:
        - --offline
```

---

## Standalone usage

A launcher can be used independently of a full benchmark setup.
Call `prepare` to obtain a {class}`~ifsbench.launch.LaunchData` object, then
call `launch` (or `launch_async`) on it.

```python
from pathlib import Path
from ifsbench.launch import SrunLauncher
from ifsbench.job import Job
from ifsbench.env import DefaultEnvPipeline, EnvHandler, EnvOperation
import os

launcher = SrunLauncher()
job = Job(tasks=32, nodes=1, cpus_per_task=4)

env_pipeline = DefaultEnvPipeline(env_initial=os.environ)
env_pipeline.add(EnvHandler(mode=EnvOperation.SET, key='MY_VAR', value='hello'))

launch_data = launcher.prepare(
    run_dir=Path('/scratch/run'),
    job=job,
    cmd=['/opt/myapp/bin/myapp', '--config', 'config.nml'],
    env_pipeline=env_pipeline,
)

result = launch_data.launch()
print('Exit code:', result.exit_code)
print('Wall time:', result.wall_time, 'seconds')
```
