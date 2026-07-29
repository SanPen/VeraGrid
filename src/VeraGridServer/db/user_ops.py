"""
User CRUD operations for the VeraGrid PostgreSQL store.
"""

from __future__ import annotations

from typing import Any, Dict

import psycopg

from VeraGridServer.db.database import (
    CursorLike,
    PostgreSqlConnectionSettings,
    build_connection_kwargs,
    log_database_operation,
    quote_sql_identifier,
)


def ensure_user_row_does_not_exist(cursor: CursorLike,
                                   schema_name: str,
                                   user_idtag: str) -> bool:
    """
    Validate that one user row does not exist before creation.

    :param cursor: Open database cursor.
    :param schema_name: Target schema name.
    :param user_idtag: User identifier.
    :return: ``True`` when the user does not exist yet, ``False`` otherwise.
    """
    quoted_schema_name: str = quote_sql_identifier(schema_name)

    # Create operations must not silently overwrite existing rows, so the
    # check happens before the insert and raises a clear application error.
    log_database_operation(
        f"Checking whether user '{user_idtag}' already exists in '{schema_name}.Users'."
    )
    cursor.execute(
        f'''
        SELECT 1
        FROM {quoted_schema_name}."Users"
        WHERE idtag = %s
        ''',
        (user_idtag,),
    )
    row: Any = cursor.fetchone()

    if row is None:
        return True
    else:
        log_database_operation(
            f"User '{user_idtag}' already exists in schema '{schema_name}', skipping creation."
        )
        return False


def create_user(settings: PostgreSqlConnectionSettings,
                user_idtag: str,
                user_name: str,
                password: str,
                organization_idtag: str) -> None:
    """
    Create one user row.

    :param settings: PostgreSQL connection settings.
    :param user_idtag: User identifier.
    :param user_name: User display name.
    :param password: User password.
    :param organization_idtag: Owning organization identifier.
    :return: None.
    """
    schema_name: str = settings.schema_name
    connection_kwargs: Dict[str, Any] = build_connection_kwargs(settings=settings)
    quoted_schema_name: str = quote_sql_identifier(schema_name)

    log_database_operation(
        f"Connecting to database '{settings.database}' to create user '{user_idtag}'."
    )
    with psycopg.connect(**connection_kwargs) as connection:
        cursor: CursorLike = connection.cursor()
        can_create: bool = ensure_user_row_does_not_exist(
            cursor=cursor,
            schema_name=schema_name,
            user_idtag=user_idtag,
        )
        if can_create:
            cursor.execute(
                f'''
                INSERT INTO {quoted_schema_name}."Users" (idtag, name, password, organization_idtag)
                VALUES (%s, %s, %s, %s)
                ''',
                (user_idtag, user_name, password, organization_idtag),
            )
            connection.commit()
        else:
            pass
        cursor.close()


def get_user(settings: PostgreSqlConnectionSettings,
             user_idtag: str) -> Dict[str, str] | None:
    """
    Read one user row.

    :param settings: PostgreSQL connection settings.
    :param user_idtag: User identifier.
    :return: User row dictionary or ``None``.
    """
    schema_name: str = settings.schema_name
    connection_kwargs: Dict[str, Any] = build_connection_kwargs(settings=settings)
    quoted_schema_name: str = quote_sql_identifier(schema_name)

    log_database_operation(
        f"Connecting to database '{settings.database}' to read user '{user_idtag}'."
    )
    with psycopg.connect(**connection_kwargs) as connection:
        cursor: CursorLike = connection.cursor()
        cursor.execute(
            f'''
            SELECT idtag, name, password, organization_idtag
            FROM {quoted_schema_name}."Users"
            WHERE idtag = %s
            ''',
            (user_idtag,),
        )
        row: Any = cursor.fetchone()
        cursor.close()

    if row is None:
        return None
    else:
        return {
            "idtag": str(row[0]),
            "name": str(row[1]),
            "password": str(row[2]),
            "organization_idtag": str(row[3]),
        }


def get_users_json(settings: PostgreSqlConnectionSettings) -> list[Dict[str, str]]:
    """
    Read every user row as JSON-like dictionaries.

    :param settings: PostgreSQL connection settings.
    :return: Ordered user dictionaries.
    """
    schema_name: str = settings.schema_name
    connection_kwargs: Dict[str, Any] = build_connection_kwargs(settings=settings)
    quoted_schema_name: str = quote_sql_identifier(schema_name)
    users_json: list[Dict[str, str]] = list()

    log_database_operation(
        f"Connecting to database '{settings.database}' to read every user row."
    )
    with psycopg.connect(**connection_kwargs) as connection:
        cursor: CursorLike = connection.cursor()
        cursor.execute(
            f'''
            SELECT idtag, name, organization_idtag
            FROM {quoted_schema_name}."Users"
            ORDER BY organization_idtag, name, idtag
            '''
        )
        rows: Any = cursor.fetchall()
        cursor.close()

    row: Any
    for row in rows:
        users_json.append(
            {
                "idtag": str(row[0]),
                "name": str(row[1]),
                "organization_idtag": str(row[2]),
            }
        )

    return users_json


def get_organizations_json(settings: PostgreSqlConnectionSettings) -> list[Dict[str, str]]:
    """
    Read every organization row as JSON-like dictionaries.

    :param settings: PostgreSQL connection settings.
    :return: Ordered organization dictionaries.
    """
    schema_name: str = settings.schema_name
    connection_kwargs: Dict[str, Any] = build_connection_kwargs(settings=settings)
    quoted_schema_name: str = quote_sql_identifier(schema_name)
    organizations_json: list[Dict[str, str]] = list()

    log_database_operation(
        f"Connecting to database '{settings.database}' to read every organization row."
    )
    with psycopg.connect(**connection_kwargs) as connection:
        cursor: CursorLike = connection.cursor()
        cursor.execute(
            f'''
            SELECT idtag, name
            FROM {quoted_schema_name}."Organization"
            ORDER BY name, idtag
            '''
        )
        rows: Any = cursor.fetchall()
        cursor.close()

    row: Any
    for row in rows:
        organizations_json.append(
            {
                "idtag": str(row[0]),
                "name": str(row[1]),
            }
        )

    return organizations_json


def update_user(settings: PostgreSqlConnectionSettings,
                user_idtag: str,
                user_name: str,
                password: str,
                organization_idtag: str) -> None:
    """
    Update one existing user row.

    :param settings: PostgreSQL connection settings.
    :param user_idtag: User identifier.
    :param user_name: User display name.
    :param password: User password.
    :param organization_idtag: Owning organization identifier.
    :return: None.
    """
    schema_name: str = settings.schema_name
    connection_kwargs: Dict[str, Any] = build_connection_kwargs(settings=settings)
    quoted_schema_name: str = quote_sql_identifier(schema_name)

    log_database_operation(
        f"Connecting to database '{settings.database}' to update user '{user_idtag}'."
    )
    with psycopg.connect(**connection_kwargs) as connection:
        cursor: CursorLike = connection.cursor()
        cursor.execute(
            f'''
            UPDATE {quoted_schema_name}."Users"
            SET name = %s, password = %s, organization_idtag = %s
            WHERE idtag = %s
            ''',
            (user_name, password, organization_idtag, user_idtag),
        )
        connection.commit()
        cursor.close()


def delete_user(settings: PostgreSqlConnectionSettings,
                user_idtag: str,
                cascade: bool = False) -> None:
    """
    Delete one user row, optionally removing its files first.

    :param settings: PostgreSQL connection settings.
    :param user_idtag: User identifier.
    :param cascade: Delete the user's files before deleting the user.
    :return: None.
    """
    schema_name: str = settings.schema_name
    connection_kwargs: Dict[str, Any] = build_connection_kwargs(settings=settings)
    quoted_schema_name: str = quote_sql_identifier(schema_name)

    log_database_operation(
        f"Connecting to database '{settings.database}' to delete user '{user_idtag}'."
    )
    with psycopg.connect(**connection_kwargs) as connection:
        cursor: CursorLike = connection.cursor()

        if cascade:
            log_database_operation(
                f"Cascade deletion enabled for user '{user_idtag}', deleting dependent files first."
            )
            cursor.execute(
                f'''
                DELETE FROM {quoted_schema_name}."Files"
                WHERE "user" = %s
                ''',
                (user_idtag,),
            )
        else:
            pass

        cursor.execute(
            f'''
            DELETE FROM {quoted_schema_name}."Users"
            WHERE idtag = %s
            ''',
            (user_idtag,),
        )
        connection.commit()
        cursor.close()
