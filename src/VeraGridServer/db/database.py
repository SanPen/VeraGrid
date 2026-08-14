"""
Database schema helpers for VeraGridServer.
"""

from __future__ import annotations
import logging
import re
import psycopg
from typing import Any, Dict, List, Protocol, Sequence, Tuple
from VeraGridEngine.Devices.multi_circuit import MultiCircuit


class PostgreSqlConnectionSettings:
    """
    Small container for PostgreSQL connection settings.
    """

    __slots__ = ("host", "port", "database", "user_name", "password", "schema_name")

    def __init__(self,
                 host: str,
                 port: int,
                 database: str,
                 user_name: str,
                 password: str,
                 schema_name: str = "veragrid") -> None:
        """
        Build one PostgreSQL connection settings object.

        :param host: PostgreSQL host name.
        :param port: PostgreSQL port number.
        :param database: Database name.
        :param user_name: Login user name.
        :param password: Login password.
        :param schema_name: Target PostgreSQL schema name.
        :return: None.
        """
        self.host: str = host
        self.port: int = port
        self.database: str = database
        self.user_name: str = user_name
        self.password: str = password
        self.schema_name: str = schema_name


def build_connection_kwargs(settings: PostgreSqlConnectionSettings) -> Dict[str, Any]:
    """
    Convert the settings object into ``psycopg.connect`` keyword arguments.

    :param settings: Localhost PostgreSQL settings.
    :return: Keyword arguments for ``psycopg.connect``.
    """
    connection_kwargs: Dict[str, Any] = dict()

    # This helper preserves the original call surface for existing code paths
    # while the explicit example below shows the exact connection values inline.
    connection_kwargs["host"] = settings.host
    connection_kwargs["port"] = settings.port
    connection_kwargs["dbname"] = settings.database
    connection_kwargs["user"] = settings.user_name
    connection_kwargs["password"] = settings.password

    return connection_kwargs


def normalize_device_table_name(device_name: str) -> str:
    """
    Convert one VeraGrid device label into a PostgreSQL-safe snake_case table name.

    :param device_name: Original device label from the engine catalogue.
    :return: Normalized table name.
    """
    stripped_name: str = device_name.strip()

    # Device labels can contain spaces, dashes, or CamelCase fragments. The
    # first substitution keeps acronym boundaries readable before lowercasing.
    first_pass_name: str = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", stripped_name)

    # The second substitution splits trailing capitals and digits so names such
    # as "HVDCLine" and "Bus3Phase" remain stable after normalization.
    second_pass_name: str = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", first_pass_name)

    # PostgreSQL identifiers should not preserve whitespace or punctuation from
    # the UI label, so every non-alphanumeric run collapses into one underscore.
    collapsed_name: str = re.sub(r"[^0-9A-Za-z]+", "_", second_pass_name)
    normalized_name: str = collapsed_name.strip("_").lower()

    if len(normalized_name) == 0:
        return "device"
    else:
        return normalized_name


def get_veragrid_object_table_name_pairs() -> List[Tuple[str, str]]:
    """
    Inspect ``MultiCircuit`` and return legacy and normalized device table names.

    :return: Ordered list of ``(raw_table_name, normalized_table_name)`` pairs.
    """
    circuit: MultiCircuit = MultiCircuit()
    discovered_names: Dict[str, None] = dict()
    ordered_pairs: List[Tuple[str, str]] = list()

    # The template items are the authoritative list of object kinds supported by
    # the current MultiCircuit implementation, so both legacy and normalized SQL
    # names must be derived from that list instead of a duplicated registry.
    for template_item in circuit.template_items():
        raw_table_name: str = template_item.device_type.value
        normalized_table_name: str = normalize_device_table_name(raw_table_name)

        # Multiple engine aliases can normalize to the same SQL table. The
        # dictionary keeps only the first authoritative raw name per table.
        if normalized_table_name not in discovered_names:
            discovered_names[normalized_table_name] = None
            ordered_pairs.append((raw_table_name, normalized_table_name))
        else:
            pass

    return ordered_pairs


class CursorLike(Protocol):
    """
    Minimal DB-API cursor protocol used by the schema helpers.
    """

    def execute(self, operation: str, parameters: Sequence[Any] | None = None) -> Any:
        """
        Execute one SQL operation.

        :param operation: SQL statement to execute.
        :param parameters: Optional positional parameters.
        :return: Driver-defined execution result.
        """
        ...

    def executemany(self, operation: str, parameters_seq: Sequence[Sequence[Any]]) -> Any:
        """
        Execute one SQL operation against many positional parameter sets.

        :param operation: SQL statement to execute.
        :param parameters_seq: Ordered parameter sequences.
        :return: Driver-defined execution result.
        """
        ...

    def close(self) -> None:
        """
        Close the cursor.

        :return: None.
        """
        ...

    def fetchone(self) -> Any:
        """
        Fetch one row from the previous query.

        :return: Driver-defined row object.
        """
        ...

    def fetchall(self) -> Any:
        """
        Fetch all rows from the previous query.

        :return: Driver-defined row collection.
        """
        ...


class ConnectionLike(Protocol):
    """
    Minimal DB-API connection protocol used by the schema helpers.
    """

    def cursor(self) -> CursorLike:
        """
        Create one cursor.

        :return: Database cursor.
        """
        ...

    def commit(self) -> None:
        """
        Commit the active transaction.

        :return: None.
        """
        ...


def quote_sql_identifier(identifier: str) -> str:
    """
    Quote one SQL identifier for PostgreSQL.

    :param identifier: Raw identifier.
    :return: Double-quoted identifier.
    :raises ValueError: If the identifier is empty.
    """
    if len(identifier) == 0:
        raise ValueError("The SQL identifier cannot be empty")
    else:
        pass

    return '"' + identifier.replace('"', '""') + '"'


def log_database_operation(message: str) -> None:
    """
    Emit one database operation log line to the standard logging system.

    :param message: Operation description to log.
    :return: None.
    """
    logger: logging.Logger = logging.getLogger("VeraGridServer.db")

    # The handler is attached only once so repeated database calls do not emit
    # duplicated lines while still writing to the normal process stderr stream.
    if len(logger.handlers) == 0:
        handler: logging.StreamHandler = logging.StreamHandler()
        formatter: logging.Formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    else:
        pass

    logger.setLevel(logging.INFO)
    logger.propagate = False
    logger.info(message)


def add_column_if_not_exists(cursor: CursorLike,
                             schema_name: str,
                             table_name: str,
                             column_name: str,
                             column_definition: str) -> None:
    """
    Add one column to a table when it is missing.

    :param cursor: Open database cursor.
    :param schema_name: Target schema name.
    :param table_name: Target table name.
    :param column_name: Column name.
    :param column_definition: PostgreSQL column definition.
    :return: None.
    """
    quoted_schema_name: str = quote_sql_identifier(schema_name)
    quoted_table_name: str = quote_sql_identifier(table_name)
    quoted_column_name: str = quote_sql_identifier(column_name)

    log_database_operation(
        f"Ensuring column '{schema_name}.{table_name}.{column_name}' exists."
    )
    cursor.execute(
        f"""
        ALTER TABLE {quoted_schema_name}.{quoted_table_name}
        ADD COLUMN IF NOT EXISTS {quoted_column_name} {column_definition}
        """
    )


def add_constraint_if_not_exists(cursor: CursorLike,
                                 schema_name: str,
                                 table_name: str,
                                 constraint_name: str,
                                 constraint_sql: str) -> None:
    """
    Add one table constraint when it is missing.

    :param cursor: Open database cursor.
    :param schema_name: Target schema name.
    :param table_name: Target table name.
    :param constraint_name: Constraint name.
    :param constraint_sql: SQL fragment after the constraint name.
    :return: None.
    """
    quoted_schema_name: str = quote_sql_identifier(schema_name)
    quoted_table_name: str = quote_sql_identifier(table_name)
    quoted_constraint_name: str = quote_sql_identifier(constraint_name)

    log_database_operation(
        f"Ensuring constraint '{constraint_name}' exists on '{schema_name}.{table_name}'."
    )
    cursor.execute(
        f"""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint AS c
                INNER JOIN pg_class AS t ON c.conrelid = t.oid
                INNER JOIN pg_namespace AS n ON t.relnamespace = n.oid
                WHERE c.conname = '{constraint_name}'
                  AND t.relname = '{table_name}'
                  AND n.nspname = '{schema_name}'
            ) THEN
                ALTER TABLE {quoted_schema_name}.{quoted_table_name}
                ADD CONSTRAINT {quoted_constraint_name}
                {constraint_sql};
            ELSE
                NULL;
            END IF;
        END $$;
        """
    )


def ensure_primary_key_columns(cursor: CursorLike,
                               schema_name: str,
                               table_name: str,
                               constraint_name: str,
                               column_names: Sequence[str]) -> None:
    """
    Ensure one table primary key matches the requested ordered columns.

    :param cursor: Open database cursor.
    :param schema_name: Target schema name.
    :param table_name: Target table name.
    :param constraint_name: Desired primary-key constraint name.
    :param column_names: Ordered primary-key column names.
    :return: None.
    """
    if len(column_names) == 0:
        raise ValueError("At least one primary-key column is required")
    else:
        pass

    quoted_schema_name: str = quote_sql_identifier(schema_name)
    quoted_table_name: str = quote_sql_identifier(table_name)
    quoted_constraint_name: str = quote_sql_identifier(constraint_name)
    expected_columns_sql: str = ", ".join(f"'{column_name}'" for column_name in column_names)
    primary_key_sql: str = ", ".join(quote_sql_identifier(column_name) for column_name in column_names)

    log_database_operation(
        f"Ensuring primary key {tuple(column_names)} exists on '{schema_name}.{table_name}'."
    )
    cursor.execute(
        f"""
        DO $$
        DECLARE
            current_constraint_name TEXT;
            current_columns TEXT[];
        BEGIN
            SELECT
                c.conname,
                array_agg(att.attname ORDER BY ord.ordinality)
            INTO current_constraint_name, current_columns
            FROM pg_constraint AS c
            INNER JOIN pg_class AS t ON c.conrelid = t.oid
            INNER JOIN pg_namespace AS n ON t.relnamespace = n.oid
            INNER JOIN unnest(c.conkey) WITH ORDINALITY AS ord(attnum, ordinality) ON TRUE
            INNER JOIN pg_attribute AS att
                ON att.attrelid = t.oid
               AND att.attnum = ord.attnum
            WHERE c.contype = 'p'
              AND t.relname = '{table_name}'
              AND n.nspname = '{schema_name}'
            GROUP BY c.conname;

            IF current_constraint_name IS NULL THEN
                EXECUTE format(
                    'ALTER TABLE %I.%I ADD CONSTRAINT %I PRIMARY KEY ({primary_key_sql})',
                    '{schema_name}',
                    '{table_name}',
                    '{constraint_name}'
                );
            ELSIF current_columns = ARRAY[{expected_columns_sql}] THEN
                NULL;
            ELSE
                EXECUTE format(
                    'ALTER TABLE %I.%I DROP CONSTRAINT %I',
                    '{schema_name}',
                    '{table_name}',
                    current_constraint_name
                );
                EXECUTE format(
                    'ALTER TABLE %I.%I ADD CONSTRAINT %I PRIMARY KEY ({primary_key_sql})',
                    '{schema_name}',
                    '{table_name}',
                    '{constraint_name}'
                );
            END IF;
        END $$;
        """
    )


def ensure_default_admin_user(cursor: CursorLike,
                              schema_name: str,
                              user_idtag: str = "admin",
                              user_name: str = "admin",
                              user_password: str = "veragrid is great",
                              organization_idtag: str = "admin") -> None:
    """
    Insert the default admin user when it is missing.

    :param cursor: Open database cursor.
    :param schema_name: Target schema name.
    :param user_idtag: Identifier for the seeded user row.
    :param user_name: Display name for the seeded user row.
    :param user_password: Bookkeeping password stored on the seeded user row
        (not used for authentication; the admin console and API only check
        the single instance-level password/API key).
    :param organization_idtag: Identifier of the organization the seeded user belongs to.
    :return: None.
    """
    quoted_schema_name: str = quote_sql_identifier(schema_name)

    # The seeded administrator row gives a fresh schema one known login that
    # can own initial models before any explicit user management happens.
    log_database_operation(
        f"Ensuring default admin user exists in '{schema_name}.Users'."
    )
    cursor.execute(
        f'''
        INSERT INTO {quoted_schema_name}."Users" (idtag, name, password, organization_idtag)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (idtag) DO UPDATE
        SET name = EXCLUDED.name,
            password = EXCLUDED.password,
            organization_idtag = EXCLUDED.organization_idtag
        ''',
        (user_idtag, user_name, user_password, organization_idtag),
    )


def ensure_default_admin_organization(cursor: CursorLike,
                                      schema_name: str,
                                      organization_idtag: str = "admin",
                                      organization_name: str = "admin") -> None:
    """
    Insert the default admin organization when it is missing.

    :param cursor: Open database cursor.
    :param schema_name: Target schema name.
    :param organization_idtag: Identifier for the seeded organization row.
    :param organization_name: Display name for the seeded organization row.
    :return: None.
    """
    quoted_schema_name: str = quote_sql_identifier(schema_name)

    # The seeded administrator user must belong to one stable organization, so
    # the organization row is created before the default user row.
    log_database_operation(
        f"Ensuring default admin organization exists in '{schema_name}.Organization'."
    )
    cursor.execute(
        f'''
        INSERT INTO {quoted_schema_name}."Organization" (idtag, name)
        VALUES (%s, %s)
        ON CONFLICT (idtag) DO NOTHING
        ''',
        (organization_idtag, organization_name),
    )


def ensure_device_table_composite_primary_key(cursor: CursorLike,
                                              schema_name: str,
                                              table_name: str,
                                              constraint_name: str) -> None:
    """
    Ensure one device table uses ``(model_idtag, idtag)`` as its primary key.

    Existing legacy single-column primary keys are replaced in place so the same
    device idtag can appear in different models without colliding.

    :param cursor: Open database cursor.
    :param schema_name: Target schema name.
    :param table_name: Target table name.
    :param constraint_name: Desired primary-key constraint name.
    :return: None.
    """
    ensure_primary_key_columns(
        cursor=cursor,
        schema_name=schema_name,
        table_name=table_name,
        constraint_name=constraint_name,
        column_names=("model_idtag", "idtag"),
    )


def backfill_legacy_model_file_rows(cursor: CursorLike,
                                    schema_name: str) -> None:
    """
    Assign one synthetic file row to each legacy model missing ``file_idtag``.

    :param cursor: Open database cursor.
    :param schema_name: Target schema name.
    :return: None.
    """
    quoted_schema_name: str = quote_sql_identifier(schema_name)

    # Legacy schemas stored standalone models without a file container. The
    # smallest migration is to map each root-level model to its own file id.
    log_database_operation(
        f"Backfilling legacy file rows for models in '{schema_name}.Models'."
    )
    cursor.execute(
        f'''
        INSERT INTO {quoted_schema_name}."Files" (idtag, name)
        SELECT idtag, name
        FROM {quoted_schema_name}."Models"
        WHERE file_idtag IS NULL
        ON CONFLICT (idtag) DO NOTHING
        '''
    )
    cursor.execute(
        f'''
        UPDATE {quoted_schema_name}."Models"
        SET file_idtag = idtag
        WHERE file_idtag IS NULL
        '''
    )


def rename_legacy_device_tables(cursor: CursorLike,
                                schema_name: str,
                                table_name_pairs: Sequence[Tuple[str, str]]) -> None:
    """
    Rename legacy device tables to normalized snake_case names when needed.

    :param cursor: Open database cursor.
    :param schema_name: Target schema name.
    :param table_name_pairs: Ordered ``(raw_name, normalized_name)`` pairs.
    :return: None.
    """
    quoted_schema_name: str = quote_sql_identifier(schema_name)

    # Existing deployments can already contain quoted legacy names such as
    # "Country". Renaming them in place preserves the rows and avoids primary
    # key index collisions when the normalized lowercase table is created.
    for raw_table_name, normalized_table_name in table_name_pairs:
        if raw_table_name == normalized_table_name:
            continue
        else:
            pass

        log_database_operation(
            f"Renaming legacy table '{schema_name}.{raw_table_name}' to "
            f"'{schema_name}.{normalized_table_name}' when required."
        )
        cursor.execute(
            f"""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = '{schema_name}'
                      AND table_name = '{raw_table_name}'
                ) THEN
                    IF EXISTS (
                        SELECT 1
                        FROM information_schema.tables
                        WHERE table_schema = '{schema_name}'
                          AND table_name = '{normalized_table_name}'
                    ) THEN
                        NULL;
                    ELSE
                        EXECUTE format(
                            'ALTER TABLE %I.%I RENAME TO %I',
                            '{schema_name}',
                            '{raw_table_name}',
                            '{normalized_table_name}'
                        );
                    END IF;
                ELSE
                    NULL;
                END IF;
            END $$;
            """
        )


def create_database_if_not_exists(settings: PostgreSqlConnectionSettings,
                                  maintenance_database: str = "postgres") -> bool:
    """
    Create the target PostgreSQL database when it does not exist yet.

    PostgreSQL requires connecting to an existing maintenance database before
    issuing ``CREATE DATABASE``, so this helper uses the provided server and
    credentials but temporarily switches the database name for the check.

    :param settings: Target PostgreSQL connection settings.
    :param maintenance_database: Existing database used to manage databases.
    :return: ``True`` when the database was created, ``False`` otherwise.
    """
    maintenance_settings: PostgreSqlConnectionSettings = PostgreSqlConnectionSettings(
        host=settings.host,
        port=settings.port,
        database=maintenance_database,
        user_name=settings.user_name,
        password=settings.password,
    )
    connection_kwargs: Dict[str, Any] = build_connection_kwargs(settings=maintenance_settings)
    created: bool = False

    # The first connection goes to a maintenance database because PostgreSQL can
    # only create databases from an already existing database context.
    log_database_operation(
        f"Connecting to maintenance database '{maintenance_database}' on "
        f"{settings.host}:{settings.port} to verify database '{settings.database}'."
    )

    # PostgreSQL does not allow CREATE DATABASE inside a transaction, so this
    # management connection must run in autocommit mode.
    with psycopg.connect(autocommit=True, **connection_kwargs) as connection:
        cursor: CursorLike = connection.cursor()

        # The catalog lookup avoids a failing CREATE DATABASE call and keeps the
        # utility re-runnable on machines where the database is already present.
        log_database_operation(
            f"Checking whether database '{settings.database}' already exists."
        )
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (settings.database,),
        )
        row: Any = cursor.fetchone()

        if row is None:
            quoted_database_name: str = quote_sql_identifier(settings.database)
            log_database_operation(
                f"Creating PostgreSQL database '{settings.database}'."
            )
            cursor.execute(f"CREATE DATABASE {quoted_database_name}")
            created = True
        else:
            log_database_operation(
                f"Database '{settings.database}' already exists, skipping creation."
            )
            created = False

        log_database_operation(
            f"Closing maintenance cursor for database '{maintenance_database}'."
        )
        cursor.close()

    return created


def get_veragrid_object_table_names() -> List[str]:
    """
    Inspect ``MultiCircuit`` and return the available VeraGrid object table names.

    The function uses the template device instances declared by ``MultiCircuit``
    so the schema follows the same object catalogue exposed by the engine.

    :return: Ordered list of distinct table names.
    """
    ordered_names: List[str] = list()
    table_name_pairs: List[Tuple[str, str]] = get_veragrid_object_table_name_pairs()

    # The public schema API only exposes normalized table names, but the pair
    # helper keeps the raw labels available for legacy-table migrations.
    for _raw_table_name, normalized_table_name in table_name_pairs:
        ordered_names.append(normalized_table_name)

    return ordered_names


def create_veragrid_schema(settings: PostgreSqlConnectionSettings,
                           seed_default_admin: bool = True,
                           default_admin_org_idtag: str = "admin",
                           default_admin_org_name: str = "admin",
                           default_admin_user_idtag: str = "admin",
                           default_admin_user_name: str = "admin",
                           default_admin_user_password: str = "veragrid is great") -> List[str]:
    """
    Create the PostgreSQL schema used to persist VeraGrid models and objects.

    The created structure is:

    - ``Files`` with ``(idtag, name, user, created_at)``
    - ``Organization`` with ``(idtag, name)``
    - ``Users`` with ``(idtag, name, password, organization_idtag)``
    - ``Models`` with ``(file_idtag, idtag, name, user, parent_model_idtag)``,
      linked to ``Files`` and ``Users``
    - ``ModelData`` with ``(model_idtag, circuit, time, symbolic_data)``,
      linked to ``Models``
    - One table per VeraGrid object type with ``(model_idtag, idtag, data, object_index)``,
      linked to ``Models``

    :param settings: Open DB-API compatible PostgreSQL connection.
    :param seed_default_admin: Whether to (re-)seed the default admin organization/user
        on every startup. Set to ``False`` once a deployment manages its own
        organizations/users, so the built-in "admin"/"admin" row stops reappearing.
    :param default_admin_org_idtag: Identifier for the seeded organization row.
    :param default_admin_org_name: Display name for the seeded organization row.
    :param default_admin_user_idtag: Identifier for the seeded user row.
    :param default_admin_user_name: Display name for the seeded user row.
    :param default_admin_user_password: Bookkeeping password for the seeded user row
        (not used for authentication; see :func:`ensure_default_admin_user`).
    :return: Ordered list of created VeraGrid object table names.
    """
    schema_name: str = settings.schema_name
    created_database: bool = create_database_if_not_exists(settings=settings)
    connection_kwargs: Dict[str, Any] = build_connection_kwargs(settings=settings)

    if created_database:
        log_database_operation(
            f"Database '{settings.database}' was created and is ready for schema setup."
        )
    else:
        log_database_operation(
            f"Database '{settings.database}' already existed, continuing with schema setup."
        )

    # The second connection targets the real application database where the
    # schema and tables must be reconciled.
    log_database_operation(
        f"Connecting to application database '{settings.database}' on "
        f"{settings.host}:{settings.port}."
    )

    # The context manager keeps the example small and ensures the connection is
    # closed even when PostgreSQL rejects the credentials or the network fails.
    with psycopg.connect(**connection_kwargs) as connection:
        cursor: CursorLike = connection.cursor()
        object_table_names: List[str] = get_veragrid_object_table_names()
        table_name_pairs: List[Tuple[str, str]] = get_veragrid_object_table_name_pairs()
        quoted_schema_name: str = quote_sql_identifier(schema_name)

        # The schema boundary isolates the VeraGrid persistence objects from any
        # other application tables and keeps the DDL idempotent across deployments.
        log_database_operation(
            f"Creating schema '{schema_name}' if it does not exist."
        )
        cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {quoted_schema_name}")
        rename_legacy_device_tables(
            cursor=cursor,
            schema_name=schema_name,
            table_name_pairs=table_name_pairs,
        )

        # Organizations own users. The default admin organization is seeded
        # before the default admin user so the FK target already exists.
        log_database_operation(
            f"Creating table '{schema_name}.Organization' if it does not exist."
        )
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {quoted_schema_name}."Organization" (
                idtag TEXT PRIMARY KEY,
                name TEXT NOT NULL
            )
            """
        )
        add_column_if_not_exists(cursor, schema_name, "Organization", "idtag", "TEXT")
        add_column_if_not_exists(cursor, schema_name, "Organization", "name", "TEXT")
        if seed_default_admin:
            ensure_default_admin_organization(
                cursor=cursor,
                schema_name=schema_name,
                organization_idtag=default_admin_org_idtag,
                organization_name=default_admin_org_name,
            )
        else:
            pass

        # Users are owned by organizations and later own files.
        log_database_operation(
            f"Creating table '{schema_name}.Users' if it does not exist."
        )
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {quoted_schema_name}."Users" (
                idtag TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                password TEXT NOT NULL,
                organization_idtag TEXT NOT NULL,
                CONSTRAINT users_organization_fk
                    FOREIGN KEY (organization_idtag)
                    REFERENCES {quoted_schema_name}."Organization"(idtag)
                    ON DELETE RESTRICT
            )
            """
        )
        add_column_if_not_exists(cursor, schema_name, "Users", "idtag", "TEXT")
        add_column_if_not_exists(cursor, schema_name, "Users", "name", "TEXT")
        add_column_if_not_exists(cursor, schema_name, "Users", "password", "TEXT")
        add_column_if_not_exists(cursor, schema_name, "Users", "organization_idtag", "TEXT")
        add_constraint_if_not_exists(
            cursor=cursor,
            schema_name=schema_name,
            table_name="Users",
            constraint_name="users_organization_fk",
            constraint_sql=(
                f'FOREIGN KEY (organization_idtag) REFERENCES {quoted_schema_name}."Organization"(idtag) '
                f'ON DELETE RESTRICT'
            ),
        )
        if seed_default_admin:
            ensure_default_admin_user(
                cursor=cursor,
                schema_name=schema_name,
                user_idtag=default_admin_user_idtag,
                user_name=default_admin_user_name,
                user_password=default_admin_user_password,
                organization_idtag=default_admin_org_idtag,
            )
        else:
            pass

        # Files are the top-level persisted artifacts. A file can contain one base
        # model plus optional delta models that together form one MultiVerse.
        log_database_operation(
            f"Creating table '{schema_name}.Files' if it does not exist."
        )
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {quoted_schema_name}."Files" (
                idtag TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                "user" TEXT,
                CONSTRAINT files_user_fk
                    FOREIGN KEY ("user")
                    REFERENCES {quoted_schema_name}."Users"(idtag)
                    ON DELETE RESTRICT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        add_column_if_not_exists(cursor, schema_name, "Files", "idtag", "TEXT")
        add_column_if_not_exists(cursor, schema_name, "Files", "name", "TEXT")
        add_column_if_not_exists(cursor, schema_name, "Files", "user", "TEXT")
        add_column_if_not_exists(
            cursor,
            schema_name,
            "Files",
            "created_at",
            "TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP",
        )
        add_constraint_if_not_exists(
            cursor=cursor,
            schema_name=schema_name,
            table_name="Files",
            constraint_name="files_user_fk",
            constraint_sql=(
                f'FOREIGN KEY ("user") REFERENCES {quoted_schema_name}."Users"(idtag) '
                f'ON DELETE RESTRICT'
            ),
        )

        # Models hold the logical grid/container metadata. The "user" column name is
        # kept exactly as requested, and quoted because PostgreSQL treats USER as
        # a special keyword. The composite key attaches each model to one file.
        log_database_operation(
            f"Creating table '{schema_name}.Models' if it does not exist."
        )
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {quoted_schema_name}."Models" (
                file_idtag TEXT NOT NULL,
                idtag TEXT NOT NULL,
                name TEXT NOT NULL,
                parent_model_idtag TEXT,
                CONSTRAINT models_pkey
                    PRIMARY KEY (file_idtag, idtag),
                CONSTRAINT models_idtag_key
                    UNIQUE (idtag),
                CONSTRAINT models_file_fk
                    FOREIGN KEY (file_idtag)
                    REFERENCES {quoted_schema_name}."Files"(idtag)
                    ON DELETE CASCADE,
                CONSTRAINT models_parent_model_fk
                    FOREIGN KEY (parent_model_idtag)
                    REFERENCES {quoted_schema_name}."Models"(idtag)
                    ON DELETE SET NULL
            )
            """
        )
        add_column_if_not_exists(cursor, schema_name, "Models", "file_idtag", "TEXT")
        add_column_if_not_exists(cursor, schema_name, "Models", "idtag", "TEXT")
        add_column_if_not_exists(cursor, schema_name, "Models", "name", "TEXT")
        add_column_if_not_exists(cursor, schema_name, "Models", "parent_model_idtag", "TEXT")
        cursor.execute(
            f'ALTER TABLE {quoted_schema_name}."Models" ALTER COLUMN file_idtag SET NOT NULL'
        )
        add_constraint_if_not_exists(
            cursor=cursor,
            schema_name=schema_name,
            table_name="Models",
            constraint_name="models_file_idtag_idtag_key",
            constraint_sql="UNIQUE (file_idtag, idtag)",
        )
        add_constraint_if_not_exists(
            cursor=cursor,
            schema_name=schema_name,
            table_name="Models",
            constraint_name="models_idtag_key",
            constraint_sql="UNIQUE (idtag)",
        )
        add_constraint_if_not_exists(
            cursor=cursor,
            schema_name=schema_name,
            table_name="Models",
            constraint_name="models_file_fk",
            constraint_sql=(
                f'FOREIGN KEY (file_idtag) REFERENCES {quoted_schema_name}."Files"(idtag) '
                f'ON DELETE CASCADE'
            ),
        )
        add_constraint_if_not_exists(
            cursor=cursor,
            schema_name=schema_name,
            table_name="Models",
            constraint_name="models_parent_model_fk",
            constraint_sql=(
                f'FOREIGN KEY (parent_model_idtag) REFERENCES {quoted_schema_name}."Models"(idtag) '
                f'ON DELETE SET NULL'
            ),
        )

        # The typed object tables do not carry the global circuit/time/symbolic
        # payload that VeraGrid needs to rebuild a full MultiCircuit, so that
        # payload is stored once per model in a dedicated companion table.
        log_database_operation(
            f"Creating table '{schema_name}.ModelData' if it does not exist."
        )
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {quoted_schema_name}."ModelData" (
                model_idtag TEXT PRIMARY KEY,
                circuit JSONB NOT NULL,
                time JSONB NOT NULL,
                symbolic_data JSONB,
                CONSTRAINT model_data_model_fk
                    FOREIGN KEY (model_idtag)
                    REFERENCES {quoted_schema_name}."Models"(idtag)
                    ON DELETE CASCADE
            )
            """
        )
        add_column_if_not_exists(cursor, schema_name, "ModelData", "model_idtag", "TEXT")
        add_column_if_not_exists(cursor, schema_name, "ModelData", "circuit", "JSONB")
        add_column_if_not_exists(cursor, schema_name, "ModelData", "time", "JSONB")
        add_column_if_not_exists(cursor, schema_name, "ModelData", "symbolic_data", "JSONB")
        add_constraint_if_not_exists(
            cursor=cursor,
            schema_name=schema_name,
            table_name="ModelData",
            constraint_name="model_data_model_fk",
            constraint_sql=(
                f'FOREIGN KEY (model_idtag) REFERENCES {quoted_schema_name}."Models"(idtag) '
                f'ON DELETE CASCADE'
            ),
        )

        # Each VeraGrid object type gets its own payload table. The payload is kept
        # as JSONB so the object structure can evolve without forcing a table redesign
        # for every engine-side property change.
        for table_name in object_table_names:
            quoted_table_name: str = quote_sql_identifier(table_name)
            constraint_name: str = f"{table_name}_model_fk".lower().replace(" ", "_")
            primary_key_name: str = f"{table_name}_pkey".lower().replace(" ", "_")

            log_database_operation(
                f"Creating table '{schema_name}.{table_name}' if it does not exist."
            )
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {quoted_schema_name}.{quoted_table_name} (
                    model_idtag TEXT NOT NULL,
                    idtag TEXT NOT NULL,
                    data JSONB NOT NULL,
                    object_index INTEGER NOT NULL,
                    CONSTRAINT {quote_sql_identifier(primary_key_name)}
                        PRIMARY KEY (model_idtag, idtag),
                    CONSTRAINT {quote_sql_identifier(constraint_name)}
                        FOREIGN KEY (model_idtag)
                        REFERENCES {quoted_schema_name}."Models"(idtag)
                        ON DELETE CASCADE
                )
                """
            )
            add_column_if_not_exists(cursor, schema_name, table_name, "idtag", "TEXT")
            add_column_if_not_exists(cursor, schema_name, table_name, "data", "JSONB")
            add_column_if_not_exists(cursor, schema_name, table_name, "object_index", "INTEGER")
            add_column_if_not_exists(cursor, schema_name, table_name, "model_idtag", "TEXT")
            ensure_device_table_composite_primary_key(
                cursor=cursor,
                schema_name=schema_name,
                table_name=table_name,
                constraint_name=primary_key_name,
            )
            add_constraint_if_not_exists(
                cursor=cursor,
                schema_name=schema_name,
                table_name=table_name,
                constraint_name=constraint_name,
                constraint_sql=(
                    f'FOREIGN KEY (model_idtag) REFERENCES {quoted_schema_name}."Models"(idtag) '
                    f'ON DELETE CASCADE'
                ),
            )

        log_database_operation(
            f"Committing schema changes for database '{settings.database}'."
        )
        connection.commit()
        log_database_operation(
            f"Closing schema cursor for database '{settings.database}'."
        )
        cursor.close()

    return object_table_names
