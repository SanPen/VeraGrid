from __future__ import annotations

import threading
import time

from VeraGridServer.settings import FileOperationLockRegistry


def acquire_and_release_file_lock(registry: FileOperationLockRegistry,
                                  schema_name: str,
                                  file_idtag: str,
                                  ready_event: threading.Event,
                                  acquired_event: threading.Event) -> None:
    """
    Acquire one file lock in a worker thread and release it immediately.

    :param registry: Shared file-lock registry.
    :param schema_name: Target PostgreSQL schema name.
    :param file_idtag: Stored file identifier.
    :param ready_event: Event emitted before the blocking acquire.
    :param acquired_event: Event emitted after the acquire succeeds.
    :return: None.
    """
    ready_event.set()
    registry.acquire_file_lock(
        schema_name=schema_name,
        file_idtag=file_idtag,
    )

    try:
        acquired_event.set()
    finally:
        registry.release_file_lock(
            schema_name=schema_name,
            file_idtag=file_idtag,
        )


def test_file_operation_lock_registry_serializes_writers_per_file() -> None:
    """
    Verify one file key admits only one concurrent writer at a time.

    :return: None.
    """
    registry: FileOperationLockRegistry = FileOperationLockRegistry()
    ready_event: threading.Event = threading.Event()
    acquired_event: threading.Event = threading.Event()
    worker: threading.Thread = threading.Thread(
        target=acquire_and_release_file_lock,
        args=(registry, "veragrid", "shared_file", ready_event, acquired_event),
    )

    # The main thread holds the file lock first so the worker must block on the
    # same file key until the first writer releases the mutex.
    registry.acquire_file_lock(
        schema_name="veragrid",
        file_idtag="shared_file",
    )

    try:
        worker.start()
        assert ready_event.wait(timeout=1.0)
        time.sleep(0.05)
        assert not acquired_event.is_set()
    finally:
        registry.release_file_lock(
            schema_name="veragrid",
            file_idtag="shared_file",
        )

    assert acquired_event.wait(timeout=1.0)
    worker.join(timeout=1.0)
    assert not worker.is_alive()
