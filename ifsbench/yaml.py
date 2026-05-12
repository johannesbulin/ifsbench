# (C) Copyright 2020- ECMWF.
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

"""
Utilities for loading YAML files with support for file imports and
template-based configuration.
"""

import copy
from pathlib import Path

import yaml


__all__ = ['read_yaml']


class _ConfigureMarker:
    """
    Placeholder for a ``!configure`` node that is resolved after the
    full document has been loaded.
    """

    def __init__(self, template_path, overrides):
        self.template_path = template_path
        self.overrides = overrides


def _make_loader(base_dir):
    """
    Create a custom YAML loader with ``!import`` and ``!configure``
    constructors that resolve paths relative to *base_dir*.
    """

    class _Loader(yaml.SafeLoader):
        pass

    def _import_constructor(loader, node):
        """Handle ``!import other_file.yaml``."""
        rel_path = loader.construct_scalar(node)
        import_path = (base_dir / rel_path).resolve()
        if not import_path.is_file():
            raise FileNotFoundError(
                f'Imported YAML file not found: {import_path}'
            )
        return read_yaml(str(import_path))

    def _configure_constructor(loader, tag_suffix, node):
        """Handle ``!configure:template/path`` mapping nodes."""
        overrides = loader.construct_mapping(node, deep=True)
        return _ConfigureMarker(tag_suffix.lstrip(':'), overrides)

    _Loader.add_constructor('!import', _import_constructor)
    _Loader.add_multi_constructor('!configure:', _configure_constructor)

    return _Loader


def _resolve_template(root, template_path):
    """
    Walk *root* (a dict) along the slash-separated *template_path* and
    return the value found there.
    """
    current = root
    for key in template_path.split('/'):
        try:
            current = current[key]
        except (KeyError, TypeError):
            raise KeyError(
                f'Template path {template_path!r} not found in YAML document'
            )
    return current


def _substitute(obj, overrides):
    """
    Recursively replace ``{key}`` placeholders in strings inside *obj*
    with values from *overrides*.
    """
    if isinstance(obj, str):
        for key, value in overrides.items():
            obj = obj.replace(f'{{{key}}}', str(value))
        return obj
    if isinstance(obj, dict):
        return {k: _substitute(v, overrides) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_substitute(item, overrides) for item in obj]
    return obj


def _resolve_markers(obj, root):
    """
    Walk the parsed data structure and resolve any
    :class:`_ConfigureMarker` instances using templates from *root*.
    """
    if isinstance(obj, _ConfigureMarker):
        template = copy.deepcopy(_resolve_template(root, obj.template_path))
        return _substitute(template, obj.overrides)
    if isinstance(obj, dict):
        return {k: _resolve_markers(v, root) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_resolve_markers(item, root) for item in obj]
    return obj


def read_yaml(filename, encoding='utf-8'):
    """
    Read and parse a YAML file with support for ``!import`` and
    ``!configure`` directives.

    The ``!import`` tag includes the content of another YAML file,
    resolved relative to the directory of *filename*::

        included: !import other_file.yaml

    The ``!configure`` tag references a template block defined
    elsewhere in the same document and substitutes ``{key}``
    placeholders with the provided values::

        templates:
          greeting:
            message: Hello, {name}!

        instances:
          welcome: !configure:templates/greeting
            name: World

    Parameters
    ----------
    filename : str or path-like
        Path to the YAML file to read.
    encoding : str, optional
        File encoding (default ``'utf-8'``).

    Returns
    -------
    object
        The parsed YAML content with all imports resolved and
        templates substituted.

    Raises
    ------
    FileNotFoundError
        If *filename* or any ``!import``-ed file does not exist.
    """
    filepath = Path(filename).resolve()
    if not filepath.is_file():
        raise FileNotFoundError(f'YAML file not found: {filepath}')

    base_dir = filepath.parent
    loader_cls = _make_loader(base_dir)

    with open(filepath, encoding=encoding) as fh:
        data = yaml.load(fh, Loader=loader_cls)

    data = _resolve_markers(data, data)
    return data
