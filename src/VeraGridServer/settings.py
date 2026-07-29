# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import threading

from VeraGridServer.db.database import PostgreSqlConnectionSettings


class FileOperationLockRegistry:
    """
    Keep one process-local lock registry for file-scoped database writes.
    """

    __slots__ = ("_registry_lock", "_locks", "_holders")

    def __init__(self) -> None:
        """
        Build one empty file-lock registry.

        :return: None.
        """
        self._registry_lock: threading.Lock = threading.Lock()
        self._locks: dict[str, threading.RLock] = dict()
        self._holders: dict[str, int] = dict()

    def acquire_file_lock(self,
                          schema_name: str,
                          file_idtag: str) -> None:
        """
        Acquire the process-local write lock for one stored file.

        :param schema_name: Target PostgreSQL schema name.
        :param file_idtag: Stored file identifier.
        :return: None.
        """
        lock_key: str = self._build_lock_key(schema_name=schema_name, file_idtag=file_idtag)

        # The registry lock protects lock-object creation and waiter counting
        # so concurrent requests targeting the same file share one mutex.
        with self._registry_lock:
            file_lock: threading.RLock | None = self._locks.get(lock_key, None)

            if file_lock is None:
                file_lock = threading.RLock()
                self._locks[lock_key] = file_lock
                self._holders[lock_key] = 1
            else:
                self._holders[lock_key] += 1

        # The blocking acquire happens outside the registry lock so unrelated
        # file writes can continue creating or using different lock keys.
        file_lock.acquire()

    def release_file_lock(self,
                          schema_name: str,
                          file_idtag: str) -> None:
        """
        Release the process-local write lock for one stored file.

        :param schema_name: Target PostgreSQL schema name.
        :param file_idtag: Stored file identifier.
        :return: None.
        """
        lock_key: str = self._build_lock_key(schema_name=schema_name, file_idtag=file_idtag)

        with self._registry_lock:
            file_lock: threading.RLock | None = self._locks.get(lock_key, None)

        if file_lock is None:
            raise ValueError(f"No file lock exists for '{lock_key}'")
        else:
            pass

        # The file lock is released before the waiter count is decremented so
        # queued writers can proceed immediately on the same mutex object.
        file_lock.release()

        with self._registry_lock:
            remaining_holders: int = self._holders[lock_key] - 1

            if remaining_holders == 0:
                del self._holders[lock_key]
                del self._locks[lock_key]
            else:
                self._holders[lock_key] = remaining_holders

    def _build_lock_key(self,
                        schema_name: str,
                        file_idtag: str) -> str:
        """
        Build one stable registry key for one stored file.

        :param schema_name: Target PostgreSQL schema name.
        :param file_idtag: Stored file identifier.
        :return: Stable lock key.
        """
        return f"{schema_name}:{file_idtag}"

class ExtraSettings:
    def __init__(self):
        self.am_i_master: bool = True
        self.master_host: str = ""
        self.master_port = 0
        self.this_host: str = ""
        self.this_port = 0
        self.this_username = ""
        self.this_password = ""
        self.db_host: str = ""
        self.db_port: int = 0
        self.db_name: str = ""
        self.db_user: str = ""
        self.db_password: str = ""
        self.db_schema: str = "veragrid"
        self.file_operation_locks: FileOperationLockRegistry = FileOperationLockRegistry()

    def has_database_configuration(self) -> bool:
        """
        Check whether the database configuration is complete.

        :return: ``True`` when every database setting is present, ``False`` otherwise.
        """
        if (
            len(self.db_host) > 0
            and self.db_port > 0
            and len(self.db_name) > 0
            and len(self.db_user) > 0
            and len(self.db_password) > 0
        ):
            return True
        else:
            return False

    def get_database_settings(self) -> PostgreSqlConnectionSettings | None:
        """
        Build one PostgreSQL settings object when the configuration is complete.

        :return: PostgreSQL connection settings or ``None``.
        """
        if self.has_database_configuration():
            return PostgreSqlConnectionSettings(
                host=self.db_host,
                port=self.db_port,
                database=self.db_name,
                user_name=self.db_user,
                password=self.db_password,
                schema_name=self.db_schema,
            )
        else:
            return None

    def acquire_database_file_lock(self,
                                   schema_name: str,
                                   file_idtag: str) -> None:
        """
        Acquire the process-local write lock for one stored file.

        :param schema_name: Target PostgreSQL schema name.
        :param file_idtag: Stored file identifier.
        :return: None.
        """
        self.file_operation_locks.acquire_file_lock(
            schema_name=schema_name,
            file_idtag=file_idtag,
        )

    def release_database_file_lock(self,
                                   schema_name: str,
                                   file_idtag: str) -> None:
        """
        Release the process-local write lock for one stored file.

        :param schema_name: Target PostgreSQL schema name.
        :param file_idtag: Stored file identifier.
        :return: None.
        """
        self.file_operation_locks.release_file_lock(
            schema_name=schema_name,
            file_idtag=file_idtag,
        )


settings = ExtraSettings()
