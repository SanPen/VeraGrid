from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest


_ORIGINAL_CWD: Path | None = None
_TESTS_ROOT: Path = Path(__file__).resolve().parent


class _AttributeOverrideManager:
    """
    Deterministic attribute override manager for tests.

    The manager applies explicit ``setattr`` overrides and restores all mutated
    attributes in LIFO order when the fixture finalizes.
    """

    __slots__ = ("_restore_stack",)

    def __init__(self) -> None:
        """
        Build one empty override manager.

        :return: None.
        """
        self._restore_stack: list[tuple[object, str, bool, Any]] = list()

    def setattr(self, target: object, name: str, value: Any) -> None:
        """
        Override one attribute by object reference.

        :param target: Object instance/class/module.
        :param name: Attribute name.
        :param value: Replacement value.
        :return: None.
        """
        has_attr: bool = hasattr(target, name)
        old_value: Any = getattr(target, name, None)
        self._restore_stack.append((target, name, has_attr, old_value))
        setattr(target, name, value)

    def restore_all(self) -> None:
        """
        Restore every overridden attribute in reverse application order.

        :return: None.
        """
        while len(self._restore_stack) > 0:
            obj, attr_name, has_attr, old_value = self._restore_stack.pop()
            if has_attr:
                setattr(obj, attr_name, old_value)
            else:
                if hasattr(obj, attr_name):
                    delattr(obj, attr_name)
                else:
                    pass


@pytest.fixture
def override_attrs() -> _AttributeOverrideManager:
    """
    Provide deterministic runtime attribute overrides for test seams.

    :return: Override manager.
    """
    manager: _AttributeOverrideManager = _AttributeOverrideManager()
    try:
        yield manager
    finally:
        manager.restore_all()


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
