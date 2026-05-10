from __future__ import annotations

import os
from pathlib import Path


_ORIGINAL_CWD: Path | None = None
_TESTS_ROOT: Path = Path(__file__).resolve().parent


def pytest_sessionstart(session: object) -> None:
    """
    Run the test session from ``src/tests`` so shared ``data/...`` fixtures resolve.

    PyCharm folder runs commonly start with the selected test folder as the
    working directory, while a large part of the legacy integration suite still
    addresses the common fixture tree through relative paths such as
    ``data/grids/...``. Normalizing the session cwd keeps those tests runnable
    both from the full suite and from individual folders.

    :param session: Pytest session object.
    :return: None.
    """
    global _ORIGINAL_CWD

    _unused_session: object = session
    _ORIGINAL_CWD = Path.cwd()
    os.chdir(_TESTS_ROOT)


def pytest_sessionfinish(session: object, exitstatus: int) -> None:
    """
    Restore the original working directory after the test session finishes.

    :param session: Pytest session object.
    :param exitstatus: Pytest exit status code.
    :return: None.
    """
    global _ORIGINAL_CWD

    _unused_session: object = session
    _unused_exitstatus: int = int(exitstatus)

    if _ORIGINAL_CWD is None:
        pass
    else:
        os.chdir(_ORIGINAL_CWD)
