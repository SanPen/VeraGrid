from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

import psycopg
import pytest
from psycopg.types.json import Json

import VeraGridEngine.api as vge
from VeraGridServer.db.database import (
    PostgreSqlConnectionSettings,
    get_veragrid_object_table_names,
    normalize_device_table_name,
)
from VeraGridServer.db.model_ops import (
    create_file,
    create_model,
    delete_file,
    get_file_models_json,
    get_files_with_models_json,
    get_model_json_payload,
    get_multicircuit_from_database,
    get_multiverse_from_database,
    put_multicircuit_in_database,
    put_multiverse_in_database,
)
from VeraGridServer.db.user_ops import get_user


GRID_FOLDER = Path(__file__).resolve().parents[1] / "data" / "grids"


class FakeCursor:
    """
    Minimal cursor used to verify generated SQL without a live PostgreSQL server.
    """

    __slots__ = ("executed_sql", "_missing_table_failures", "_payload_returned")

    def __init__(self) -> None:
        """
        Initialize the captured SQL list and payload-row state.

        :return: None.
        """
        self.executed_sql: list[str] = list()
        self._missing_table_failures: int = 0
        self._payload_returned: bool = False

    def execute(self, operation: str, parameters: Sequence[Any] | None = None) -> None:
        """
        Capture one SQL operation.

        :param operation: SQL statement.
        :param parameters: Optional positional parameters.
        :return: None.
        """
        self.executed_sql.append(operation)
        if self.should_raise_missing_control_pc(operation=operation):
            self._missing_table_failures += 1
            raise psycopg.errors.UndefinedTable('relation "veragrid.control_pc" does not exist')
        else:
            pass

    def executemany(self, operation: str, parameters_seq: Sequence[Sequence[Any]]) -> None:
        """
        Capture one batched SQL operation.

        :param operation: SQL statement.
        :param parameters_seq: Batched positional parameters.
        :return: None.
        """
        self.executed_sql.append(operation)

    def should_raise_missing_control_pc(self, operation: str) -> bool:
        """
        Decide whether this fake cursor must simulate the first missing typed-table read.

        :param operation: SQL statement.
        :return: ``True`` when the statement should fail with ``UndefinedTable``.
        """
        should_raise: bool = (
            self._missing_table_failures == 0
            and "SELECT data" in operation
            and 'FROM "veragrid"."control_pc"' in operation
        )

        return should_raise

    def close(self) -> None:
        """
        Close the fake cursor.

        :return: None.
        """
        pass

    def fetchone(self) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]] | None:
        """
        Return one ModelData payload row for the first payload query.

        :return: Payload row or ``None`` after the first row.
        """
        if self._payload_returned:
            return None
        else:
            self._payload_returned = True
            return (
                {"idtag": "model", "name": "model"},
                {"unix": list(), "prob": list(), "snapshot_unix": None},
                dict(),
            )

    def fetchall(self) -> list[tuple[dict[str, Any]]]:
        """
        Return no typed-object rows.

        :return: Empty row list.
        """
        return list()


def _assert_circuits_equal(grid1: vge.MultiCircuit, grid2: vge.MultiCircuit) -> None:
    """
    Assert semantic circuit equality and print the engine logger on mismatch.

    :param grid1: First circuit.
    :param grid2: Second circuit.
    :return: None.
    """
    equal, logger = grid1.compare_circuits(
        grid2,
        detailed_profile_comparison=True,
        skip_internals=True,
    )

    if not equal:
        logger.print()
    else:
        pass

    assert equal


def _get_local_db_settings() -> PostgreSqlConnectionSettings:
    """
    Return the localhost PostgreSQL settings used by the DB examples.

    :return: PostgreSQL connection settings.
    """
    return PostgreSqlConnectionSettings(
        host="localhost",
        port=5432,
        database="veragrid",
        user_name="admin",
        password="pgpwd",
    )


def _skip_when_local_db_is_unavailable(settings: PostgreSqlConnectionSettings) -> None:
    """
    Skip the test when the expected localhost PostgreSQL instance is unreachable.

    :param settings: PostgreSQL connection settings.
    :return: None.
    """
    try:
        with psycopg.connect(
            host=settings.host,
            port=settings.port,
            dbname="postgres",
            user=settings.user_name,
            password=settings.password,
            connect_timeout=2,
        ) as connection:
            _unused_connection = connection
    except psycopg.Error as exc:
        pytest.skip(f"Local PostgreSQL is not accessible: {exc}")


def test_single_model_db_roundtrip_when_local_db_is_available() -> None:
    """
    Roundtrip one shipped grid through the file and model PostgreSQL store.

    :return: None.
    """
    settings: PostgreSqlConnectionSettings = _get_local_db_settings()
    _skip_when_local_db_is_unavailable(settings=settings)

    source_grid: vge.MultiCircuit = vge.open_file(str(GRID_FOLDER / "case14.gridcal"))
    file_idtag: str = create_file(
        settings=settings,
        file_name="case14_db_roundtrip_file",
        user_idtag="admin",
    )
    model_idtag: str = create_model(
        settings=settings,
        file_idtag=file_idtag,
        model_name="case14_db_roundtrip_model",
    )

    try:
        put_multicircuit_in_database(
            settings=settings,
            circuit=source_grid,
            file_idtag=file_idtag,
            model_idtag=model_idtag,
        )

        loaded_grid: vge.MultiCircuit = get_multicircuit_from_database(
            settings=settings,
            file_idtag=file_idtag,
        )

        _assert_circuits_equal(source_grid, loaded_grid)
    finally:
        delete_file(settings=settings, file_idtag=file_idtag)


def test_schema_creation_seeds_default_admin_user_when_local_db_is_available() -> None:
    """
    Verify that schema bootstrap inserts the default admin user row.

    :return: None.
    """
    settings: PostgreSqlConnectionSettings = _get_local_db_settings()
    _skip_when_local_db_is_unavailable(settings=settings)

    admin_user: dict[str, str] | None = get_user(
        settings=settings,
        user_idtag="admin",
    )

    assert admin_user is not None
    assert admin_user["name"] == "admin"
    assert admin_user["password"] == "veragrid is great"
    assert admin_user["organization_idtag"] == "admin"


def test_normalize_device_table_name_returns_snake_case_names() -> None:
    """
    Verify device labels are normalized into snake_case PostgreSQL table names.

    :return: None.
    """
    assert normalize_device_table_name("Overhead Line Type") == "overhead_line_type"
    assert normalize_device_table_name("HVDCLine") == "hvdc_line"
    assert normalize_device_table_name("Bus 3 Phase") == "bus_3_phase"


def test_all_generated_device_table_names_are_snake_case() -> None:
    """
    Verify the discovered device table catalogue is already snake_case.

    :return: None.
    """
    table_names: list[str] = get_veragrid_object_table_names()

    assert len(table_names) > 0
    assert all(len(table_name) > 0 for table_name in table_names)
    assert all(" " not in table_name for table_name in table_names)
    assert all(table_name == table_name.lower() for table_name in table_names)
    assert all("__" not in table_name for table_name in table_names)


def test_get_model_json_payload_lazily_creates_missing_object_tables() -> None:
    """
    Verify JSON rebuild creates newly-added typed tables only after PostgreSQL reports them missing.

    :return: None.
    """
    cursor: FakeCursor = FakeCursor()

    payload: dict[str, Any] = get_model_json_payload(
        cursor=cursor,
        schema_name="veragrid",
        model_idtag="model",
        table_mappings=(("control_pc", "control_pc"),),
    )

    create_table_index: int = -1
    select_table_indices: list[int] = list()
    sql_index: int
    sql_statement: str
    for sql_index, sql_statement in enumerate(cursor.executed_sql):
        if 'CREATE TABLE IF NOT EXISTS "veragrid"."control_pc"' in sql_statement:
            create_table_index = sql_index
        else:
            pass

        if 'FROM "veragrid"."control_pc"' in sql_statement:
            select_table_indices.append(sql_index)
        else:
            pass

    assert payload["model_data"]["control_pc"] == list()
    assert len(select_table_indices) == 2
    assert create_table_index >= 0
    assert select_table_indices[0] < create_table_index
    assert create_table_index < select_table_indices[1]


def test_multiverse_db_roundtrip_and_file_json_when_local_db_is_available() -> None:
    """
    Roundtrip one multiverse through the database and verify the file JSON view.

    :return: None.
    """
    settings: PostgreSqlConnectionSettings = _get_local_db_settings()
    _skip_when_local_db_is_unavailable(settings=settings)

    base_grid: vge.MultiCircuit = vge.open_file(str(GRID_FOLDER / "lynn5node.gridcal"))
    multiverse: vge.MultiVerse = vge.MultiVerse(base_grid)
    root_node = multiverse.root_nodes[0]
    child_node = multiverse.create_node(
        data=vge.MultiCircuit(name="child scenario"),
        parent_id=root_node.node_id,
        position=root_node.child_count(),
    )
    multiverse.activate_scenario(child_node.node_id)
    multiverse.current_model.lines[0].name = "child_line_override"
    multiverse.commit_current()

    file_idtag: str = create_file(
        settings=settings,
        file_name="lynn5_multiverse_file",
        user_idtag="admin",
    )

    try:
        put_multiverse_in_database(
            settings=settings,
            multiverse=multiverse,
            file_idtag=file_idtag,
            user_idtag="admin",
        )

        loaded_multiverse: vge.MultiVerse = get_multiverse_from_database(
            settings=settings,
            file_idtag=file_idtag,
        )
        loaded_base_grid: vge.MultiCircuit = get_multicircuit_from_database(
            settings=settings,
            file_idtag=file_idtag,
        )
        loaded_child_grid: vge.MultiCircuit = get_multicircuit_from_database(
            settings=settings,
            file_idtag=file_idtag,
            model_idtag=child_node.circuit.idtag,
        )

        _assert_circuits_equal(multiverse.checkout(root_node), loaded_base_grid)
        _assert_circuits_equal(multiverse.checkout(child_node), loaded_child_grid)
        assert loaded_multiverse.roots_number() == 1

        file_json: dict[str, object] | None = get_file_models_json(
            settings=settings,
            file_idtag=file_idtag,
        )
        all_files_json: list[dict[str, object]] = get_files_with_models_json(
            settings=settings,
        )

        assert file_json is not None
        assert file_json["idtag"] == file_idtag
        assert file_json["user"] == "admin"
        assert isinstance(file_json["created_at"], str)
        assert len(file_json["created_at"]) > 0
        assert len(file_json["models"]) == 2
        assert any(
            entry["parent_model_idtag"] is None
            for entry in file_json["models"]
        )
        assert any(
            entry["parent_model_idtag"] == root_node.circuit.idtag
            for entry in file_json["models"]
        )
        assert any(file_entry["idtag"] == file_idtag for file_entry in all_files_json)
    finally:
        delete_file(settings=settings, file_idtag=file_idtag)


def test_get_multicircuit_uses_model_row_idtag_when_payload_idtag_differs() -> None:
    """
    Rebind a loaded circuit to the SQL model idtag when legacy payloads disagree.

    :return: None.
    """
    settings: PostgreSqlConnectionSettings = _get_local_db_settings()
    _skip_when_local_db_is_unavailable(settings=settings)

    source_grid: vge.MultiCircuit = vge.open_file(str(GRID_FOLDER / "case14.gridcal"))
    file_idtag: str = create_file(
        settings=settings,
        file_name="case14_db_payload_idtag_mismatch",
        user_idtag="admin",
    )
    model_idtag: str = create_model(
        settings=settings,
        file_idtag=file_idtag,
        model_name="case14_db_payload_idtag_mismatch_model",
    )

    try:
        put_multicircuit_in_database(
            settings=settings,
            circuit=source_grid,
            file_idtag=file_idtag,
            model_idtag=model_idtag,
        )

        with psycopg.connect(
            host=settings.host,
            port=settings.port,
            dbname=settings.database,
            user=settings.user_name,
            password=settings.password,
        ) as connection:
            cursor = connection.cursor()
            cursor.execute(
                '''
                UPDATE veragrid."ModelData"
                SET circuit = jsonb_set(circuit::jsonb, '{idtag}', %s::jsonb, true)::json
                WHERE model_idtag = %s
                ''',
                (Json("legacy_payload_idtag"), model_idtag),
            )
            connection.commit()
            cursor.close()

        loaded_multiverse: vge.MultiVerse = get_multiverse_from_database(
            settings=settings,
            file_idtag=file_idtag,
        )
        loaded_grid: vge.MultiCircuit = get_multicircuit_from_database(
            settings=settings,
            file_idtag=file_idtag,
            model_idtag=model_idtag,
        )

        assert loaded_multiverse.root_nodes[0].circuit.idtag == model_idtag
        assert loaded_grid.idtag == model_idtag
        _assert_circuits_equal(source_grid, loaded_grid)
    finally:
        delete_file(settings=settings, file_idtag=file_idtag)
