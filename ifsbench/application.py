# (C) Copyright 2020- ECMWF.
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

from abc import ABC, abstractmethod
from pathlib import Path

from .launch import Job

class Application(ABC):

    @abstractmethod
    def get_data_handlers(self, job, kwargs):
        return NotImplemented

    @abstractmethod
    def get_env_handlers(self, job, kwargs):
        return NotImplemented

    @abstractmethod
    def get_library_paths(self):
        return NotImplemented

    @abstractmethod
    def get_executable_path(self):
        return NotImplemented

class DefaultApplication(Application):

    def __init__(self, path, data_handlers=None, env_handlers=None, lib_paths=None):
        self._path = path
        self._data_handlers = data_handlers
        self._env_handlers = env_handlers
        self._lib_paths = lib_paths

    def get_data_handlers(self, job, kwargs):
        if self._data_handlers is None:
            return []
        return list(self._data_handlers)

    def get_env_handlers(self, job, kwargs):
        if self._env_handlers is None:
            return []
        return list(self._env_handlers)

    def get_library_paths(self):
        if self._lib_paths is None:
            return []
        return list(self._lib_paths)

    def get_executable_path(self):
        return Path(self._path)