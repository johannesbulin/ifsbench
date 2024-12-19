# (C) Copyright 2020- ECMWF.
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

from enum import auto, Enum
import pathlib


from .logging import debug, info


__all__ = ['EnvOverride', 'EnvHandler']


class EnvOverride:
    """
    Specify changes that will be applied to a namelist.
    """
    class EnvOperation(Enum):
        SET = auto()
        APPEND = auto()
        DELETE = auto()

    def __init__(self, key, mode, value=None):
        """
        Parameters
        ----------
        key: str
            The environment variable that will be modified.

        mode: EnvOverride.EnvOperation
            What kind of operation is specified. Can be
                * Set a certain entry.
                * Append to an array entry.
                * Delete an entry.

        value:
            The value that is set (SET operation) or appended (APPEND).
        """

        self._key = str(key)
        self._mode = mode
        self._value = value

        if self._value is None:
            if self._mode in (self.EnvOperation.SET, self.EnvOperation.APPEND):
                raise ValueError("The new value must not be None!")

    def apply(self, env):
        """
        Apply the stored changes to an environment dict.

        Parameters
        ----------
        env: dict
            The environment dictionary.
        """

        if self._mode == self.EnvOverride.SET:
            debug(f"Set environment entry {str(self._key)} = {str(self._value)}.")
            env[self._key] = str(self._value)
        elif self._mode == self.EnvOverride.APPEND:
            if self._key in env:
                env[self._key] += ":" + str(self._value)
            else:
                env[self._key] = str(self._value)

            debug(f"Append {str(self._value)} to environment variable {str(self._key)}.")

        elif self._mode == self.NamelistOperation.DELETE:
            if self._key in env:
                debug(f"Delete environment variable {str(self._key)}.")
                del env[self._key]

class EnvHandler:
    """
    DataHandler specialisation that can modify Fortran namelists.
    """

    def __init__(self, overrides):
        """
        Initialise the environment handler.

        Parameters
        ----------

        overrides: iterable of EnvOverride
            The EnvOverride that will be applied.
        """

        self._overrides = list(overrides)
        for override in self._overrides:
            if not isinstance(override, EnvOverride):
                raise ValueError("Environment overrides must be EnvOverride objects!")

    def execute(self, env):
        new_env = dict(env)

        for override in self._overrides:
            override.apply(new_env)

        return new_env
