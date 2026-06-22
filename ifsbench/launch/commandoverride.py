# (C) Copyright 2020- ECMWF.
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

from abc import abstractmethod
from typing import List

from ifsbench.serialisation_mixin import (
    SubclassableSerialisationMixin,
)

__all__ = ['CommandOverride', 'CommandWrapOverride']


class CommandOverride(SubclassableSerialisationMixin):
    """
    Abstract base class for overriding a command before it is passed to a launcher.
    """

    @abstractmethod
    def override(self, cmd: List[str]) -> List[str]:
        """
        Return an updated version of the given command.

        Parameters
        ----------
        cmd: List[str]
            The original command.

        Returns
        -------
        List[str]
            The updated command.
        """
        return NotImplemented


class CommandWrapOverride(CommandOverride):
    """
    :any:`CommandOverride` implementation that allows appending/prepending to a
    command.

    The resulting command will be
        prepend_cmd + original_command + append_cmd.
    """

    #: List of tokens prepended to the command.
    prepend_cmd: List[str] = []

    #: List of tokens appended to the command.
    append_cmd: List[str] = []

    def override(self, cmd: List[str]) -> List[str]:
        return [*self.prepend_cmd, *cmd, *self.append_cmd]
