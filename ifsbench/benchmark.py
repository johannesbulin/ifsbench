"""
Classes to set-up a benchmark
"""
from abc import ABC, abstractmethod
from collections import defaultdict
from enum import Enum, auto
from pathlib import Path
from subprocess import CalledProcessError
import sys
import glob
import re
import yaml

from .drhook import DrHook
from .logging import warning, error, header, success
from .util import copy_data, symlink_data, as_tuple, flatten, gettempdir, execute
from .runrecord import RunRecord


__all__ = ['Benchmark', 'InputFile', 'ExperimentFiles', 'SpecialRelativePath', 'ExperimentFilesBenchmark']


class Benchmark(ABC):
    """
    Definition of a general benchmark setup

    Parameters
    ----------
    expid : str
        The experiment id corresponding to the input data set.
    ifs : :any:`IFS`
        The IFS configuration object.
    rundir : str or :any:`pathlib.Path`, optional
        The default working directory to be used for :meth:`run`.
    """

    def __init__(self, **kwargs):
        self.expid = kwargs.get('expid')
        self.rundir = kwargs.get('rundir', None)

        self.ifs = kwargs.get('ifs')

    @property
    @classmethod
    @abstractmethod
    def input_files(cls):
        """
        List of relative paths that define all necessary input data files to
        run this benchmark

        Returns
        -------
        list of str or :any:`pathlib.Path`
            Relative paths for all input files required to run this benchmark.
            The relative paths will be reproduced in :attr:`Benchmark.rundir`.
        """

    @classmethod
    def from_files(cls, **kwargs):
        """
        Create instance of :class:`Benchmark` by globbing a set of input paths
        for the necessary input data and copying or linking it into rundir

        Parameters
        ----------
        rundir : str or :any:`pathlib.Path`
            Run directory to copy/symlink input data into
        srcdir : (list of) str or :any:`pathlib.Path`
            One or more source directories to search for input data
        ifsdata : str or :any:`pathlib.Path`, optional
            `ifsdata` directory to link as a whole
            (default: :attr:`Benchmark.input_data`)
        input_files : list of str, optional
            Relative paths of necessary input files
        copy : bool, optional
            Copy files into :data:`rundir` instead of symlinking them (default: False)
        force : bool, optional
            Overwrite existing input files and re-link/copy (default: False)
        """
        srcdir = as_tuple(kwargs.get('srcdir'))
        rundir = Path(kwargs.get('rundir'))
        copy = kwargs.pop('copy', False)
        force = kwargs.pop('force', False)
        ifsdata = kwargs.get('ifsdata', None)
        input_files = kwargs.get('input_files', cls.input_files)

        if ifsdata is not None:
            symlink_data(Path(ifsdata), rundir/'ifsdata', force=force)

        # Copy / symlink input files into rundir
        for path in input_files:
            path = Path(path)
            dest = Path(rundir) / path
            candidates = flatten([list(Path(s).glob('**/%s' % path.name)) for s in srcdir])
            if len(candidates) == 0:
                warning('Input file %s not found in %s' % (path.name, srcdir))
                continue
            if len(candidates) == 1:
                source = candidates[0]
            else:
                warning('More than one input file %s found in %s' % (path.name, srcdir))
                source = candidates[0]

            if copy:
                copy_data(source, dest, force=force)
            else:
                symlink_data(source, dest, force=force)

        return cls(**kwargs)

    @classmethod
    def from_tarball(cls):
        """
        Create instance of ``Benchmark`` object from given tarball
        """
        pass

    def to_tarball(self, filepath):
        """
        Dump input files and configuration to a tarball for off-line
        benchmarking.
        """
        pass

    def check_input(self):
        """
        Check input file list matches benchmark configuration.
        """
        for path in self.input_files:
            filepath = self.rundir / path
            if not filepath.exists():
                raise RuntimeError('Required input file %s not found!' % filepath)

    def run(self, **kwargs):
        """
        Run the specified benchmark and validate against stored results.
        """
        if 'rundir' in kwargs:
            if kwargs['rundir'] != self.rundir:
                error('Stored run directory: %s' % self.rundir)
                error('Given run directory:  %s' % kwargs['rundir'])
                raise RuntimeError('Conflicting run directories provided!')
        else:
            kwargs['rundir'] = self.rundir

        try:
            self.ifs.run(**kwargs)

        except CalledProcessError:
            error('Benchmark run failed: %s' % kwargs)
            sys.exit(-1)

        # Provide DrHook output path only if DrHook is active
        drhook = kwargs.get('drhook', DrHook.OFF)
        drhook_path = None if drhook == DrHook.OFF else self.rundir/'drhook.*'

        dryrun = kwargs.get('dryrun', False)
        if not dryrun:
            return RunRecord.from_run(nodefile=self.rundir/'NODE.001_01', drhook=drhook_path)
        return None


class InputFile:
    """
    Representation of a single input file together with some meta data

    Parameters
    ----------
    path : str or :any:`pathlib.Path`
        The path of the input file
    src_dir : str or :any:`pathlib.Path`, optional
        The base directory relative to which :attr:`path` is interpreted.
    compute_metadata : bool, optional
        Compute meta data for that file (such as SHA-256 checksum and size).
    """

    def __init__(self, path, src_dir=None, compute_metadata=True):
        if src_dir is None:
            src_dir = '/'
        self._src_dir = Path(src_dir)
        self._path = Path(path).relative_to(self.src_dir)

        if compute_metadata:
            self.checksum = self._sha256sum(self.fullpath)
            self.size = self._size(self.fullpath)
        else:
            self.checksum = None
            self.size = None

    @classmethod
    def from_dict(cls, data, src_dir=None, verify_checksum=True):
        """
        Create :any:`InputFile` from a dict representation

        Parameters
        ----------
        data : dict
            The dict representation, e.g. created by :meth:`to_dict`
        src_dir : str or :any:`pathlib.Path`, optional
            The base directory relative to which the path should be stored.
        verify_checksum : bool, optional
            Verify that checksum in dict matches the file.
        """
        path, meta = data.popitem()
        assert not data
        obj = cls(meta['fullpath'], src_dir=src_dir, compute_metadata=verify_checksum)
        if verify_checksum:
            if meta['sha256sum'] != obj.checksum:
                raise ValueError('Checksum for {} does not match'.format(path))
        else:
            obj.checksum = meta.get('sha256sum')
            obj.size = meta.get('size')
        return obj

    def to_dict(self):
        """Create a `dict` representation of the meta data for this file"""
        data = {'fullpath': str(self.fullpath)}
        if self.checksum:
            data['sha256sum'] = self.checksum
        if self.size:
            data['size'] = self.size
        return {str(self.path): data}

    @property
    def fullpath(self):
        """The full path of the file"""
        return self.src_dir/self._path

    @property
    def path(self):
        """The path of the file relative to :attr:`src_dir`"""
        return self._path

    @property
    def src_dir(self):
        """The base directory under which the file is located"""
        return self._src_dir

    @staticmethod
    def _sha256sum(filepath):
        """Create SHA-256 checksum for the file at the given path"""
        filepath = Path(filepath)
        logfile = gettempdir()/'checksum.sha256'
        cmd = ['sha256sum', str(filepath)]
        execute(cmd, logfile=logfile)
        with logfile.open() as f:
            checksum, name = f.read().split()
            assert name == str(filepath)
        return checksum

    @staticmethod
    def _size(filepath):
        """Obtain file size in byte for the file at the given path"""
        filepath = Path(filepath)
        return filepath.stat().st_size

    def __hash__(self):
        """
        Custom hash function using :attr:`InputFile.checksum`, if
        available, and :attr:`InputFile.fullpath` otherwise.
        """
        return hash(self.checksum or self.fullpath)

    def __eq__(self, other):
        """
        Compare to another object

        If available, compare :attr:`InputFile.checksum`, otherwise
        rely on :attr:`InputFile.fullpath`.
        """
        if not isinstance(other, InputFile):
            return False
        if not self.checksum or not other.checksum:
            return self.fullpath == other.fullpath
        return self.checksum == other.checksum


class ExperimentFiles:
    """
    Helper class to store the list of files required to run an experiment

    It provides capabilities to pack and unpack tarballs of these files
    to prepare an experiment for external runs.

    Parameters
    ----------
    exp_id : str
        The id of the experiment
    src_dir : (list of) str or :any:`pathlib.Path`, optional
        One or more source directories from which input data to take.
        If given, files are searched for in these paths.
    """

    def __init__(self, exp_id, src_dir=None):
        self.exp_id = exp_id
        self.src_dir = tuple(Path(s) for s in as_tuple(src_dir))
        self._files = set()

    @classmethod
    def from_yaml(cls, input_path, verify_checksum=True):
        """
        Load :any:`ExperimentFiles` from a YAML file

        Parameters
        ----------
        input_path : str or :any:`pathlib.Path`
            The file name of the YAML file.
        verify_checksum : bool, optional
            Verify checksum of all files.
        """
        with Path(input_path).open() as f:
            return cls.from_dict(yaml.safe_load(f), verify_checksum=verify_checksum)

    @classmethod
    def from_dict(cls, data, verify_checksum=True):
        """
        Create :any:`ExperimentFiles` from `dict` representation

        Parameters
        ----------
        data : dict
            The dictionary representation, e.g. as created by :meth:`to_dict`.
        verify_checksum : bool, optional
            Verify checksum of all files.
        """
        exp_id, src_dir_files = data.popitem()
        assert not data
        src_dir = list(src_dir_files.keys())
        obj = cls(exp_id, src_dir=src_dir)
        obj._files = {  # pylint: disable=protected-access
            InputFile.from_dict({p: f}, src_dir=src_dir, verify_checksum=verify_checksum)
            for src_dir, files in src_dir_files.items() for p, f in files.items()
        }
        return obj

    def to_yaml(self, output_path):
        """
        Save list of experiment files and their meta data as a YAML file.

        Parameters
        ----------
        output_path : str or :any:`pathlib.Path`
            File name for the YAML file.
        """
        with Path(output_path).open('w') as f:
            yaml.safe_dump(self.to_dict(), f, sort_keys=False)

    def to_dict(self):
        """
        Create a dictionary containing the list of experiment files and the
        meta data stored for them.
        """
        data = defaultdict(dict)
        for f in self.files:
            data[str(f.src_dir)].update(f.to_dict())
        return {self.exp_id: dict(data)}

    def _input_file_in_src_dir(self, input_file, verify_checksum=False):
        """
        Find :attr:`input_file` in :attr:`ExperimentFiles.src_dir`

        The file is identified by comparing file name and checksum.
        """
        if not self.src_dir:
            return input_file
        candidates = [
            (path, src_dir)
            for src_dir in self.src_dir
            for path in glob.iglob(str(src_dir/'**'/input_file.path.name), recursive=True)
        ]
        for path, src_dir in candidates:
            candidate_file = InputFile(path, src_dir)
            if candidate_file.checksum == input_file.checksum:
                return candidate_file
        if verify_checksum:
            raise ValueError('Input file {} not found in source directories'.format(input_file.path.name))
        warning('Input file %s not found in source directories', input_file.path.name)
        return input_file

    def add_file(self, *filepath, compute_metadata=True):
        """
        Add one or more files to the list of input files for the experiment

        Parameters
        ----------
        filepath : (list of) str or :any:`pathlib.Path`
            One or multiple file paths to add.
        """
        for path in filepath:
            input_file = InputFile(path, compute_metadata=compute_metadata)
            input_file = self._input_file_in_src_dir(input_file, verify_checksum=compute_metadata)
            self._files.add(input_file)

    def add_input_file(self, *input_file, verify_checksum=True):
        """
        Add one or more :any:`InputFile` to the list of input files

        Parameters
        ----------
        Input_file : (list of) :any:`InputFile`
            One or multiple input file instances to add.
        """
        for f in input_file:
            new_file = self._input_file_in_src_dir(f, verify_checksum=verify_checksum)
            self._files.add(new_file)

    def update_srcdir(self, src_dir, update_files=True, with_ifsdata=False):
        """
        Change the :attr:`ExperimentFiles.src_dir` relative to which input
        files are searched

        Parameters
        ----------
        src_dir : (list of) str or :any:`pathlib.Path`, optional
            One or more source directories.
        update_files : bool, optional
            Update paths for stored files. This verifies checksums.
        with_ifsdata : bool, optional
            Include ifsdata files in the update.
        """
        self.src_dir = as_tuple(src_dir)

        if update_files:
            if with_ifsdata:
                old_files = self.files
                new_files = set()
            else:
                old_files = self.exp_files
                new_files = self.ifsdata_files
            while old_files:
                new_file = self._input_file_in_src_dir(old_files.pop(), verify_checksum=True)
                new_files.add(new_file)
            self._files = new_files

    @property
    def files(self):
        """
        The set of :any:`InputFile` for the experiment
        """
        return self._files.copy()

    @property
    def exp_files(self):
        """
        The set of experiment-specific :any:`InputFile`
        """
        return {f for f in self._files if '/ifsdata/' not in str(f.fullpath)}

    @property
    def ifsdata_files(self):
        """
        The set of static ifsdata files used by the experiment
        """
        return {f for f in self._files if '/ifsdata/' in str(f.fullpath)}

    @staticmethod
    def _create_tarball(files, output_basename, basedir=None):
        """
        Create a tarball containing :attr:`files`

        Parameters
        ----------
        files : list of str
            The files to be included in the tarball.
        output_basename : str
            The base name without suffix of the tarball.
        basedir : str, optional
            If given, :attr:`files` are interpreted as relative to this.
        """
        output_file = Path(output_basename).with_suffix('.tar.gz')
        header('Creating tarball %s...', str(output_file))
        cmd = ['tar', 'cvzhf', str(output_file)]
        if basedir:
            cmd += ['-C', str(basedir)]
        cmd += files
        execute(cmd)
        success('Finished creating tarball')

    def to_tarball(self, output_dir, with_ifsdata=False):
        """
        Create tarballs containing all input files

        Parameters
        ----------
        output_dir : str or :any:`pathlib.Path`
            Output directory for tarballs.
        with_ifsdata : bool, optional
            Create also a tarball containing the ifsdata files used by
            this experiment (default: disabled).
        """
        output_dir = Path(output_dir)

        exp_files = defaultdict(list)
        for f in self.exp_files:
            exp_files[f.src_dir] += [str(f.path)]
        for src_dir, files in exp_files.items():
            output_basename = output_dir/(src_dir.name or 'other')
            self._create_tarball(files, output_basename, basedir=src_dir)

        if with_ifsdata:
            ifsdata_files = list(self.ifsdata_files)
            if ifsdata_files:
                basedir = ifsdata_files[0].src_dir
                files = [str(f.path) for f in ifsdata_files]
                output_basename = output_dir/'ifsdata'
                self._create_tarball(files, output_basename, basedir=basedir)

    @staticmethod
    def _extract_tarball(filepath, output_dir):
        """
        Extract a tarball

        Parameters
        ----------
        filepath : str or :any:`pathlib.Path`
            The file path for the tarball
        output_dir : str or :any:`pathlib.Path`
            Output directory for extracted files.
        """
        filepath = Path(filepath).resolve()
        header('Extracting tarball %s', str(filepath))
        cmd = ['tar', 'xvzf', str(filepath)]
        execute(cmd, cwd=str(output_dir))
        success('Finished extracting tarball')

    @classmethod
    def from_tarball(cls, summary_file, input_dir, output_dir, ifsdata_dir=None,
                     with_ifsdata=False, verify_checksum=True):
        """
        Create :any:`ExperimentFiles` from a summary file and unpack corresponding tarballs
        containing the files

        Parameters
        ----------
        summary_file : str or :any:`pathlib.Path`
            The file path for the YAML file
        input_dir : (list of) str or :any:`pathlib.Path`
            One or multiple input directories to search recursively for tarballs.
        output_dir : str or :any:`pathlib.Path`
            Output directory for files after unpacking tarballs.
        ifsdata_dir : str or :any:`pathlib.Path`, optional
            Directory to look for ifsdata files (default: :data:`output_dir`).
        with_ifsdata : bool, optional
            Look for an `ifsdata.tar.gz` tarball in the same directories as the
            experiment file tarballs and unpack it to :data:`ifsdata_dir` (default: disabled).
        verify_checksum : bool, optional
            Verify that all files exist and checksums match (default: enabled).
        """
        summary_file = Path(summary_file).resolve()
        obj = cls.from_yaml(summary_file, verify_checksum=False)

        # Find all tarballs for experiment files
        input_dir = [Path(path).resolve() for path in as_tuple(input_dir)]
        tarballs = set()
        for f in obj.exp_files:
            tarball_name = '{}.tar.gz'.format(f.src_dir.name)
            candidates = [path for src_dir in input_dir
                          for path in glob.iglob(str(src_dir/'**'/tarball_name), recursive=True)]
            if not candidates:
                raise ValueError('Archive {} not found in input directories'.format(tarball_name))
            if len(candidates) > 1:
                warning('Found multiple candidates for %s, using the first: %s',
                        tarball_name, ', '.join(candidates))
            tarballs.add(candidates[0])

        # Add ifsdata tarball
        ifsdata_tarball = None
        if with_ifsdata:
            if tarballs:
                candidates = list({Path(path).with_name('ifsdata.tar.gz') for path in tarballs})
            else:
                candidates = [Path(path)/'ifsdata.tar.gz' for path in input_dir]
            candidates = [str(path) for path in candidates if path.exists()]
            if not candidates:
                raise ValueError('ifsdata.tar.gz not found in any experiment tarball directory')
            if len(candidates) > 1:
                warning('Found multiple candidates for ifsdata.tar.gz, using the first: %s',
                        ', '.join(candidates))
            ifsdata_tarball = candidates[0]

        # Extract all tarballs
        output_dir = (Path(output_dir)/obj.exp_id).resolve()
        if tarballs:
            output_dir.mkdir(exist_ok=True)
            for tarball in tarballs:
                cls._extract_tarball(tarball, output_dir)

        if ifsdata_dir is None:
            ifsdata_dir = output_dir
        else:
            ifsdata_dir = Path(ifsdata_dir).resolve()
        if ifsdata_tarball is not None:
            ifsdata_dir.mkdir(exist_ok=True)
            cls._extract_tarball(ifsdata_tarball, ifsdata_dir)

        # Update paths (which automatically verifies checksums)
        if verify_checksum:
            src_dir = [output_dir]
            if ifsdata_dir is not None:
                src_dir += [ifsdata_dir]
            obj.update_srcdir(src_dir, update_files=True,
                              with_ifsdata=with_ifsdata or ifsdata_dir is not None)

        # Save (updated) YAML file in output_dir
        if tarballs:
            obj.to_yaml(output_dir/summary_file.name)
        elif ifsdata_tarball is not None:
            obj.to_yaml(ifsdata_dir/summary_file.name)

        return obj


class SpecialRelativePath:
    """
    Define a search and replacement pattern for special input files
    that need to have a particular name or relative path

    It is essentially a wrapper for :any:`re.sub`.

    Parameters
    ----------
    pattern : str or :any:`re.Pattern`
        The search pattern to match a path against
    repl : str
        The replacement string to apply
    """

    def __init__(self, pattern, repl):
        if isinstance(pattern, str):
            self.pattern = re.compile(pattern)
        self.repl = repl

    class NameMatch(Enum):
        """
        Enumeration of available types of name matches

        Attributes
        ----------
        EXACT :
            Match the name exactly as is
        LEFT_ALIGNED :
            Match the name from the start but it can be followed
            by other characters
        RIGHT_ALIGNED :
            Match the name from the end but it can be preceded by
            other characters
        FREE :
            Match the name but allow for other characters before
            and after
        """
        EXACT = auto()
        LEFT_ALIGNED = auto()
        RIGHT_ALIGNED = auto()
        FREE = auto()

    @classmethod
    def from_filename(cls, filename, repl, match=NameMatch.FREE):
        r"""
        Create a :class:`SpecialRelativePath` object that matches
        a specific file name

        Parameters
        ----------
        filename : str
            The filename (or part of it) that should match
        repl : str
            The relative path to retrun. :data:`repl` can reference components
            of the matched path: original filename as ``\g<name>``, path
            without filename as ``\g<parent>``, matched part of the filename
            as ``\g<match>`` and parts of the filename before/after the
            matched section as ``\g<pre>``/``\g<post>``, respectively.
        match : :any:`SpecialRelativePath.NameMatch`, optional
            Determines if the file name should be matched exactly
        """
        pattern = r"^(?P<parent>.*?\/)?(?P<name>"
        if match in (cls.NameMatch.RIGHT_ALIGNED, cls.NameMatch.FREE):
            pattern += r"(?P<pre>[^\/]*?)"
        pattern += r"(?P<match>{})".format(filename)
        if match in (cls.NameMatch.LEFT_ALIGNED, cls.NameMatch.FREE):
            pattern += r"(?P<post>[^\/]*?)"
        pattern += r")$"
        return cls(pattern, repl)

    @classmethod
    def from_dirname(cls, dirname, repl, match=NameMatch.FREE):
        r"""
        Create a :class:`SpecialRelativePath` object that matches
        paths that have a certain subdirectory in their path

        Parameters
        ----------
        dirname : str
            The directory name (or part of it) that should match
        repl : str
            The relative path to retrun. :data:`repl` can reference components
            of the matched path: original dirname as ``\g<name>``, path
            without matched directory as ``\g<parent>``, matched part of the
            directory name as ``\g<match>``, path following the matched
            directory as ``\g<child>``, and parts of the directory name
            before/after the matched section as ``\g<pre>``/``\g<post>``,
            respectively.
        match : :any:`SpecialRelativePath.NameMatch`, optional
            Determines if the directory name should be matched exactly
        """
        pattern = r"^(?P<parent>.*?\/)?(?P<name>"
        if match in (cls.NameMatch.RIGHT_ALIGNED, cls.NameMatch.FREE):
            pattern += r"(?P<pre>[^\/]*?)"
        pattern += r"(?P<match>{})".format(dirname)
        if match in (cls.NameMatch.LEFT_ALIGNED, cls.NameMatch.FREE):
            pattern += r"(?P<post>[^\/]*?)"
        pattern += r")(?P<child>\/.*?)$"
        return cls(pattern, repl)

    def __call__(self, path):
        """
        Apply :any:`re.sub` with :attr:`SpecialRelativePath.pattern`
        and :attr:`SpecialRelativePath.repl` to :data:`path`
        """
        return self.pattern.sub(self.repl, str(path))


class ExperimentFilesBenchmark(Benchmark):
    """
    General :class:`Benchmark` setup created from input file description
    provided by :class:`ExperimentFiles`

    """

    def __init__(self, **kwargs):
        self._input_files = kwargs.pop('input_files')
        super().__init__(**kwargs)

    @property
    @classmethod
    def special_paths(cls):
        """
        List of :class:`SpecialRelativePath` patterns that define transformations
        for converting a file path to a particular relative path object.

        Returns
        -------
        list of :any:`SpecialRelativePath`
        """

    @property
    def input_files(self):
        return self._input_files

    @classmethod
    def from_experiment_files(cls, **kwargs):
        """
        Instantiate :class:`Benchmark` using input file lists captured in an
        :class:`ExperimentFiles` object
        """
        rundir = Path(kwargs.get('rundir'))
        exp_files = kwargs.pop('exp_files')
        copy = kwargs.pop('copy', False)
        force = kwargs.pop('force', False)
        ifsdata = kwargs.get('ifsdata', None)

        if ifsdata is not None:
            symlink_data(Path(ifsdata), rundir/'ifsdata', force=force)

        special_paths = cls.special_paths if isinstance(cls.special_paths, (list, tuple)) else ()
        input_files = []
        for f in exp_files.files:
            dest, source = str(f.fullpath), str(f.fullpath)
            for pattern in special_paths:
                dest = pattern(dest)
                if dest != source:
                    break
            else:
                dest = str(Path(dest).name)

            input_files += [dest]
            source, dest = Path(source), rundir/dest
            if copy:
                copy_data(source, dest, force=force)
            else:
                symlink_data(source, dest, force=force)

        obj = cls(input_files=input_files, **kwargs)
        return obj
