"""
File and model persistence operations for the VeraGrid PostgreSQL store.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple
from uuid import uuid4

import psycopg
from psycopg.types.json import Json

from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Devices.multiverse import MultiVerse, ScenarioNode
from VeraGridEngine.IO.veragrid.pack_unpack import (
    gather_model_as_jsons,
    get_objects_dictionary,
    parse_veragrid_data,
)
from VeraGridServer.db.database import (
    CursorLike,
    PostgreSqlConnectionSettings,
    build_connection_kwargs,
    get_veragrid_object_table_names,
    log_database_operation,
    normalize_device_table_name,
    quote_sql_identifier,
)
from VeraGridServer.settings import settings as server_settings


def get_supported_table_mappings() -> List[Tuple[str, str]]:
    """
    Build the serializer-bucket to SQL-table mapping supported by the schema.

    :return: Ordered list of ``(json_key, table_name)`` pairs.
    """
    object_types: Dict[str, Any] = get_objects_dictionary()
    available_table_names: set[str] = set(get_veragrid_object_table_names())
    mappings: List[Tuple[str, str]] = list()

    # The serializer still exposes one legacy branch bucket that is not backed
    # by a dedicated SQL table in the current schema, so it must be skipped.
    if "branch" in object_types:
        del object_types["branch"]
    else:
        pass

    # Only buckets backed by physical tables can be persisted safely.
    for json_key, template_elm in object_types.items():
        raw_table_name: str = template_elm.device_type.value
        table_name: str = normalize_device_table_name(raw_table_name)

        if table_name in available_table_names:
            mappings.append((json_key, table_name))
        else:
            log_database_operation(
                f"Skipping serializer bucket '{json_key}' because table '{table_name}' "
                f"(from device label '{raw_table_name}') is not present in the schema."
            )

    return mappings


def acquire_database_file_lock(settings: PostgreSqlConnectionSettings,
                               file_idtag: str) -> None:
    """
    Acquire the process-local mutex for one stored file write path.

    :param settings: PostgreSQL connection settings.
    :param file_idtag: Stored file identifier.
    :return: None.
    """
    server_settings.acquire_database_file_lock(
        schema_name=settings.schema_name,
        file_idtag=file_idtag,
    )


def release_database_file_lock(settings: PostgreSqlConnectionSettings,
                               file_idtag: str) -> None:
    """
    Release the process-local mutex for one stored file write path.

    :param settings: PostgreSQL connection settings.
    :param file_idtag: Stored file identifier.
    :return: None.
    """
    server_settings.release_database_file_lock(
        schema_name=settings.schema_name,
        file_idtag=file_idtag,
    )


def row_exists(cursor: CursorLike,
               schema_name: str,
               table_name: str,
               where_sql: str,
               parameters: Tuple[Any, ...]) -> bool:
    """
    Check whether one row exists in a table.

    :param cursor: Open database cursor.
    :param schema_name: Target schema name.
    :param table_name: Target table name.
    :param where_sql: SQL condition without the ``WHERE`` keyword.
    :param parameters: Positional parameters for the condition.
    :return: ``True`` when the row exists, ``False`` otherwise.
    """
    quoted_schema_name: str = quote_sql_identifier(schema_name)
    quoted_table_name: str = quote_sql_identifier(table_name)

    cursor.execute(
        f"""
        SELECT 1
        FROM {quoted_schema_name}.{quoted_table_name}
        WHERE {where_sql}
        """,
        parameters,
    )
    row: Any = cursor.fetchone()

    if row is None:
        return False
    else:
        return True


def resolve_circuit_idtag(cursor: CursorLike,
                          schema_name: str,
                          file_idtag: str,
                          circuit: MultiCircuit) -> str:
    """
    Ensure one circuit has a stable idtag, scoped to this file, and return it.

    A circuit loaded from disk often already carries an idtag from whenever it (or a
    template/ancestor it was saved-as from) was first created. Reusing that idtag is
    correct across re-saves of THIS SAME file - that is the "stable" this function is
    named for - but the ``Models`` table also enforces ``UNIQUE (idtag)`` regardless of
    file, because every per-device-type table's foreign key references ``Models(idtag)``
    directly. Two files derived from a common template carry the identical circuit
    idtag, so blindly reusing it made the second file's upload fail against that
    constraint even though the two files are otherwise unrelated. Mint a fresh idtag
    only when the existing one is blank, or already claimed by a DIFFERENT file;
    otherwise reuse it exactly as before.

    :param cursor: Open database cursor.
    :param schema_name: Target schema name.
    :param file_idtag: File this circuit is being persisted into.
    :param circuit: Circuit to inspect.
    :return: Stable circuit identifier, unique across every file in the schema.
    """
    current_idtag: Any = circuit.idtag
    current_text: str = "" if current_idtag is None else str(current_idtag).strip()

    if len(current_text) == 0:
        resolved_idtag: str = str(uuid4())
    else:
        quoted_schema_name: str = quote_sql_identifier(schema_name)
        cursor.execute(
            f'''
            SELECT file_idtag
            FROM {quoted_schema_name}."Models"
            WHERE idtag = %s
            ''',
            (current_text,),
        )
        owner_row: Any = cursor.fetchone()

        if owner_row is None or str(owner_row[0]) == file_idtag:
            resolved_idtag = current_text
        else:
            log_database_operation(
                f"Circuit idtag '{current_text}' already belongs to file '{owner_row[0]}' "
                f"(not '{file_idtag}') - minting a fresh idtag instead of colliding with it."
            )
            resolved_idtag = str(uuid4())

    circuit.idtag = resolved_idtag
    return resolved_idtag


def ensure_file_row_exists(cursor: CursorLike,
                           schema_name: str,
                           file_idtag: str) -> None:
    """
    Validate that one file row already exists.

    :param cursor: Open database cursor.
    :param schema_name: Target schema name.
    :param file_idtag: File identifier to validate.
    :return: None.
    """
    quoted_schema_name: str = quote_sql_identifier(schema_name)

    log_database_operation(
        f"Checking whether file '{file_idtag}' exists in '{schema_name}.Files'."
    )
    cursor.execute(
        f'SELECT 1 FROM {quoted_schema_name}."Files" WHERE idtag = %s',
        (file_idtag,),
    )
    row: Any = cursor.fetchone()

    if row is None:
        raise ValueError(f"File '{file_idtag}' does not exist in schema '{schema_name}'")
    else:
        pass


def get_file_owner_idtag(cursor: CursorLike,
                         schema_name: str,
                         file_idtag: str) -> str:
    """
    Read the owning user identifier for one file.

    :param cursor: Open database cursor.
    :param schema_name: Target schema name.
    :param file_idtag: File identifier.
    :return: Owning user identifier.
    """
    quoted_schema_name: str = quote_sql_identifier(schema_name)

    cursor.execute(
        f'''
        SELECT "user"
        FROM {quoted_schema_name}."Files"
        WHERE idtag = %s
        ''',
        (file_idtag,),
    )
    row: Any = cursor.fetchone()

    if row is None:
        raise ValueError(f"File '{file_idtag}' does not exist in schema '{schema_name}'")
    elif row[0] is None:
        raise ValueError(f"File '{file_idtag}' does not have an owning user in schema '{schema_name}'")
    else:
        return str(row[0])


def upsert_file_row(cursor: CursorLike,
                    schema_name: str,
                    file_idtag: str,
                    file_name: str,
                    user_idtag: str) -> None:
    """
    Insert or update one file metadata row.

    :param cursor: Open database cursor.
    :param schema_name: Target schema name.
    :param file_idtag: File identifier.
    :param file_name: Human-readable file name.
    :param user_idtag: Owning user identifier.
    :return: None.
    """
    quoted_schema_name: str = quote_sql_identifier(schema_name)

    # File-level saves own the top-level artifact metadata, so the row is
    # upserted before any child model rows are rewritten.
    log_database_operation(
        f"Upserting file '{file_idtag}' into '{schema_name}.Files'."
    )
    cursor.execute(
        f'''
        INSERT INTO {quoted_schema_name}."Files" (idtag, name, "user")
        VALUES (%s, %s, %s)
        ON CONFLICT (idtag) DO UPDATE
        SET name = EXCLUDED.name, "user" = EXCLUDED."user"
        ''',
        (file_idtag, file_name, user_idtag),
    )


def ensure_model_row_exists(cursor: CursorLike,
                            schema_name: str,
                            file_idtag: str,
                            model_idtag: str) -> None:
    """
    Validate that one model row already exists before storing objects into it.

    :param cursor: Open database cursor.
    :param schema_name: Target schema name.
    :param file_idtag: Parent file identifier.
    :param model_idtag: Model identifier to validate.
    :return: None.
    """
    quoted_schema_name: str = quote_sql_identifier(schema_name)

    # Object rows depend on the model metadata row, so the validation happens
    # before any payload write to avoid orphaned persistence rows.
    log_database_operation(
        f"Checking whether model '{model_idtag}' exists in '{schema_name}.Models' for file '{file_idtag}'."
    )
    cursor.execute(
        f'''
        SELECT 1
        FROM {quoted_schema_name}."Models"
        WHERE file_idtag = %s AND idtag = %s
        ''',
        (file_idtag, model_idtag),
    )
    row: Any = cursor.fetchone()

    if row is None:
        raise ValueError(
            f"Model '{model_idtag}' does not exist in file '{file_idtag}' within schema '{schema_name}'"
        )
    else:
        pass


def ensure_model_row_does_not_exist(cursor: CursorLike,
                                    schema_name: str,
                                    file_idtag: str,
                                    model_idtag: str) -> bool:
    """
    Validate that one model row does not exist before creation.

    :param cursor: Open database cursor.
    :param schema_name: Target schema name.
    :param file_idtag: Parent file identifier.
    :param model_idtag: Model identifier to validate.
    :return: ``True`` when the model does not exist yet, ``False`` otherwise.
    """
    quoted_schema_name: str = quote_sql_identifier(schema_name)

    log_database_operation(
        f"Checking whether model '{model_idtag}' already exists in '{schema_name}.Models' for file '{file_idtag}'."
    )
    cursor.execute(
        f'''
        SELECT 1
        FROM {quoted_schema_name}."Models"
        WHERE file_idtag = %s AND idtag = %s
        ''',
        (file_idtag, model_idtag),
    )
    row: Any = cursor.fetchone()

    if row is None:
        return True
    else:
        log_database_operation(
            f"Model '{model_idtag}' already exists in file '{file_idtag}', skipping creation."
        )
        return False


def create_file(settings: PostgreSqlConnectionSettings,
                file_name: str,
                user_idtag: str,
                file_idtag: str | None = None) -> str:
    """
    Create one file row and return its identifier.

    :param settings: PostgreSQL connection settings.
    :param file_name: Human-readable file name.
    :param user_idtag: Owning user identifier.
    :param file_idtag: Optional pre-existing file identifier.
    :return: File identifier.
    """
    schema_name: str = settings.schema_name
    resolved_file_idtag: str
    if file_idtag is None:
        resolved_file_idtag = str(uuid4())
    else:
        resolved_file_idtag = file_idtag

    connection_kwargs: Dict[str, Any] = build_connection_kwargs(settings=settings)
    quoted_schema_name: str = quote_sql_identifier(schema_name)

    log_database_operation(
        f"Connecting to database '{settings.database}' to create file '{resolved_file_idtag}'."
    )
    with psycopg.connect(**connection_kwargs) as connection:
        cursor: CursorLike = connection.cursor()
        upsert_file_row(
            cursor=cursor,
            schema_name=schema_name,
            file_idtag=resolved_file_idtag,
            file_name=file_name,
            user_idtag=user_idtag,
        )
        connection.commit()
        cursor.close()

    return resolved_file_idtag


def get_file(settings: PostgreSqlConnectionSettings,
             file_idtag: str) -> Dict[str, str] | None:
    """
    Read one file row.

    :param settings: PostgreSQL connection settings.
    :param file_idtag: File identifier.
    :return: File row dictionary or ``None``.
    """
    schema_name: str = settings.schema_name
    connection_kwargs: Dict[str, Any] = build_connection_kwargs(settings=settings)
    quoted_schema_name: str = quote_sql_identifier(schema_name)

    log_database_operation(
        f"Connecting to database '{settings.database}' to read file '{file_idtag}'."
    )
    with psycopg.connect(**connection_kwargs) as connection:
        cursor: CursorLike = connection.cursor()
        cursor.execute(
            f'''
            SELECT idtag, name, "user", created_at
            FROM {quoted_schema_name}."Files"
            WHERE idtag = %s
            ''',
            (file_idtag,),
        )
        row: Any = cursor.fetchone()
        cursor.close()

    if row is None:
        return None
    else:
        return {
            "idtag": str(row[0]),
            "name": str(row[1]),
            "user": str(row[2]),
            "created_at": str(row[3]),
        }


def create_model(settings: PostgreSqlConnectionSettings,
                 file_idtag: str,
                 model_name: str,
                 parent_model_idtag: str | None = None,
                 model_idtag: str | None = None) -> str:
    """
    Create one model row inside one file and return its identifier.

    :param settings: PostgreSQL connection settings.
    :param file_idtag: Parent file identifier.
    :param model_name: Human-readable model name.
    :param parent_model_idtag: Optional parent model identifier.
    :param model_idtag: Optional pre-existing model identifier.
    :return: Model identifier.
    """
    schema_name: str = settings.schema_name
    resolved_model_idtag: str
    if model_idtag is None:
        resolved_model_idtag = str(uuid4())
    else:
        resolved_model_idtag = model_idtag

    acquire_database_file_lock(settings=settings, file_idtag=file_idtag)

    try:
        connection_kwargs: Dict[str, Any] = build_connection_kwargs(settings=settings)
        quoted_schema_name: str = quote_sql_identifier(schema_name)

        log_database_operation(
            f"Connecting to database '{settings.database}' to create model '{resolved_model_idtag}' in file '{file_idtag}'."
        )
        with psycopg.connect(**connection_kwargs) as connection:
            cursor: CursorLike = connection.cursor()
            ensure_file_row_exists(cursor=cursor, schema_name=schema_name, file_idtag=file_idtag)
            can_create: bool = ensure_model_row_does_not_exist(
                cursor=cursor,
                schema_name=schema_name,
                file_idtag=file_idtag,
                model_idtag=resolved_model_idtag,
            )
            if can_create:
                log_database_operation(
                    f"Inserting model '{resolved_model_idtag}' into '{schema_name}.Models' for file '{file_idtag}'."
                )
                cursor.execute(
                    f'''
                    INSERT INTO {quoted_schema_name}."Models" (file_idtag, idtag, name, parent_model_idtag)
                    VALUES (%s, %s, %s, %s)
                    ''',
                    (file_idtag, resolved_model_idtag, model_name, parent_model_idtag),
                )
                connection.commit()
            else:
                pass
            cursor.close()
    finally:
        release_database_file_lock(settings=settings, file_idtag=file_idtag)

    return resolved_model_idtag


def get_model(settings: PostgreSqlConnectionSettings,
              file_idtag: str,
              model_idtag: str) -> Dict[str, str | None] | None:
    """
    Read one model row.

    :param settings: PostgreSQL connection settings.
    :param file_idtag: Parent file identifier.
    :param model_idtag: Model identifier.
    :return: Model row dictionary or ``None``.
    """
    schema_name: str = settings.schema_name
    connection_kwargs: Dict[str, Any] = build_connection_kwargs(settings=settings)
    quoted_schema_name: str = quote_sql_identifier(schema_name)

    log_database_operation(
        f"Connecting to database '{settings.database}' to read model '{model_idtag}' from file '{file_idtag}'."
    )
    with psycopg.connect(**connection_kwargs) as connection:
        cursor: CursorLike = connection.cursor()
        cursor.execute(
            f'''
            SELECT file_idtag, idtag, name, parent_model_idtag
            FROM {quoted_schema_name}."Models"
            WHERE file_idtag = %s AND idtag = %s
            ''',
            (file_idtag, model_idtag),
        )
        row: Any = cursor.fetchone()
        cursor.close()

    if row is None:
        return None
    else:
        return {
            "file_idtag": str(row[0]),
            "idtag": str(row[1]),
            "name": str(row[2]),
            "parent_model_idtag": None if row[3] is None else str(row[3]),
        }


def update_model(settings: PostgreSqlConnectionSettings,
                 file_idtag: str,
                 model_idtag: str,
                 model_name: str,
                 parent_model_idtag: str | None = None) -> None:
    """
    Update one existing model row.

    :param settings: PostgreSQL connection settings.
    :param file_idtag: Parent file identifier.
    :param model_idtag: Model identifier.
    :param model_name: Human-readable model name.
    :param parent_model_idtag: Optional parent model identifier.
    :return: None.
    """
    schema_name: str = settings.schema_name
    acquire_database_file_lock(settings=settings, file_idtag=file_idtag)

    try:
        connection_kwargs: Dict[str, Any] = build_connection_kwargs(settings=settings)
        quoted_schema_name: str = quote_sql_identifier(schema_name)

        log_database_operation(
            f"Connecting to database '{settings.database}' to update model '{model_idtag}' in file '{file_idtag}'."
        )
        with psycopg.connect(**connection_kwargs) as connection:
            cursor: CursorLike = connection.cursor()
            cursor.execute(
                f'''
                UPDATE {quoted_schema_name}."Models"
                SET name = %s, parent_model_idtag = %s
                WHERE file_idtag = %s AND idtag = %s
                ''',
                (model_name, parent_model_idtag, file_idtag, model_idtag),
            )
            connection.commit()
            cursor.close()
    finally:
        release_database_file_lock(settings=settings, file_idtag=file_idtag)


def delete_file(settings: PostgreSqlConnectionSettings,
                file_idtag: str) -> None:
    """
    Delete one file row and its dependent models.

    :param settings: PostgreSQL connection settings.
    :param file_idtag: File identifier.
    :return: None.
    """
    schema_name: str = settings.schema_name
    acquire_database_file_lock(settings=settings, file_idtag=file_idtag)

    try:
        connection_kwargs: Dict[str, Any] = build_connection_kwargs(settings=settings)
        quoted_schema_name: str = quote_sql_identifier(schema_name)

        log_database_operation(
            f"Connecting to database '{settings.database}' to delete file '{file_idtag}'."
        )
        with psycopg.connect(**connection_kwargs) as connection:
            cursor: CursorLike = connection.cursor()
            cursor.execute(
                f'''
                DELETE FROM {quoted_schema_name}."Files"
                WHERE idtag = %s
                ''',
                (file_idtag,),
            )
            connection.commit()
            cursor.close()
    finally:
        release_database_file_lock(settings=settings, file_idtag=file_idtag)


def delete_model(settings: PostgreSqlConnectionSettings,
                 file_idtag: str,
                 model_idtag: str,
                 cascade: bool = False) -> None:
    """
    Delete one model row, optionally removing child models first.

    :param settings: PostgreSQL connection settings.
    :param file_idtag: Parent file identifier.
    :param model_idtag: Model identifier.
    :param cascade: Delete child models before deleting this model.
    :return: None.
    """
    schema_name: str = settings.schema_name
    acquire_database_file_lock(settings=settings, file_idtag=file_idtag)

    try:
        connection_kwargs: Dict[str, Any] = build_connection_kwargs(settings=settings)
        quoted_schema_name: str = quote_sql_identifier(schema_name)

        log_database_operation(
            f"Connecting to database '{settings.database}' to delete model '{model_idtag}' from file '{file_idtag}'."
        )
        with psycopg.connect(**connection_kwargs) as connection:
            cursor: CursorLike = connection.cursor()

            if cascade:
                log_database_operation(
                    f"Cascade deletion enabled for model '{model_idtag}' in file '{file_idtag}', deleting child models first."
                )
                cursor.execute(
                    f'''
                    DELETE FROM {quoted_schema_name}."Models"
                    WHERE file_idtag = %s AND parent_model_idtag = %s
                    ''',
                    (file_idtag, model_idtag),
                )
            else:
                pass

            cursor.execute(
                f'''
                DELETE FROM {quoted_schema_name}."Models"
                WHERE file_idtag = %s AND idtag = %s
                ''',
                (file_idtag, model_idtag),
            )
            connection.commit()
            cursor.close()
    finally:
        release_database_file_lock(settings=settings, file_idtag=file_idtag)


def delete_existing_model_object_rows(cursor: CursorLike,
                                      schema_name: str,
                                      table_mappings: Sequence[Tuple[str, str]],
                                      model_idtag: str) -> None:
    """
    Remove the previous object snapshot for one model from all supported tables.

    :param cursor: Open database cursor.
    :param schema_name: Target schema name.
    :param table_mappings: Serializer-to-table mappings to clear.
    :param model_idtag: Model identifier whose snapshot must be replaced.
    :return: None.
    """
    quoted_schema_name: str = quote_sql_identifier(schema_name)

    # Replacing the old snapshot first prevents stale rows from surviving when
    # devices were removed from the MultiCircuit between saves.
    for json_key, table_name in table_mappings:
        quoted_table_name: str = quote_sql_identifier(table_name)

        log_database_operation(
            f"Deleting previous rows for model '{model_idtag}' from '{schema_name}.{table_name}' (bucket '{json_key}')."
        )
        cursor.execute(
            f"DELETE FROM {quoted_schema_name}.{quoted_table_name} WHERE model_idtag = %s",
            (model_idtag,),
        )


def insert_model_object_rows(cursor: CursorLike,
                             schema_name: str,
                             table_mappings: Sequence[Tuple[str, str]],
                             model_data: Dict[str, Any],
                             model_idtag: str) -> None:
    """
    Insert one full MultiCircuit object snapshot into the typed object tables.

    :param cursor: Open database cursor.
    :param schema_name: Target schema name.
    :param table_mappings: Serializer-to-table mappings to fill.
    :param model_data: Packed model JSON dictionary from VeraGrid.
    :param model_idtag: Parent model identifier.
    :return: None.
    """
    quoted_schema_name: str = quote_sql_identifier(schema_name)

    # Each bucket contains homogeneous JSON objects already serialized by the
    # engine, so one batched upsert per table is enough and avoids one SQL round
    # trip per object row.
    for json_key, table_name in table_mappings:
        quoted_table_name: str = quote_sql_identifier(table_name)
        entries: Any = model_data.get(json_key, list())

        if isinstance(entries, list):
            row_count: int = len(entries)
        else:
            row_count = 0

        log_database_operation(
            f"Inserting {row_count} rows into '{schema_name}.{table_name}' from serializer bucket '{json_key}'."
        )

        if isinstance(entries, list) and row_count > 0:
            batch_parameters: List[Tuple[str, Json, int, str]] = list()
            object_index: int
            entry: Dict[str, Any]
            for object_index, entry in enumerate(entries):
                object_idtag: str = str(entry["idtag"])
                batch_parameters.append((object_idtag, Json(entry), object_index, model_idtag))

            cursor.executemany(
                f"""
                INSERT INTO {quoted_schema_name}.{quoted_table_name} (idtag, data, object_index, model_idtag)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (model_idtag, idtag) DO UPDATE
                SET data = EXCLUDED.data,
                    object_index = EXCLUDED.object_index
                """,
                batch_parameters,
            )
        else:
            pass


def insert_model_metadata_rows(cursor: CursorLike,
                               schema_name: str,
                               file_idtag: str,
                               nodes: Sequence[ScenarioNode]) -> None:
    """
    Insert the model metadata rows for one full multiverse save in one batch.

    :param cursor: Open database cursor.
    :param schema_name: Target schema name.
    :param file_idtag: Parent file identifier.
    :param nodes: Ordered multiverse nodes to persist.
    :return: None.
    """
    quoted_schema_name: str = quote_sql_identifier(schema_name)
    batch_parameters: List[Tuple[str, str, str, str | None]] = list()
    node: ScenarioNode

    for node in nodes:
        model_idtag: str = resolve_circuit_idtag(
            cursor=cursor, schema_name=schema_name, file_idtag=file_idtag, circuit=node.circuit
        )
        model_name_raw: str | None = node.circuit.name
        model_name: str
        if model_name_raw is None or len(model_name_raw.strip()) == 0:
            model_name = model_idtag
        else:
            model_name = model_name_raw

        parent_model_idtag: str | None
        if node.parent is None:
            parent_model_idtag = None
        else:
            parent_model_idtag = resolve_circuit_idtag(
                cursor=cursor, schema_name=schema_name, file_idtag=file_idtag,
                circuit=node.parent.circuit,
            )

        batch_parameters.append((file_idtag, model_idtag, model_name, parent_model_idtag))

    if len(batch_parameters) > 0:
        log_database_operation(
            f"Inserting {len(batch_parameters)} rows into '{schema_name}.Models' for file '{file_idtag}'."
        )
        cursor.executemany(
            f'''
            INSERT INTO {quoted_schema_name}."Models" (file_idtag, idtag, name, parent_model_idtag)
            VALUES (%s, %s, %s, %s)
            ''',
            batch_parameters,
        )
    else:
        pass


def upsert_model_payload_row(cursor: CursorLike,
                             schema_name: str,
                             model_data: Dict[str, Any],
                             symbolic_data: Dict[str, Any],
                             model_idtag: str) -> None:
    """
    Store the non-typed payload needed to rebuild one MultiCircuit.

    :param cursor: Open database cursor.
    :param schema_name: Target schema name.
    :param model_data: Packed model JSON dictionary from VeraGrid.
    :param symbolic_data: Packed symbolic JSON dictionary from VeraGrid.
    :param model_idtag: Parent model identifier.
    :return: None.
    """
    quoted_schema_name: str = quote_sql_identifier(schema_name)
    circuit_data: Dict[str, Any] = model_data["circuit"]
    time_data: Dict[str, Any] = model_data["time"]

    log_database_operation(
        f"Upserting payload row into '{schema_name}.ModelData' for model '{model_idtag}'."
    )
    exists: bool = row_exists(
        cursor=cursor,
        schema_name=schema_name,
        table_name="ModelData",
        where_sql="model_idtag = %s",
        parameters=(model_idtag,),
    )

    if exists:
        cursor.execute(
            f'''
            UPDATE {quoted_schema_name}."ModelData"
            SET circuit = %s, time = %s, symbolic_data = %s
            WHERE model_idtag = %s
            ''',
            (
                Json(circuit_data),
                Json(time_data),
                Json(symbolic_data),
                model_idtag,
            ),
        )
    else:
        cursor.execute(
            f'''
            INSERT INTO {quoted_schema_name}."ModelData" (model_idtag, circuit, time, symbolic_data)
            VALUES (%s, %s, %s, %s)
            ''',
            (
                model_idtag,
                Json(circuit_data),
                Json(time_data),
                Json(symbolic_data),
            ),
        )


def get_model_payload_row(cursor: CursorLike,
                          schema_name: str,
                          model_idtag: str) -> Dict[str, Any]:
    """
    Read the stored non-typed payload for one model.

    :param cursor: Open database cursor.
    :param schema_name: Target schema name.
    :param model_idtag: Model identifier.
    :return: Payload dictionary with ``circuit``, ``time``, and ``symbolic_data``.
    """
    quoted_schema_name: str = quote_sql_identifier(schema_name)

    log_database_operation(
        f"Reading payload row from '{schema_name}.ModelData' for model '{model_idtag}'."
    )
    cursor.execute(
        f'''
        SELECT circuit, time, symbolic_data
        FROM {quoted_schema_name}."ModelData"
        WHERE model_idtag = %s
        ''',
        (model_idtag,),
    )
    row: Any = cursor.fetchone()

    if row is None:
        log_database_operation(
            f"No payload row exists in '{schema_name}.ModelData' for model '{model_idtag}', falling back to typed tables only."
        )
        cursor.execute(
            f'''
            SELECT name
            FROM {quoted_schema_name}."Models"
            WHERE idtag = %s
            ''',
            (model_idtag,),
        )
        model_row: Any = cursor.fetchone()
        model_name: str
        if model_row is None:
            model_name = model_idtag
        else:
            model_name = str(model_row[0])

        return {
            "circuit": {
                "idtag": model_idtag,
                "name": model_name,
            },
            "time": {
                "unix": list(),
                "prob": list(),
                "snapshot_unix": None,
            },
            "symbolic_data": dict(),
        }
    else:
        return {
            "circuit": row[0],
            "time": row[1],
            "symbolic_data": dict() if row[2] is None else row[2],
        }


def get_model_json_payload(cursor: CursorLike,
                           schema_name: str,
                           model_idtag: str,
                           table_mappings: Sequence[Tuple[str, str]]) -> Dict[str, Any]:
    """
    Rebuild the VeraGrid JSON bundle for one model from SQL storage.

    :param cursor: Open database cursor.
    :param schema_name: Target schema name.
    :param model_idtag: Model identifier.
    :param table_mappings: Serializer-to-table mappings to read.
    :return: Dictionary compatible with ``parse_veragrid_data``.
    """
    quoted_schema_name: str = quote_sql_identifier(schema_name)
    payload_row: Dict[str, Any] = get_model_payload_row(
        cursor=cursor,
        schema_name=schema_name,
        model_idtag=model_idtag,
    )
    model_data: Dict[str, Any] = dict()

    model_data["circuit"] = payload_row["circuit"]
    model_data["time"] = payload_row["time"]

    for json_key, table_name in table_mappings:
        quoted_table_name: str = quote_sql_identifier(table_name)

        log_database_operation(
            f"Reading rows from '{schema_name}.{table_name}' for model '{model_idtag}'."
        )
        cursor.execute(
            f'''
            SELECT data
            FROM {quoted_schema_name}.{quoted_table_name}
            WHERE model_idtag = %s
            ORDER BY object_index
            ''',
            (model_idtag,),
        )
        rows: Any = cursor.fetchall()
        model_data[json_key] = [row[0] for row in rows]

    return {
        "model_data": model_data,
        "symbolic_data": payload_row["symbolic_data"],
    }


def get_file_model_rows(cursor: CursorLike,
                        schema_name: str,
                        file_idtag: str) -> List[Dict[str, str | None]]:
    """
    Read all model metadata rows for one file.

    :param cursor: Open database cursor.
    :param schema_name: Target schema name.
    :param file_idtag: File identifier.
    :return: Ordered model metadata rows.
    """
    quoted_schema_name: str = quote_sql_identifier(schema_name)

    log_database_operation(
        f"Reading model metadata rows for file '{file_idtag}' from '{schema_name}.Models'."
    )
    cursor.execute(
        f'''
        SELECT file_idtag, idtag, name, parent_model_idtag
        FROM {quoted_schema_name}."Models"
        WHERE file_idtag = %s
        ORDER BY parent_model_idtag NULLS FIRST, idtag
        ''',
        (file_idtag,),
    )
    rows: Any = cursor.fetchall()
    model_rows: List[Dict[str, str | None]] = list()

    for row in rows:
        model_rows.append(
            {
                "file_idtag": str(row[0]),
                "idtag": str(row[1]),
                "name": str(row[2]),
                "parent_model_idtag": None if row[3] is None else str(row[3]),
            }
        )

    return model_rows


def get_base_model_idtag_for_file(cursor: CursorLike,
                                  schema_name: str,
                                  file_idtag: str) -> str:
    """
    Resolve the base model identifier for one file.

    :param cursor: Open database cursor.
    :param schema_name: Target schema name.
    :param file_idtag: File identifier.
    :return: Base model identifier.
    """
    model_rows: List[Dict[str, str | None]] = get_file_model_rows(
        cursor=cursor,
        schema_name=schema_name,
        file_idtag=file_idtag,
    )
    base_model_rows: List[Dict[str, str | None]] = list()

    for model_row in model_rows:
        if model_row["parent_model_idtag"] is None:
            base_model_rows.append(model_row)
        else:
            pass

    if len(base_model_rows) == 1:
        return str(base_model_rows[0]["idtag"])
    elif len(base_model_rows) == 0:
        raise ValueError(f"File '{file_idtag}' does not contain a base model")
    else:
        raise ValueError(f"File '{file_idtag}' contains more than one base model")


def find_model_node(multiverse: MultiVerse,
                    model_idtag: str) -> ScenarioNode:
    """
    Find one multiverse node by its circuit idtag.

    :param multiverse: Loaded multiverse.
    :param model_idtag: Target model identifier.
    :return: Matching scenario node.
    """
    node: ScenarioNode
    for node in multiverse.iter_nodes_depth_first():
        if node.circuit.idtag == model_idtag:
            return node
        else:
            pass

    raise ValueError(f"Model '{model_idtag}' was not found in the loaded multiverse")


def put_multicircuit_in_database(settings: PostgreSqlConnectionSettings,
                                 circuit: MultiCircuit,
                                 file_idtag: str,
                                 model_idtag: str,
                                 project_directory: Path | None = None) -> None:
    """
    Persist one ``MultiCircuit`` snapshot into the typed VeraGrid SQL tables.

    :param settings: PostgreSQL connection settings.
    :param circuit: VeraGrid circuit to persist.
    :param file_idtag: Parent file identifier.
    :param model_idtag: Existing parent model identifier.
    :param project_directory: Optional project directory for the serializer.
    :return: None.
    """
    schema_name: str = settings.schema_name
    acquire_database_file_lock(settings=settings, file_idtag=file_idtag)

    try:
        connection_kwargs: Dict[str, Any] = build_connection_kwargs(settings=settings)
        packed_model: Dict[str, Any] = gather_model_as_jsons(
            circuit=circuit,
            project_directory=project_directory,
        )
        model_data: Dict[str, Any] = packed_model["model_data"]
        symbolic_data: Dict[str, Any] = packed_model["symbolic_data"]
        table_mappings: List[Tuple[str, str]] = get_supported_table_mappings()

        log_database_operation(
            f"Connecting to database '{settings.database}' to persist MultiCircuit into model '{model_idtag}' from file '{file_idtag}'."
        )
        with psycopg.connect(**connection_kwargs) as connection:
            cursor: CursorLike = connection.cursor()

            ensure_model_row_exists(
                cursor=cursor,
                schema_name=schema_name,
                file_idtag=file_idtag,
                model_idtag=model_idtag,
            )

            delete_existing_model_object_rows(
                cursor=cursor,
                schema_name=schema_name,
                table_mappings=table_mappings,
                model_idtag=model_idtag,
            )

            insert_model_object_rows(
                cursor=cursor,
                schema_name=schema_name,
                table_mappings=table_mappings,
                model_data=model_data,
                model_idtag=model_idtag,
            )

            upsert_model_payload_row(
                cursor=cursor,
                schema_name=schema_name,
                model_data=model_data,
                symbolic_data=symbolic_data,
                model_idtag=model_idtag,
            )

            connection.commit()
            cursor.close()
    finally:
        release_database_file_lock(settings=settings, file_idtag=file_idtag)


def put_multiverse_in_database(settings: PostgreSqlConnectionSettings,
                               multiverse: MultiVerse,
                               file_idtag: str,
                               user_idtag: str,
                               file_name: str | None = None,
                               project_directory: Path | None = None) -> None:
    """
    Persist one ``MultiVerse`` into one file row and its child model rows.

    :param settings: PostgreSQL connection settings.
    :param multiverse: VeraGrid multiverse to persist.
    :param file_idtag: Parent file identifier.
    :param user_idtag: Owning user identifier for every stored model row.
    :param file_name: Optional file name override.
    :param project_directory: Optional project directory for the serializer.
    :return: None.
    """
    schema_name: str = settings.schema_name
    acquire_database_file_lock(settings=settings, file_idtag=file_idtag)

    try:
        connection_kwargs: Dict[str, Any] = build_connection_kwargs(settings=settings)
        table_mappings: List[Tuple[str, str]] = get_supported_table_mappings()

        multiverse.commit_current()
        nodes: List[ScenarioNode] = list(multiverse.iter_nodes_depth_first())

        if len(nodes) == 0:
            raise ValueError("The MultiVerse does not contain any models to persist")
        else:
            pass

        resolved_file_name: str
        if file_name is None:
            root_name: str | None = nodes[0].circuit.name
            if root_name is None or len(root_name.strip()) == 0:
                resolved_file_name = file_idtag
            else:
                resolved_file_name = root_name
        else:
            resolved_file_name = file_name

        # The file save rewrites the complete model tree so stale child rows are
        # removed once, up front, and then recreated in current tree order.
        log_database_operation(
            f"Connecting to database '{settings.database}' to persist MultiVerse into file '{file_idtag}'."
        )
        with psycopg.connect(**connection_kwargs) as connection:
            cursor: CursorLike = connection.cursor()
            upsert_file_row(
                cursor=cursor,
                schema_name=schema_name,
                file_idtag=file_idtag,
                file_name=resolved_file_name,
                user_idtag=user_idtag,
            )

            quoted_schema_name: str = quote_sql_identifier(schema_name)
            cursor.execute(
                f'''
                DELETE FROM {quoted_schema_name}."Models"
                WHERE file_idtag = %s
                ''',
                (file_idtag,),
            )
            insert_model_metadata_rows(
                cursor=cursor,
                schema_name=schema_name,
                file_idtag=file_idtag,
                nodes=nodes,
            )

            for node in nodes:
                model_idtag = resolve_circuit_idtag(
                    cursor=cursor, schema_name=schema_name, file_idtag=file_idtag,
                    circuit=node.circuit,
                )
                packed_model: Dict[str, Any] = gather_model_as_jsons(
                    circuit=node.circuit,
                    project_directory=project_directory,
                )
                model_data: Dict[str, Any] = packed_model["model_data"]
                symbolic_data: Dict[str, Any] = packed_model["symbolic_data"]

                insert_model_object_rows(
                    cursor=cursor,
                    schema_name=schema_name,
                    table_mappings=table_mappings,
                    model_data=model_data,
                    model_idtag=model_idtag,
                )
                upsert_model_payload_row(
                    cursor=cursor,
                    schema_name=schema_name,
                    model_data=model_data,
                    symbolic_data=symbolic_data,
                    model_idtag=model_idtag,
                )

            connection.commit()
            cursor.close()
    finally:
        release_database_file_lock(settings=settings, file_idtag=file_idtag)


def _coerce_ints_to_floats(node: Any) -> Any:
    """
    Recursively coerce ``int`` leaves to ``float`` inside one JSON value.

    PostgreSQL's ``jsonb`` type normalizes whole-number-valued floats (e.g.
    ``-5.76e+16``) into bare integer literals on storage/retrieval. Python's
    ``json`` module then parses those literals back as native ``int``, and a
    numpy array built from a list mixing ``int`` and ``float`` can silently
    fall back to ``dtype=object`` once an ``int`` exceeds the exact-integer
    range of ``int64``. ``VeraGridEngine``'s ``AdmittanceMatrix`` requires a
    strict complex dtype and raises on that ``object`` array, so any
    sufficiently large admittance value round-tripped through this database
    fails to load. This is a database round-trip workaround, not a fix for
    whatever produced the oversized admittance values in the first place.

    :param node: JSON-decoded value (dict, list, or scalar).
    :return: Same structure with every non-bool ``int`` leaf converted to ``float``.
    """
    if isinstance(node, dict):
        return {key: _coerce_ints_to_floats(value) for key, value in node.items()}
    elif isinstance(node, list):
        return [_coerce_ints_to_floats(value) for value in node]
    elif isinstance(node, bool):
        # bool is a subclass of int, and JSON booleans must stay booleans.
        return node
    elif isinstance(node, int):
        return float(node)
    else:
        return node


def _sanitize_admittance_matrix_payload(packed_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Defensively coerce ``values_r``/``values_i`` leaves to ``float`` throughout one packed payload.

    See :func:`_coerce_ints_to_floats` for why this is necessary. Scoped to
    only these two key names so nothing else in the payload (sizes, indices,
    booleans, enums) is touched.

    :param packed_payload: Packed model JSON dictionary as read from the database.
    :return: Same structure with every ``values_r``/``values_i`` leaf coerced to ``float``.
    """
    if isinstance(packed_payload, dict):
        sanitized: Dict[str, Any] = dict()
        key: str
        value: Any
        for key, value in packed_payload.items():
            if key in ("values_r", "values_i"):
                sanitized[key] = _coerce_ints_to_floats(value)
            else:
                sanitized[key] = _sanitize_admittance_matrix_payload(value)
        return sanitized
    elif isinstance(packed_payload, list):
        return [_sanitize_admittance_matrix_payload(item) for item in packed_payload]
    else:
        return packed_payload


def get_multiverse_from_database(settings: PostgreSqlConnectionSettings,
                                 file_idtag: str,
                                 project_directory: Path | None = None) -> MultiVerse:
    """
    Retrieve one stored file and rebuild it as a ``MultiVerse``.

    :param settings: PostgreSQL connection settings.
    :param file_idtag: File identifier.
    :param project_directory: Optional project directory for path resolution.
    :return: Rebuilt ``MultiVerse`` instance.
    """
    schema_name: str = settings.schema_name
    connection_kwargs: Dict[str, Any] = build_connection_kwargs(settings=settings)
    table_mappings: List[Tuple[str, str]] = get_supported_table_mappings()

    log_database_operation(
        f"Connecting to database '{settings.database}' to rebuild MultiVerse for file '{file_idtag}'."
    )
    with psycopg.connect(**connection_kwargs) as connection:
        cursor: CursorLike = connection.cursor()
        ensure_file_row_exists(cursor=cursor, schema_name=schema_name, file_idtag=file_idtag)
        model_rows: List[Dict[str, str | None]] = get_file_model_rows(
            cursor=cursor,
            schema_name=schema_name,
            file_idtag=file_idtag,
        )
        circuit_by_model_idtag: Dict[str, MultiCircuit] = dict()

        model_row: Dict[str, str | None]
        for model_row in model_rows:
            model_idtag: str = str(model_row["idtag"])
            packed_payload: Dict[str, Any] = get_model_json_payload(
                cursor=cursor,
                schema_name=schema_name,
                model_idtag=model_idtag,
                table_mappings=table_mappings,
            )
            packed_payload = _sanitize_admittance_matrix_payload(packed_payload)
            # The SQL model row is the stable scenario identity. Some legacy
            # payloads still store a different circuit idtag inside ModelData,
            # so the parsed circuit must be rebound to the model row idtag
            # before the multiverse tree is rebuilt.
            loaded_circuit: MultiCircuit = parse_veragrid_data(
                data=packed_payload,
                project_directory=project_directory,
            )
            loaded_circuit.idtag = model_idtag
            circuit_by_model_idtag[model_idtag] = loaded_circuit

        cursor.close()

    multiverse: MultiVerse = MultiVerse()
    node_by_model_idtag: Dict[str, ScenarioNode] = dict()
    pending_rows: List[Dict[str, str | None]] = list(model_rows)

    while len(pending_rows) > 0:
        progressed: bool = False
        next_pending_rows: List[Dict[str, str | None]] = list()

        for model_row in pending_rows:
            model_idtag = str(model_row["idtag"])
            parent_model_idtag = model_row["parent_model_idtag"]

            if parent_model_idtag is None:
                parent_node_id: int | None = None
            elif parent_model_idtag in node_by_model_idtag:
                parent_node_id = node_by_model_idtag[parent_model_idtag].node_id
            else:
                parent_node_id = -1

            if parent_node_id == -1:
                next_pending_rows.append(model_row)
            else:
                node: ScenarioNode = multiverse.create_node(
                    data=circuit_by_model_idtag[model_idtag],
                    parent_id=parent_node_id,
                    position=None,
                )
                node_by_model_idtag[model_idtag] = node
                progressed = True

        if progressed:
            pending_rows = next_pending_rows
        else:
            raise ValueError(f"Could not resolve parent links for file '{file_idtag}'")

    if multiverse.roots_number() > 0:
        root_node: ScenarioNode = multiverse.root_nodes[0]
        multiverse.activate_scenario(root_node.node_id)
    else:
        raise ValueError(f"File '{file_idtag}' does not contain any stored models")

    return multiverse


def get_multicircuit_from_database(settings: PostgreSqlConnectionSettings,
                                   file_idtag: str,
                                   model_idtag: str | None = None,
                                   project_directory: Path | None = None) -> MultiCircuit:
    """
    Retrieve one stored model as a composed ``MultiCircuit``.

    When ``model_idtag`` is omitted, the base model for the file is returned.

    :param settings: PostgreSQL connection settings.
    :param file_idtag: File identifier.
    :param model_idtag: Optional model identifier.
    :param project_directory: Optional project directory for path resolution.
    :return: Rebuilt composed ``MultiCircuit`` instance.
    """
    multiverse: MultiVerse = get_multiverse_from_database(
        settings=settings,
        file_idtag=file_idtag,
        project_directory=project_directory,
    )

    resolved_model_idtag: str
    if model_idtag is None:
        root_node: ScenarioNode = multiverse.root_nodes[0]
        resolved_model_idtag = str(root_node.circuit.idtag)
    else:
        resolved_model_idtag = model_idtag

    target_node: ScenarioNode = find_model_node(
        multiverse=multiverse,
        model_idtag=resolved_model_idtag,
    )
    return multiverse.checkout(target_node)


def get_file_models_json(settings: PostgreSqlConnectionSettings,
                         file_idtag: str) -> Dict[str, Any] | None:
    """
    Read one file with its model metadata as JSON-like dictionaries.

    :param settings: PostgreSQL connection settings.
    :param file_idtag: File identifier.
    :return: File dictionary with nested model rows, or ``None``.
    """
    schema_name: str = settings.schema_name
    connection_kwargs: Dict[str, Any] = build_connection_kwargs(settings=settings)

    log_database_operation(
        f"Connecting to database '{settings.database}' to read file-model JSON for file '{file_idtag}'."
    )
    with psycopg.connect(**connection_kwargs) as connection:
        cursor: CursorLike = connection.cursor()
        file_row: Dict[str, str] | None = get_file(
            settings=settings,
            file_idtag=file_idtag,
        )

        if file_row is None:
            cursor.close()
            return None
        else:
            pass

        model_rows: List[Dict[str, str | None]] = get_file_model_rows(
            cursor=cursor,
            schema_name=schema_name,
            file_idtag=file_idtag,
        )
        cursor.close()

    return {
        "idtag": file_row["idtag"],
        "name": file_row["name"],
        "user": file_row["user"],
        "created_at": file_row["created_at"],
        "models": [
            {
                "idtag": str(model_row["idtag"]),
                "name": str(model_row["name"]),
                "parent_model_idtag": None if model_row["parent_model_idtag"] is None else str(model_row["parent_model_idtag"]),
                "is_base_model": model_row["parent_model_idtag"] is None,
            }
            for model_row in model_rows
        ],
    }


def get_files_with_models_json(settings: PostgreSqlConnectionSettings) -> List[Dict[str, Any]]:
    """
    Read every file and the models it contains as JSON-like dictionaries.

    :param settings: PostgreSQL connection settings.
    :return: Ordered list of file dictionaries with nested model rows.
    """
    schema_name: str = settings.schema_name
    connection_kwargs: Dict[str, Any] = build_connection_kwargs(settings=settings)
    quoted_schema_name: str = quote_sql_identifier(schema_name)
    files_json: List[Dict[str, Any]] = list()

    log_database_operation(
        f"Connecting to database '{settings.database}' to read all file-model JSON rows."
    )
    with psycopg.connect(**connection_kwargs) as connection:
        cursor: CursorLike = connection.cursor()
        cursor.execute(
            f'''
            SELECT idtag, name, "user", created_at
            FROM {quoted_schema_name}."Files"
            ORDER BY name, idtag
            '''
        )
        file_rows: Any = cursor.fetchall()

        file_row: Any
        for file_row in file_rows:
            file_idtag: str = str(file_row[0])
            model_rows: List[Dict[str, str | None]] = get_file_model_rows(
                cursor=cursor,
                schema_name=schema_name,
                file_idtag=file_idtag,
            )
            files_json.append(
                {
                    "idtag": file_idtag,
                    "name": str(file_row[1]),
                    "user": str(file_row[2]),
                    "created_at": str(file_row[3]),
                    "models": [
                        {
                            "idtag": str(model_row["idtag"]),
                            "name": str(model_row["name"]),
                            "parent_model_idtag": None if model_row["parent_model_idtag"] is None else str(model_row["parent_model_idtag"]),
                            "is_base_model": model_row["parent_model_idtag"] is None,
                        }
                        for model_row in model_rows
                    ],
                }
            )

        cursor.close()

    return files_json
