# (C) Copyright 2020- ECMWF.
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import pathlib
from typing import Union
import urllib.error
import urllib.request

from ifsbench.config_mixin import PydanticConfigMixin
from ifsbench.data.datahandler import DataHandler
from ifsbench.logging import debug

__all__ = ['FetchHandler']

class FetchHandler(DataHandler, PydanticConfigMixin):
    """
    Fetch a file from a given URL.
    """

    #: The source URL from where the file gets fetched.
    source_url: str

    #: Path where the file will be placed. If the path is relative, it will
    #: be used relative to the run directory.
    target_path: pathlib.Path

    #: Whether the file will be fetched even if ``target_path`` exists already.
    force: bool = False

    #: If True, any errors encountered are ignored. Otherwise, a ``RuntimeError``
    #: is raised on failure.
    ignore_errors: bool = True

    def execute(self, wdir: Union[str, pathlib.Path], **kwargs) -> None:
        wdir = pathlib.Path(wdir)

        target_path = self.target_path

        if not self.target_path.is_absolute():
            target_path = wdir/self.target_path

        # Create the necessary parent folders.
        target_path.parent.mkdir(parents=True, exist_ok=True)

        if target_path.exists() and (not self.force):
            debug(f"File {target_path} exists already and won't be fetched.")
            return
        if target_path.exists():
            target_path.unlink()

        debug(f"Download file from {self.source_url} to {target_path}.")

        try:
            urllib.request.urlretrieve(self.source_url, filename=target_path)
        except urllib.error.URLError as ue:
            debug("Fetching file failed: {ue}")
            if not self.ignore_errors:
                raise RuntimeError(str(ue)) from ue
