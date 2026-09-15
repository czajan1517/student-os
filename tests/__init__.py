"""Keep every module-based test run isolated from the development database."""

import os
import tempfile
from pathlib import Path


_TEST_DATABASE_DIRECTORY = tempfile.TemporaryDirectory(
    prefix="studentos-tests-"
)
_TEST_DATABASE_PATH = (
    Path(_TEST_DATABASE_DIRECTORY.name) / "studentos-tests.db"
)
os.environ["DATABASE_URL"] = (
    f"sqlite:///{_TEST_DATABASE_PATH.as_posix()}"
)
