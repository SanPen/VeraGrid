# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations
from collections import deque
import hashlib
import hmac
import html
import logging
from math import ceil
import os
from pathlib import Path
import tempfile
from typing import Any, Dict, List
from urllib.parse import parse_qs, unquote, urlencode
from uuid import uuid4

import psycopg
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from VeraGridEngine.IO.file_open import FileOpen
from VeraGridServer.db.database import (
    build_connection_kwargs,
    quote_sql_identifier,
)
from VeraGridServer.db.model_ops import (
    create_file,
    create_model,
    delete_file,
    delete_model,
    put_multicircuit_in_database,
    put_multiverse_in_database,
    update_model,
)
from VeraGridServer.db.user_ops import (
    create_user,
    delete_user,
    get_user,
    update_user,
)
from VeraGridServer.endpoints.jobs import JOBS_LIST
from VeraGridServer.endpoints.register_sub_servers import registered_services
from VeraGridServer.settings import settings


router = APIRouter()

ADMIN_COOKIE_NAME: str = "veragrid_admin_session"
LOG_BUFFER_MAXLEN: int = 4000
LOG_BUFFER: deque[Dict[str, str]] = deque(maxlen=LOG_BUFFER_MAXLEN)
ADMIN_HANDLER_NAME: str = "veragrid_admin_buffer_handler"


class AdminBufferLogHandler(logging.Handler):
    """
    Keep a bounded in-memory copy of recent log records for the admin page.
    """

    def emit(self, record: logging.LogRecord) -> None:
        """
        Store one formatted log record into the ring buffer.

        :param record: Logging record to store.
        :return: None.
        """
        timestamp_text: str = self.formatTime(record=record)
        LOG_BUFFER.appendleft(
            {
                "timestamp": timestamp_text,
                "logger": record.name,
                "level": record.levelname,
                "message": record.getMessage(),
            }
        )

    def formatTime(self, record: logging.LogRecord) -> str:
        """
        Format one record timestamp.

        :param record: Logging record to inspect.
        :return: Timestamp text.
        """
        formatter: logging.Formatter = logging.Formatter()
        return formatter.formatTime(record=record, datefmt="%Y-%m-%d %H:%M:%S")


def ensure_admin_log_handler() -> None:
    """
    Attach the in-memory admin log handler once.

    :return: None.
    """
    root_logger: logging.Logger = logging.getLogger()

    handler: logging.Handler
    for handler in root_logger.handlers:
        if getattr(handler, "name", "") == ADMIN_HANDLER_NAME:
            return
        else:
            pass

    buffer_handler: AdminBufferLogHandler = AdminBufferLogHandler()
    buffer_handler.set_name(ADMIN_HANDLER_NAME)
    buffer_handler.setLevel(logging.INFO)
    root_logger.addHandler(buffer_handler)


ensure_admin_log_handler()


def get_admin_cookie_value() -> str:
    """
    Build the expected admin session cookie value from the configured password.

    :return: Expected session cookie value.
    """
    secret_text: str = settings.this_password
    digest: str = hmac.new(
        key=secret_text.encode("utf-8"),
        msg=b"veragrid-admin-session",
        digestmod=hashlib.sha256,
    ).hexdigest()
    return digest


def is_admin_request_authenticated(request: Request) -> bool:
    """
    Check whether one request already carries a valid admin session cookie.

    :param request: Incoming HTTP request.
    :return: ``True`` when the request is authenticated, ``False`` otherwise.
    """
    if len(settings.this_password) == 0:
        return False
    else:
        pass

    provided_cookie: str | None = request.cookies.get(ADMIN_COOKIE_NAME, None)

    if provided_cookie is None:
        return False
    else:
        return hmac.compare_digest(provided_cookie, get_admin_cookie_value())


def require_admin_request(request: Request) -> RedirectResponse | None:
    """
    Validate one admin request and redirect to login when not authenticated.

    :param request: Incoming HTTP request.
    :return: Redirect response or ``None`` when authenticated.
    """
    if is_admin_request_authenticated(request=request):
        return None
    else:
        return RedirectResponse(url="/admin/login", status_code=303)


def get_database_settings_or_none():
    """
    Resolve the configured database settings when available.

    :return: PostgreSQL settings or ``None``.
    """
    return settings.get_database_settings()


def parse_request_form(request_body: bytes) -> Dict[str, str]:
    """
    Parse one URL-encoded request body into a simple string dictionary.

    :param request_body: Raw request body bytes.
    :return: Parsed single-value form fields.
    """
    parsed_form: Dict[str, List[str]] = parse_qs(request_body.decode("utf-8"))
    result: Dict[str, str] = dict()
    key_text: str
    values: List[str]

    for key_text, values in parsed_form.items():
        if len(values) > 0:
            result[key_text] = values[0]
        else:
            result[key_text] = ""

    return result


def get_query_text(request: Request,
                   key_text: str,
                   default_value: str = "") -> str:
    """
    Read one query parameter as stripped text.

    :param request: Incoming HTTP request.
    :param key_text: Query parameter name.
    :param default_value: Fallback text.
    :return: Query text.
    """
    raw_value: str | None = request.query_params.get(key_text, None)

    if raw_value is None:
        return default_value
    else:
        return raw_value.strip()


def get_query_int(request: Request,
                  key_text: str,
                  default_value: int,
                  minimum_value: int,
                  maximum_value: int) -> int:
    """
    Read one bounded integer query parameter.

    :param request: Incoming HTTP request.
    :param key_text: Query parameter name.
    :param default_value: Fallback integer.
    :param minimum_value: Inclusive lower bound.
    :param maximum_value: Inclusive upper bound.
    :return: Bounded integer value.
    """
    raw_value: str | None = request.query_params.get(key_text, None)

    if raw_value is None:
        candidate_value: int = default_value
    else:
        try:
            candidate_value = int(raw_value)
        except ValueError:
            candidate_value = default_value

    if candidate_value < minimum_value:
        return minimum_value
    elif candidate_value > maximum_value:
        return maximum_value
    else:
        return candidate_value


def build_admin_url(section: str,
                    page: int = 1,
                    page_size: int = 50,
                    query_text: str = "",
                    message: str = "") -> str:
    """
    Build one admin URL with the common paging and message parameters.

    :param section: Admin section name.
    :param page: 1-based page number.
    :param page_size: Rows per page.
    :param query_text: Search text.
    :param message: Optional flash message.
    :return: Admin URL.
    """
    params: Dict[str, str] = dict()
    params["section"] = section
    params["page"] = str(page)
    params["page_size"] = str(page_size)

    if len(query_text) > 0:
        params["q"] = query_text
    else:
        pass

    if len(message) > 0:
        params["msg"] = message
    else:
        pass

    return "/admin?" + urlencode(params)


def get_search_clause(query_text: str,
                      column_names: List[str]) -> tuple[str, List[Any]]:
    """
    Build one SQL search clause for ``ILIKE`` filtering across several columns.

    :param query_text: Search text.
    :param column_names: Column names to search.
    :return: SQL clause and positional parameters.
    """
    if len(query_text) == 0:
        return "", list()
    else:
        pass

    conditions: List[str] = list()
    parameters: List[Any] = list()
    like_pattern: str = "%" + query_text + "%"
    column_name: str

    for column_name in column_names:
        conditions.append(f"{column_name} ILIKE %s")
        parameters.append(like_pattern)

    return " WHERE " + " OR ".join(conditions), parameters


def execute_count_query(sql_text: str,
                        parameters: List[Any]) -> int:
    """
    Execute one count query against the configured database.

    :param sql_text: SQL statement returning a single count.
    :param parameters: Positional SQL parameters.
    :return: Count result.
    """
    database_settings = get_database_settings_or_none()

    if database_settings is None:
        return 0
    else:
        pass

    connection_kwargs: Dict[str, Any] = build_connection_kwargs(settings=database_settings)

    with psycopg.connect(**connection_kwargs) as connection:
        cursor = connection.cursor()
        cursor.execute(sql_text, parameters)
        row: Any = cursor.fetchone()
        cursor.close()

    if row is None:
        return 0
    else:
        return int(row[0])


def execute_rows_query(sql_text: str,
                       parameters: List[Any]) -> List[Any]:
    """
    Execute one row-returning query against the configured database.

    :param sql_text: SQL statement returning rows.
    :param parameters: Positional SQL parameters.
    :return: Query rows.
    """
    database_settings = get_database_settings_or_none()

    if database_settings is None:
        return list()
    else:
        pass

    connection_kwargs: Dict[str, Any] = build_connection_kwargs(settings=database_settings)

    with psycopg.connect(**connection_kwargs) as connection:
        cursor = connection.cursor()
        cursor.execute(sql_text, parameters)
        rows: Any = cursor.fetchall()
        cursor.close()

    return list(rows)


def count_organizations(query_text: str) -> int:
    """
    Count organizations matching one optional search filter.

    :param query_text: Search text.
    :return: Matching row count.
    """
    quoted_schema_name: str = quote_sql_identifier("veragrid")
    where_sql, parameters = get_search_clause(query_text, ['idtag', 'name'])
    return execute_count_query(
        f'SELECT COUNT(*) FROM {quoted_schema_name}."Organization"{where_sql}',
        parameters,
    )


def list_organizations(query_text: str,
                       limit_value: int,
                       offset_value: int) -> List[Dict[str, Any]]:
    """
    List organizations with paging and one optional search filter.

    :param query_text: Search text.
    :param limit_value: Maximum rows to return.
    :param offset_value: Row offset.
    :return: Organization dictionaries.
    """
    quoted_schema_name: str = quote_sql_identifier("veragrid")
    where_sql, parameters = get_search_clause(query_text, ['o.idtag', 'o.name'])
    parameters.extend([limit_value, offset_value])
    rows: List[Any] = execute_rows_query(
        f'''
        SELECT
            o.idtag,
            o.name,
            COUNT(u.idtag) AS user_count
        FROM {quoted_schema_name}."Organization" AS o
        LEFT JOIN {quoted_schema_name}."Users" AS u
            ON u.organization_idtag = o.idtag
        {where_sql}
        GROUP BY o.idtag, o.name
        ORDER BY o.name, o.idtag
        LIMIT %s OFFSET %s
        ''',
        parameters,
    )
    organizations: List[Dict[str, Any]] = list()
    row: Any

    for row in rows:
        organizations.append(
            {
                "idtag": str(row[0]),
                "name": str(row[1]),
                "user_count": int(row[2]),
            }
        )

    return organizations


def count_users(query_text: str) -> int:
    """
    Count users matching one optional search filter.

    :param query_text: Search text.
    :return: Matching row count.
    """
    quoted_schema_name: str = quote_sql_identifier("veragrid")
    where_sql, parameters = get_search_clause(query_text, ['idtag', 'name', 'organization_idtag'])
    return execute_count_query(
        f'SELECT COUNT(*) FROM {quoted_schema_name}."Users"{where_sql}',
        parameters,
    )


def list_users(query_text: str,
               limit_value: int,
               offset_value: int) -> List[Dict[str, Any]]:
    """
    List users with paging and one optional search filter.

    :param query_text: Search text.
    :param limit_value: Maximum rows to return.
    :param offset_value: Row offset.
    :return: User dictionaries.
    """
    quoted_schema_name: str = quote_sql_identifier("veragrid")
    where_sql, parameters = get_search_clause(query_text, ['u.idtag', 'u.name', 'u.organization_idtag'])
    parameters.extend([limit_value, offset_value])
    rows: List[Any] = execute_rows_query(
        f'''
        SELECT
            u.idtag,
            u.name,
            u.organization_idtag,
            COUNT(f.idtag) AS file_count
        FROM {quoted_schema_name}."Users" AS u
        LEFT JOIN {quoted_schema_name}."Files" AS f
            ON f."user" = u.idtag
        {where_sql}
        GROUP BY u.idtag, u.name, u.organization_idtag
        ORDER BY u.organization_idtag, u.name, u.idtag
        LIMIT %s OFFSET %s
        ''',
        parameters,
    )
    users: List[Dict[str, Any]] = list()
    row: Any

    for row in rows:
        users.append(
            {
                "idtag": str(row[0]),
                "name": str(row[1]),
                "organization_idtag": str(row[2]),
                "file_count": int(row[3]),
            }
        )

    return users


def count_files(query_text: str) -> int:
    """
    Count files matching one optional search filter.

    :param query_text: Search text.
    :return: Matching row count.
    """
    quoted_schema_name: str = quote_sql_identifier("veragrid")
    where_sql, parameters = get_search_clause(query_text, ['idtag', 'name', '"user"'])
    return execute_count_query(
        f'SELECT COUNT(*) FROM {quoted_schema_name}."Files"{where_sql}',
        parameters,
    )


def list_files(query_text: str,
               limit_value: int,
               offset_value: int) -> List[Dict[str, Any]]:
    """
    List files with paging and one optional search filter.

    :param query_text: Search text.
    :param limit_value: Maximum rows to return.
    :param offset_value: Row offset.
    :return: File dictionaries.
    """
    quoted_schema_name: str = quote_sql_identifier("veragrid")
    where_sql, parameters = get_search_clause(query_text, ['f.idtag', 'f.name', 'f."user"'])
    parameters.extend([limit_value, offset_value])
    rows: List[Any] = execute_rows_query(
        f'''
        SELECT
            f.idtag,
            f.name,
            f."user",
            f.created_at,
            COUNT(m.idtag) AS model_count
        FROM {quoted_schema_name}."Files" AS f
        LEFT JOIN {quoted_schema_name}."Models" AS m
            ON m.file_idtag = f.idtag
        {where_sql}
        GROUP BY f.idtag, f.name, f."user", f.created_at
        ORDER BY f.created_at DESC, f.idtag
        LIMIT %s OFFSET %s
        ''',
        parameters,
    )
    files: List[Dict[str, Any]] = list()
    row: Any

    for row in rows:
        files.append(
            {
                "idtag": str(row[0]),
                "name": str(row[1]),
                "user": str(row[2]),
                "created_at": str(row[3]),
                "model_count": int(row[4]),
            }
        )

    return files


def count_models(query_text: str) -> int:
    """
    Count models matching one optional search filter.

    :param query_text: Search text.
    :return: Matching row count.
    """
    quoted_schema_name: str = quote_sql_identifier("veragrid")
    where_sql, parameters = get_search_clause(
        query_text,
        ['idtag', 'name', 'file_idtag', 'COALESCE(parent_model_idtag, \'\')'],
    )
    return execute_count_query(
        f'SELECT COUNT(*) FROM {quoted_schema_name}."Models"{where_sql}',
        parameters,
    )


def list_models(query_text: str,
                limit_value: int,
                offset_value: int) -> List[Dict[str, Any]]:
    """
    List models with paging and one optional search filter.

    :param query_text: Search text.
    :param limit_value: Maximum rows to return.
    :param offset_value: Row offset.
    :return: Model dictionaries.
    """
    quoted_schema_name: str = quote_sql_identifier("veragrid")
    where_sql, parameters = get_search_clause(
        query_text,
        ['m.idtag', 'm.name', 'm.file_idtag', 'COALESCE(m.parent_model_idtag, \'\')'],
    )
    parameters.extend([limit_value, offset_value])
    rows: List[Any] = execute_rows_query(
        f'''
        SELECT
            m.file_idtag,
            m.idtag,
            m.name,
            m.parent_model_idtag
        FROM {quoted_schema_name}."Models" AS m
        {where_sql}
        ORDER BY m.file_idtag, m.parent_model_idtag NULLS FIRST, m.name, m.idtag
        LIMIT %s OFFSET %s
        ''',
        parameters,
    )
    models: List[Dict[str, Any]] = list()
    row: Any

    for row in rows:
        models.append(
            {
                "file_idtag": str(row[0]),
                "idtag": str(row[1]),
                "name": str(row[2]),
                "parent_model_idtag": None if row[3] is None else str(row[3]),
                "kind": "base" if row[3] is None else "delta",
            }
        )

    return models


def count_logs(query_text: str) -> int:
    """
    Count buffered log entries matching one optional search filter.

    :param query_text: Search text.
    :return: Matching log entry count.
    """
    if len(query_text) == 0:
        return len(LOG_BUFFER)
    else:
        pass

    lowered_query_text: str = query_text.lower()
    count_value: int = 0
    log_entry: Dict[str, str]

    for log_entry in LOG_BUFFER:
        joined_text: str = " ".join(log_entry.values()).lower()
        if lowered_query_text in joined_text:
            count_value += 1
        else:
            pass

    return count_value


def list_logs(query_text: str,
              limit_value: int,
              offset_value: int) -> List[Dict[str, str]]:
    """
    List buffered log entries with paging and one optional search filter.

    :param query_text: Search text.
    :param limit_value: Maximum rows to return.
    :param offset_value: Row offset.
    :return: Log entry dictionaries.
    """
    filtered_logs: List[Dict[str, str]] = list()

    if len(query_text) == 0:
        filtered_logs = list(LOG_BUFFER)
    else:
        lowered_query_text: str = query_text.lower()
        log_entry: Dict[str, str]

        for log_entry in LOG_BUFFER:
            joined_text: str = " ".join(log_entry.values()).lower()
            if lowered_query_text in joined_text:
                filtered_logs.append(log_entry)
            else:
                pass

    return filtered_logs[offset_value:offset_value + limit_value]


def create_organization(idtag: str,
                        name: str) -> None:
    """
    Create one organization row.

    :param idtag: Organization identifier.
    :param name: Organization display name.
    :return: None.
    """
    database_settings = get_database_settings_or_none()

    if database_settings is None:
        raise ValueError("Database settings are not configured")
    else:
        pass

    quoted_schema_name: str = quote_sql_identifier("veragrid")
    connection_kwargs: Dict[str, Any] = build_connection_kwargs(settings=database_settings)

    with psycopg.connect(**connection_kwargs) as connection:
        cursor = connection.cursor()
        cursor.execute(
            f'''
            INSERT INTO {quoted_schema_name}."Organization" (idtag, name)
            VALUES (%s, %s)
            ''',
            (idtag, name),
        )
        connection.commit()
        cursor.close()


def update_organization(idtag: str,
                        name: str) -> None:
    """
    Update one organization row.

    :param idtag: Organization identifier.
    :param name: Organization display name.
    :return: None.
    """
    database_settings = get_database_settings_or_none()

    if database_settings is None:
        raise ValueError("Database settings are not configured")
    else:
        pass

    quoted_schema_name: str = quote_sql_identifier("veragrid")
    connection_kwargs: Dict[str, Any] = build_connection_kwargs(settings=database_settings)

    with psycopg.connect(**connection_kwargs) as connection:
        cursor = connection.cursor()
        cursor.execute(
            f'''
            UPDATE {quoted_schema_name}."Organization"
            SET name = %s
            WHERE idtag = %s
            ''',
            (name, idtag),
        )
        connection.commit()
        cursor.close()


def delete_organization(idtag: str) -> None:
    """
    Delete one organization row.

    :param idtag: Organization identifier.
    :return: None.
    """
    database_settings = get_database_settings_or_none()

    if database_settings is None:
        raise ValueError("Database settings are not configured")
    else:
        pass

    quoted_schema_name: str = quote_sql_identifier("veragrid")
    connection_kwargs: Dict[str, Any] = build_connection_kwargs(settings=database_settings)

    with psycopg.connect(**connection_kwargs) as connection:
        cursor = connection.cursor()
        cursor.execute(
            f'''
            DELETE FROM {quoted_schema_name}."Organization"
            WHERE idtag = %s
            ''',
            (idtag,),
        )
        connection.commit()
        cursor.close()


def update_file(file_idtag: str,
                file_name: str,
                user_idtag: str) -> None:
    """
    Update one file metadata row.

    :param file_idtag: File identifier.
    :param file_name: File display name.
    :param user_idtag: Owning user identifier.
    :return: None.
    """
    database_settings = get_database_settings_or_none()

    if database_settings is None:
        raise ValueError("Database settings are not configured")
    else:
        pass

    quoted_schema_name: str = quote_sql_identifier("veragrid")
    connection_kwargs: Dict[str, Any] = build_connection_kwargs(settings=database_settings)

    with psycopg.connect(**connection_kwargs) as connection:
        cursor = connection.cursor()
        cursor.execute(
            f'''
            UPDATE {quoted_schema_name}."Files"
            SET name = %s, "user" = %s
            WHERE idtag = %s
            ''',
            (file_name, user_idtag, file_idtag),
        )
        connection.commit()
        cursor.close()


def import_uploaded_model_file(file_name: str,
                               temp_path: str,
                               user_idtag: str) -> str:
    """
    Import one uploaded model file into the configured database.

    The upload can contain either one flat ``MultiCircuit`` or one full
    ``MultiVerse`` archive. File and model rows are created from the parsed
    engine object rather than through manual web-form creation.

    :param file_name: Original uploaded file name.
    :param temp_path: Temporary file path containing the uploaded content.
    :param user_idtag: Owning user identifier.
    :return: Created file identifier.
    """
    database_settings = get_database_settings_or_none()

    if database_settings is None:
        raise ValueError("Database settings are not configured")
    else:
        pass

    try:
        loader: FileOpen = FileOpen(file_name=temp_path)
        loader.open()
        file_idtag: str = str(uuid4())
        file_name_text: str = Path(file_name).name

        if loader.multiverse is not None:
            put_multiverse_in_database(
                settings=database_settings,
                multiverse=loader.multiverse,
                file_idtag=file_idtag,
                user_idtag=user_idtag,
                file_name=file_name_text,
                project_directory=Path(temp_path).resolve().parent,
            )
        elif loader.circuit is not None:
            file_idtag = create_file(
                settings=database_settings,
                file_name=file_name_text,
                user_idtag=user_idtag,
                file_idtag=file_idtag,
            )

            model_name_raw: str | None = loader.circuit.name
            model_name: str
            if model_name_raw is None or len(model_name_raw.strip()) == 0:
                model_name = Path(file_name).stem
            else:
                model_name = model_name_raw

            model_idtag: str = create_model(
                settings=database_settings,
                file_idtag=file_idtag,
                model_name=model_name,
                parent_model_idtag=None,
                model_idtag=None,
            )
            put_multicircuit_in_database(
                settings=database_settings,
                circuit=loader.circuit,
                file_idtag=file_idtag,
                model_idtag=model_idtag,
                project_directory=Path(temp_path).resolve().parent,
            )
        else:
            raise ValueError("The uploaded file could not be parsed into a grid or multiverse")

        return file_idtag
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        else:
            pass


def count_files_for_dashboard() -> int:
    """
    Count files for the dashboard metric.

    :return: File count.
    """
    return count_files(query_text="")


def count_models_for_dashboard() -> int:
    """
    Count models for the dashboard metric.

    :return: Model count.
    """
    return count_models(query_text="")


def count_users_for_dashboard() -> int:
    """
    Count users for the dashboard metric.

    :return: User count.
    """
    return count_users(query_text="")


def count_organizations_for_dashboard() -> int:
    """
    Count organizations for the dashboard metric.

    :return: Organization count.
    """
    return count_organizations(query_text="")


def render_page(title: str,
                body_html: str) -> str:
    """
    Wrap one admin body in the shared HTML layout.

    :param title: Document title.
    :param body_html: Pre-rendered body HTML.
    :return: Full HTML page.
    """
    safe_title: str = html.escape(title)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{safe_title}</title>
    <style>
        :root {{
            --bg: #f2f4f7;
            --paper: #ffffff;
            --paper-2: #f7f9fc;
            --paper-3: #eef2f8;
            --ink: #0b1117;
            --muted: #5d6774;
            --line: #d8e0ec;
            --accent: #004cff;
            --accent-2: #2e6dff;
            --accent-soft: #e8efff;
            --danger: #c62739;
            --warn: #9a6400;
            --shadow: rgba(11, 17, 23, 0.08);
            --shadow-strong: rgba(0, 76, 255, 0.12);
        }}
        * {{
            box-sizing: border-box;
        }}
        body {{
            margin: 0;
            color: var(--ink);
            font-family: Ubuntu, "Segoe UI", sans-serif;
            background:
                radial-gradient(circle at top left, rgba(0, 76, 255, 0.16) 0%, transparent 24%),
                radial-gradient(circle at right 18%, rgba(0, 0, 0, 0.055) 0%, transparent 22%),
                linear-gradient(180deg, #ffffff 0%, var(--bg) 100%);
        }}
        a {{
            color: var(--accent);
            text-decoration: none;
        }}
        .shell {{
            max-width: 1480px;
            margin: 0 auto;
            padding: 24px 16px 48px 16px;
        }}
        .hero {{
            display: flex;
            justify-content: space-between;
            gap: 18px;
            align-items: end;
            margin-bottom: 20px;
            padding: 22px 24px;
            border: 1px solid rgba(0, 76, 255, 0.12);
            border-radius: 28px;
            background:
                linear-gradient(135deg, rgba(0, 76, 255, 0.08) 0%, rgba(255, 255, 255, 0.96) 42%, rgba(11, 17, 23, 0.03) 100%);
            box-shadow: 0 24px 60px var(--shadow);
        }}
        .hero h1 {{
            margin: 0;
            font-size: 2.9rem;
            line-height: 0.98;
            letter-spacing: -0.06em;
        }}
        .hero p {{
            margin: 8px 0 0 0;
            max-width: 920px;
            color: var(--muted);
        }}
        .topbar {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-bottom: 18px;
        }}
        .topbar a, .topbar button {{
            border: 1px solid var(--line);
            background: rgba(255, 255, 255, 0.85);
            color: var(--ink);
            border-radius: 999px;
            padding: 10px 14px;
            font: inherit;
            font-weight: 500;
            cursor: pointer;
        }}
        .topbar .active {{
            background: var(--accent);
            color: white;
            border-color: var(--accent);
            box-shadow: 0 10px 24px var(--shadow-strong);
        }}
        .stat-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
            gap: 14px;
            margin-bottom: 18px;
        }}
        .panel {{
            border: 1px solid var(--line);
            border-radius: 22px;
            background: color-mix(in srgb, var(--paper) 95%, var(--paper-2) 5%);
            box-shadow: 0 16px 38px var(--shadow);
            padding: 20px;
        }}
        .panel h2, .panel h3 {{
            margin-top: 0;
            letter-spacing: -0.03em;
        }}
        .metric {{
            font-size: 2.35rem;
            font-weight: 700;
            margin: 8px 0 4px 0;
            letter-spacing: -0.05em;
        }}
        .muted {{
            color: var(--muted);
        }}
        .flash {{
            border: 1px solid var(--line);
            border-left: 6px solid var(--accent);
            border-radius: 14px;
            padding: 12px 14px;
            background: linear-gradient(90deg, var(--accent-soft) 0%, var(--paper) 24%);
            margin-bottom: 16px;
        }}
        .section-grid {{
            display: grid;
            grid-template-columns: minmax(280px, 360px) minmax(0, 1fr);
            gap: 16px;
        }}
        .form-grid {{
            display: grid;
            gap: 12px;
        }}
        .field {{
            display: grid;
            gap: 6px;
        }}
        .field label {{
            font-weight: 700;
            font-size: 0.95rem;
        }}
        .field input {{
            width: 100%;
            border: 1px solid var(--line);
            border-radius: 12px;
            padding: 10px 12px;
            font: inherit;
            background: white;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.9);
        }}
        .btn-row {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }}
        .btn {{
            border: 1px solid var(--line);
            border-radius: 12px;
            padding: 10px 12px;
            font: inherit;
            font-weight: 500;
            cursor: pointer;
            background: white;
            color: var(--ink);
        }}
        .btn.primary {{
            background: var(--accent);
            color: white;
            border-color: var(--accent);
            box-shadow: 0 10px 20px var(--shadow-strong);
        }}
        .btn.warn {{
            background: #fff4db;
            color: var(--warn);
            border-color: #f0cf8b;
        }}
        .btn.danger {{
            background: #ffe7ea;
            color: var(--danger);
            border-color: #f2b8c0;
        }}
        .btn[disabled] {{
            opacity: 0.65;
            cursor: wait;
        }}
        .toolbar {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            flex-wrap: wrap;
            margin-bottom: 12px;
        }}
        .toolbar form {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            align-items: center;
        }}
        .toolbar input {{
            min-width: 240px;
            border: 1px solid var(--line);
            border-radius: 12px;
            padding: 10px 12px;
            font: inherit;
            background: white;
        }}
        .scroll-table {{
            border: 1px solid var(--line);
            border-radius: 18px;
            overflow: auto;
            max-height: 72vh;
            background: white;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.85);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            min-width: 900px;
        }}
        th, td {{
            padding: 10px 12px;
            border-bottom: 1px solid var(--line);
            text-align: left;
            vertical-align: top;
        }}
        th {{
            position: sticky;
            top: 0;
            background: linear-gradient(180deg, #fdfefe 0%, var(--paper-3) 100%);
            z-index: 1;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            font-size: 0.78rem;
        }}
        tr:hover td {{
            background: rgba(0, 76, 255, 0.035);
        }}
        .inline-form {{
            display: contents;
        }}
        .mono {{
            font-family: "Ubuntu Mono", "Courier New", monospace;
            font-size: 0.92rem;
        }}
        .tag {{
            display: inline-block;
            border-radius: 999px;
            background: var(--accent-soft);
            color: var(--accent);
            padding: 3px 9px;
            margin-right: 6px;
            margin-bottom: 4px;
            font-size: 0.82rem;
            font-weight: 700;
        }}
        .pager {{
            display: flex;
            justify-content: space-between;
            gap: 12px;
            flex-wrap: wrap;
            align-items: center;
            margin-top: 12px;
        }}
        .pager .links {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }}
        .log-view {{
            border: 1px solid var(--line);
            border-radius: 16px;
            overflow: auto;
            max-height: 72vh;
            background: #0b1117;
            color: #eef4ff;
            padding: 0;
        }}
        .log-row {{
            display: grid;
            grid-template-columns: 180px 180px 120px minmax(400px, 1fr);
            gap: 0;
            border-bottom: 1px solid rgba(255,255,255,0.08);
        }}
        .log-cell {{
            padding: 10px 12px;
            white-space: pre-wrap;
            word-break: break-word;
            font-family: "Ubuntu Mono", "Courier New", monospace;
            font-size: 0.9rem;
        }}
        .login-wrap {{
            min-height: 100vh;
            display: grid;
            place-items: center;
            padding: 24px;
        }}
        .login-panel {{
            width: min(460px, 100%);
            background: var(--paper);
            border: 1px solid var(--line);
            border-radius: 28px;
            padding: 28px;
            box-shadow: 0 30px 70px var(--shadow);
        }}
        .error {{
            color: var(--danger);
            margin-bottom: 12px;
        }}
        .empty {{
            padding: 16px;
            border-radius: 14px;
            border: 1px dashed var(--line);
            color: var(--muted);
            background: linear-gradient(180deg, rgba(0, 76, 255, 0.04) 0%, rgba(255, 255, 255, 0.9) 100%);
        }}
        .upload-dropzone {{
            border: 2px dashed var(--accent-2);
            border-radius: 18px;
            padding: 20px;
            background: linear-gradient(180deg, rgba(232, 239, 255, 0.95) 0%, rgba(255, 255, 255, 0.86) 100%);
            transition: transform 120ms ease, box-shadow 120ms ease, border-color 120ms ease;
        }}
        .upload-dropzone.dragover {{
            transform: translateY(-1px);
            box-shadow: 0 16px 32px var(--shadow-strong);
            border-color: var(--accent);
        }}
        .upload-dropzone h3 {{
            margin-top: 0;
        }}
        .upload-dropzone p {{
            margin: 0 0 10px 0;
        }}
        @media (max-width: 980px) {{
            .section-grid {{
                grid-template-columns: 1fr;
            }}
        }}
        @media (max-width: 760px) {{
            .hero {{
                flex-direction: column;
                align-items: start;
            }}
            .toolbar form, .btn-row {{
                width: 100%;
            }}
            .toolbar input {{
                min-width: 0;
                width: 100%;
            }}
        }}
    </style>
</head>
<body>
{body_html}
<script>
(() => {{
    const dropzones = document.querySelectorAll("[data-upload-dropzone]");
    dropzones.forEach((zone) => {{
        const input = zone.querySelector("input[type=file]");
        const ownerInput = zone.querySelector("input[name=user_idtag]");
        const button = zone.querySelector("button[data-upload-submit]");
        const status = zone.querySelector("[data-upload-status]");

        const setStatus = (text, isError = false) => {{
            status.textContent = text;
            status.style.color = isError ? "var(--danger)" : "var(--muted)";
        }};

        const uploadSelectedFile = async () => {{
            const file = input.files && input.files[0] ? input.files[0] : null;
            const owner = ownerInput.value.trim();

            if (!file) {{
                setStatus("Pick or drop one file first.", true);
                return;
            }}

            if (!owner) {{
                setStatus("Owner user idtag is required.", true);
                return;
            }}

            button.disabled = true;
            setStatus("Uploading " + file.name + "...");

            try {{
                const response = await fetch("/admin/uploads/model", {{
                    method: "POST",
                    headers: {{
                        "Content-Type": "application/octet-stream",
                        "X-VeraGrid-File-Name": encodeURIComponent(file.name),
                        "X-VeraGrid-User-Idtag": encodeURIComponent(owner)
                    }},
                    body: file
                }});

                const payload = await response.json();

                if (payload.success) {{
                    window.location.href = payload.redirect_url;
                }} else {{
                    setStatus(payload.message || "Upload failed.", true);
                }}
            }} catch (error) {{
                setStatus("Upload failed: " + error, true);
            }} finally {{
                button.disabled = false;
            }}
        }};

        zone.addEventListener("dragover", (event) => {{
            event.preventDefault();
            zone.classList.add("dragover");
        }});

        zone.addEventListener("dragleave", () => {{
            zone.classList.remove("dragover");
        }});

        zone.addEventListener("drop", (event) => {{
            event.preventDefault();
            zone.classList.remove("dragover");
            if (event.dataTransfer && event.dataTransfer.files && event.dataTransfer.files.length > 0) {{
                input.files = event.dataTransfer.files;
                setStatus("Ready to upload " + event.dataTransfer.files[0].name);
            }}
        }});

        input.addEventListener("change", () => {{
            if (input.files && input.files[0]) {{
                setStatus("Ready to upload " + input.files[0].name);
            }} else {{
                setStatus("Drop a VeraGrid file here or choose one manually.");
            }}
        }});

        button.addEventListener("click", (event) => {{
            event.preventDefault();
            uploadSelectedFile();
        }});
    }});
}})();
</script>
</body>
</html>"""


def render_login_page(error_message: str = "") -> str:
    """
    Render the admin login form.

    :param error_message: Optional user-facing error message.
    :return: Full HTML page.
    """
    safe_error_message: str = html.escape(error_message)
    error_html: str

    if len(safe_error_message) > 0:
        error_html = f'<div class="error">{safe_error_message}</div>'
    else:
        error_html = ""

    body_html: str = f"""
    <div class="login-wrap">
        <div class="login-panel">
            <h1>VeraGrid Admin</h1>
            <p class="muted">Detailed server-side management console for the running VeraGridServer instance.</p>
            {error_html}
            <form method="post" action="/admin/login" class="form-grid">
                <div class="field">
                    <label for="password">Admin Password</label>
                    <input id="password" name="password" type="password" autocomplete="current-password" required>
                </div>
                <div class="btn-row">
                    <button class="btn primary" type="submit">Open Console</button>
                </div>
            </form>
        </div>
    </div>
    """
    return render_page(title="VeraGrid Admin Login", body_html=body_html)


def render_stat_panel(title: str,
                      value: str,
                      detail: str) -> str:
    """
    Render one metric panel.

    :param title: Panel title.
    :param value: Main metric value.
    :param detail: Secondary text.
    :return: HTML fragment.
    """
    return (
        '<section class="panel">'
        f'<h3>{html.escape(title)}</h3>'
        f'<div class="metric">{html.escape(value)}</div>'
        f'<div class="muted">{html.escape(detail)}</div>'
        '</section>'
    )


def render_flash_message(message: str) -> str:
    """
    Render one flash message box.

    :param message: Message text.
    :return: HTML fragment.
    """
    if len(message) == 0:
        return ""
    else:
        return f'<div class="flash">{html.escape(message)}</div>'


def render_topbar(active_section: str) -> str:
    """
    Render the section navigation pills.

    :param active_section: Selected section name.
    :return: HTML fragment.
    """
    sections: List[tuple[str, str]] = [
        ("dashboard", "Dashboard"),
        ("organizations", "Organizations"),
        ("users", "Users"),
        ("files", "Files"),
        ("models", "Models"),
        ("logs", "Logs"),
    ]
    links_html: List[str] = list()
    section_key: str
    label_text: str

    for section_key, label_text in sections:
        class_name: str
        if section_key == active_section:
            class_name = "active"
        else:
            class_name = ""
        links_html.append(
            f'<a class="{class_name}" href="{html.escape(build_admin_url(section=section_key))}">{html.escape(label_text)}</a>'
        )

    links_html.append('<a href="/registered_child_servers">Child API</a>')
    links_html.append('<a href="/jobs_list">Jobs API</a>')
    links_html.append(
        '<form method="post" action="/admin/logout"><button type="submit">Log Out</button></form>'
    )
    return '<div class="topbar">' + "".join(links_html) + '</div>'


def render_toolbar(section: str,
                   query_text: str,
                   page_size: int,
                   total_count: int,
                   item_label: str) -> str:
    """
    Render the paging and search toolbar for one tabular section.

    :param section: Active section name.
    :param query_text: Search text.
    :param page_size: Rows per page.
    :param total_count: Total matching rows.
    :param item_label: Human-readable item label.
    :return: HTML fragment.
    """
    return f"""
    <div class="toolbar">
        <form method="get" action="/admin">
            <input type="hidden" name="section" value="{html.escape(section)}">
            <input type="hidden" name="page" value="1">
            <input type="hidden" name="page_size" value="{html.escape(str(page_size))}">
            <input type="text" name="q" value="{html.escape(query_text)}" placeholder="Search {html.escape(item_label)}">
            <button class="btn primary" type="submit">Filter</button>
        </form>
        <div class="muted">{html.escape(str(total_count))} matching {html.escape(item_label)}</div>
    </div>
    """


def render_pager(section: str,
                 page: int,
                 page_size: int,
                 total_count: int,
                 query_text: str) -> str:
    """
    Render one pager block.

    :param section: Active section name.
    :param page: Current 1-based page.
    :param page_size: Rows per page.
    :param total_count: Total matching rows.
    :param query_text: Search text.
    :return: HTML fragment.
    """
    total_pages: int
    if total_count == 0:
        total_pages = 1
    else:
        total_pages = ceil(total_count / page_size)

    prev_page: int
    if page > 1:
        prev_page = page - 1
    else:
        prev_page = 1

    next_page: int
    if page < total_pages:
        next_page = page + 1
    else:
        next_page = total_pages

    return f"""
    <div class="pager">
        <div class="muted">Page {html.escape(str(page))} / {html.escape(str(total_pages))}</div>
        <div class="links">
            <a class="btn" href="{html.escape(build_admin_url(section=section, page=1, page_size=page_size, query_text=query_text))}">First</a>
            <a class="btn" href="{html.escape(build_admin_url(section=section, page=prev_page, page_size=page_size, query_text=query_text))}">Prev</a>
            <a class="btn" href="{html.escape(build_admin_url(section=section, page=next_page, page_size=page_size, query_text=query_text))}">Next</a>
            <a class="btn" href="{html.escape(build_admin_url(section=section, page=total_pages, page_size=page_size, query_text=query_text))}">Last</a>
        </div>
    </div>
    """


def render_dashboard_section(database_enabled: bool,
                             database_message: str) -> str:
    """
    Render the dashboard section.

    :param database_enabled: Whether DB access is configured.
    :param database_message: Human-readable DB status text.
    :return: HTML fragment.
    """
    server_mode_text: str
    if settings.am_i_master:
        server_mode_text = "Master"
    else:
        server_mode_text = "Child"

    organization_count: int
    user_count: int
    file_count: int
    model_count: int

    if database_enabled:
        organization_count = count_organizations_for_dashboard()
        user_count = count_users_for_dashboard()
        file_count = count_files_for_dashboard()
        model_count = count_models_for_dashboard()
    else:
        organization_count = 0
        user_count = 0
        file_count = 0
        model_count = 0

    child_items_html: List[str] = list()
    service_key: str
    service_data: Dict[str, Any]

    for service_key, service_data in registered_services.items():
        child_items_html.append(
            '<div class="tag">'
            f'{html.escape(service_key)} @ {html.escape(str(service_data.get("ip", "")))}:{html.escape(str(service_data.get("port", "")))}'
            '</div>'
        )

    job_items_html: List[str] = list()
    job: Any

    for job in JOBS_LIST.values():
        job_data: Dict[str, Any] = job.get_data()
        job_items_html.append(
            '<div class="tag">'
            f'{html.escape(str(job_data.get("id_tag", "")))} [{html.escape(str(job_data.get("status", "")))}]'
            '</div>'
        )

    child_block: str
    if len(child_items_html) > 0:
        child_block = "".join(child_items_html)
    else:
        child_block = '<div class="empty">No child servers registered.</div>'

    job_block: str
    if len(job_items_html) > 0:
        job_block = "".join(job_items_html)
    else:
        job_block = '<div class="empty">No jobs are currently tracked.</div>'

    return f"""
    <div class="stat-grid">
        {render_stat_panel("Server Mode", server_mode_text, f"{settings.this_host}:{settings.this_port}")}
        {render_stat_panel("Organizations", str(organization_count), "Managed tenant roots")}
        {render_stat_panel("Users", str(user_count), "Accounts with file access")}
        {render_stat_panel("Files", str(file_count), "Persisted multiverse containers")}
        {render_stat_panel("Models", str(model_count), "Base and delta snapshots")}
        {render_stat_panel("Logs In Buffer", str(len(LOG_BUFFER)), "Recent in-memory server log entries")}
    </div>
    <div class="section-grid">
        <section class="panel">
            <h2>System Summary</h2>
            <p class="muted">Database status: {html.escape(database_message)}</p>
            <p class="muted">This console is server-side rendered and uses paging, search filters, and scrollable tables so large datasets remain navigable without pushing every row to the browser.</p>
        </section>
        <section class="panel">
            <h2>Runtime Activity</h2>
            <h3>Registered Child Servers</h3>
            <div>{child_block}</div>
            <h3>Live Jobs</h3>
            <div>{job_block}</div>
        </section>
    </div>
    """


def render_organizations_section(query_text: str,
                                 page: int,
                                 page_size: int) -> str:
    """
    Render the organization management section.

    :param query_text: Search text.
    :param page: Current page.
    :param page_size: Rows per page.
    :return: HTML fragment.
    """
    total_count: int = count_organizations(query_text=query_text)
    offset_value: int = (page - 1) * page_size
    organizations: List[Dict[str, Any]] = list_organizations(
        query_text=query_text,
        limit_value=page_size,
        offset_value=offset_value,
    )
    row_html: List[str] = list()
    organization: Dict[str, Any]

    for organization in organizations:
        row_html.append(
            "<tr>"
            f"<form class=\"inline-form\" method=\"post\" action=\"/admin/organizations/update\">"
            f"<td class=\"mono\">{html.escape(organization['idtag'])}<input type=\"hidden\" name=\"idtag\" value=\"{html.escape(organization['idtag'])}\"></td>"
            f"<td><input name=\"name\" value=\"{html.escape(organization['name'])}\"></td>"
            f"<td>{html.escape(str(organization['user_count']))}</td>"
            f"<td><div class=\"btn-row\"><button class=\"btn warn\" type=\"submit\">Update</button></form>"
            f"<form method=\"post\" action=\"/admin/organizations/delete\"><input type=\"hidden\" name=\"idtag\" value=\"{html.escape(organization['idtag'])}\"><button class=\"btn danger\" type=\"submit\">Delete</button></form></div></td>"
            "</tr>"
        )

    rows_block: str
    if len(row_html) > 0:
        rows_block = "".join(row_html)
    else:
        rows_block = '<tr><td colspan="4"><div class="empty">No organizations found.</div></td></tr>'

    return f"""
    <div class="section-grid">
        <section class="panel">
            <h2>Create Organization</h2>
            <form class="form-grid" method="post" action="/admin/organizations/create">
                <div class="field">
                    <label for="organization_idtag">Organization Idtag</label>
                    <input id="organization_idtag" name="idtag" required>
                </div>
                <div class="field">
                    <label for="organization_name">Organization Name</label>
                    <input id="organization_name" name="name" required>
                </div>
                <div class="btn-row">
                    <button class="btn primary" type="submit">Create Organization</button>
                </div>
            </form>
        </section>
        <section class="panel">
            <h2>Organization Management</h2>
            {render_toolbar("organizations", query_text, page_size, total_count, "organizations")}
            <div class="scroll-table">
                <table>
                    <thead>
                        <tr>
                            <th>Idtag</th>
                            <th>Name</th>
                            <th>User Count</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>{rows_block}</tbody>
                </table>
            </div>
            {render_pager("organizations", page, page_size, total_count, query_text)}
        </section>
    </div>
    """


def render_users_section(query_text: str,
                         page: int,
                         page_size: int) -> str:
    """
    Render the user management section.

    :param query_text: Search text.
    :param page: Current page.
    :param page_size: Rows per page.
    :return: HTML fragment.
    """
    total_count: int = count_users(query_text=query_text)
    offset_value: int = (page - 1) * page_size
    users: List[Dict[str, Any]] = list_users(
        query_text=query_text,
        limit_value=page_size,
        offset_value=offset_value,
    )
    row_html: List[str] = list()
    user_json: Dict[str, Any]

    for user_json in users:
        row_html.append(
            "<tr>"
            f"<form class=\"inline-form\" method=\"post\" action=\"/admin/users/update\">"
            f"<td class=\"mono\">{html.escape(user_json['idtag'])}<input type=\"hidden\" name=\"idtag\" value=\"{html.escape(user_json['idtag'])}\"></td>"
            f"<td><input name=\"name\" value=\"{html.escape(user_json['name'])}\"></td>"
            f"<td><input name=\"password\" placeholder=\"Leave blank to keep current\"></td>"
            f"<td><input name=\"organization_idtag\" value=\"{html.escape(user_json['organization_idtag'])}\"></td>"
            f"<td>{html.escape(str(user_json['file_count']))}</td>"
            f"<td><div class=\"btn-row\"><button class=\"btn warn\" type=\"submit\">Update</button></form>"
            f"<form method=\"post\" action=\"/admin/users/delete\"><input type=\"hidden\" name=\"idtag\" value=\"{html.escape(user_json['idtag'])}\"><button class=\"btn danger\" type=\"submit\">Delete</button></form></div></td>"
            "</tr>"
        )

    rows_block: str
    if len(row_html) > 0:
        rows_block = "".join(row_html)
    else:
        rows_block = '<tr><td colspan="6"><div class="empty">No users found.</div></td></tr>'

    return f"""
    <div class="section-grid">
        <section class="panel">
            <h2>Create User</h2>
            <form class="form-grid" method="post" action="/admin/users/create">
                <div class="field">
                    <label for="user_idtag">User Idtag</label>
                    <input id="user_idtag" name="idtag" required>
                </div>
                <div class="field">
                    <label for="user_name">User Name</label>
                    <input id="user_name" name="name" required>
                </div>
                <div class="field">
                    <label for="user_password">Password</label>
                    <input id="user_password" name="password" required>
                </div>
                <div class="field">
                    <label for="organization_idtag">Organization Idtag</label>
                    <input id="organization_idtag" name="organization_idtag" required>
                </div>
                <div class="btn-row">
                    <button class="btn primary" type="submit">Create User</button>
                </div>
            </form>
        </section>
        <section class="panel">
            <h2>User Management</h2>
            {render_toolbar("users", query_text, page_size, total_count, "users")}
            <div class="scroll-table">
                <table>
                    <thead>
                        <tr>
                            <th>Idtag</th>
                            <th>Name</th>
                            <th>Password</th>
                            <th>Organization</th>
                            <th>File Count</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>{rows_block}</tbody>
                </table>
            </div>
            {render_pager("users", page, page_size, total_count, query_text)}
        </section>
    </div>
    """


def render_files_section(query_text: str,
                         page: int,
                         page_size: int) -> str:
    """
    Render the file management section.

    :param query_text: Search text.
    :param page: Current page.
    :param page_size: Rows per page.
    :return: HTML fragment.
    """
    total_count: int = count_files(query_text=query_text)
    offset_value: int = (page - 1) * page_size
    files: List[Dict[str, Any]] = list_files(
        query_text=query_text,
        limit_value=page_size,
        offset_value=offset_value,
    )
    row_html: List[str] = list()
    file_json: Dict[str, Any]

    for file_json in files:
        row_html.append(
            "<tr>"
            f"<form class=\"inline-form\" method=\"post\" action=\"/admin/files/update\">"
            f"<td class=\"mono\">{html.escape(file_json['idtag'])}<input type=\"hidden\" name=\"idtag\" value=\"{html.escape(file_json['idtag'])}\"></td>"
            f"<td><input name=\"name\" value=\"{html.escape(file_json['name'])}\"></td>"
            f"<td><input name=\"user_idtag\" value=\"{html.escape(file_json['user'])}\"></td>"
            f"<td>{html.escape(file_json['created_at'])}</td>"
            f"<td>{html.escape(str(file_json['model_count']))}</td>"
            f"<td><div class=\"btn-row\"><button class=\"btn warn\" type=\"submit\">Update</button></form>"
            f"<form method=\"post\" action=\"/admin/files/delete\"><input type=\"hidden\" name=\"idtag\" value=\"{html.escape(file_json['idtag'])}\"><button class=\"btn danger\" type=\"submit\">Delete</button></form></div></td>"
            "</tr>"
        )

    rows_block: str
    if len(row_html) > 0:
        rows_block = "".join(row_html)
    else:
        rows_block = '<tr><td colspan="6"><div class="empty">No files found.</div></td></tr>'

    return f"""
    <div class="section-grid">
        <section class="panel">
            <h2>Import File</h2>
            <div class="upload-dropzone" data-upload-dropzone>
                <h3>Drag And Drop Upload</h3>
                <p class="muted">Drop one `.gridcal`, `.veragrid`, `.dgridcal`, `.dveragrid`, or any other engine-supported model file here. Files and models are created only through this import path.</p>
                <div class="field">
                    <label for="upload_owner_user_idtag">Owning User Idtag</label>
                    <input id="upload_owner_user_idtag" name="user_idtag" required>
                </div>
                <div class="field">
                    <label for="upload_model_file">Model File</label>
                    <input id="upload_model_file" type="file" accept=".gridcal,.veragrid,.dgridcal,.dveragrid,.zip,.json,.xlsx,.xls,.raw,.rawx,.xml,.ucte,.m,.dgs">
                </div>
                <div class="btn-row">
                    <button class="btn primary" data-upload-submit type="button">Upload Into Database</button>
                </div>
                <div class="muted" data-upload-status>Drop a VeraGrid file here or choose one manually.</div>
            </div>
        </section>
        <section class="panel">
            <h2>File Management</h2>
            {render_toolbar("files", query_text, page_size, total_count, "files")}
            <div class="scroll-table">
                <table>
                    <thead>
                        <tr>
                            <th>Idtag</th>
                            <th>Name</th>
                            <th>Owner</th>
                            <th>Created At</th>
                            <th>Model Count</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>{rows_block}</tbody>
                </table>
            </div>
            {render_pager("files", page, page_size, total_count, query_text)}
        </section>
    </div>
    """


def render_models_section(query_text: str,
                          page: int,
                          page_size: int) -> str:
    """
    Render the model management section.

    :param query_text: Search text.
    :param page: Current page.
    :param page_size: Rows per page.
    :return: HTML fragment.
    """
    total_count: int = count_models(query_text=query_text)
    offset_value: int = (page - 1) * page_size
    models: List[Dict[str, Any]] = list_models(
        query_text=query_text,
        limit_value=page_size,
        offset_value=offset_value,
    )
    row_html: List[str] = list()
    model_json: Dict[str, Any]

    for model_json in models:
        parent_text: str
        if model_json["parent_model_idtag"] is None:
            parent_text = ""
        else:
            parent_text = str(model_json["parent_model_idtag"])

        row_html.append(
            "<tr>"
            f"<form class=\"inline-form\" method=\"post\" action=\"/admin/models/update\">"
            f"<td class=\"mono\">{html.escape(model_json['file_idtag'])}<input type=\"hidden\" name=\"file_idtag\" value=\"{html.escape(model_json['file_idtag'])}\"></td>"
            f"<td class=\"mono\">{html.escape(model_json['idtag'])}<input type=\"hidden\" name=\"idtag\" value=\"{html.escape(model_json['idtag'])}\"></td>"
            f"<td><input name=\"name\" value=\"{html.escape(model_json['name'])}\"></td>"
            f"<td><input name=\"parent_model_idtag\" value=\"{html.escape(parent_text)}\" placeholder=\"Blank for base model\"></td>"
            f"<td><span class=\"tag\">{html.escape(model_json['kind'])}</span></td>"
            f"<td><div class=\"btn-row\"><button class=\"btn warn\" type=\"submit\">Update</button></form>"
            f"<form method=\"post\" action=\"/admin/models/delete\"><input type=\"hidden\" name=\"file_idtag\" value=\"{html.escape(model_json['file_idtag'])}\"><input type=\"hidden\" name=\"idtag\" value=\"{html.escape(model_json['idtag'])}\"><button class=\"btn danger\" type=\"submit\">Delete</button></form></div></td>"
            "</tr>"
        )

    rows_block: str
    if len(row_html) > 0:
        rows_block = "".join(row_html)
    else:
        rows_block = '<tr><td colspan="6"><div class="empty">No models found.</div></td></tr>'

    return f"""
    <div class="section-grid">
        <section class="panel">
            <h2>Model Intake Policy</h2>
            <p class="muted">Models are not created manually from the web UI. They enter the system only through file upload so file ownership, base/delta topology, and multiverse structure stay coherent.</p>
            <p class="muted">Use the import panel in the Files tab to upload a flat grid or a multiverse archive.</p>
        </section>
        <section class="panel">
            <h2>Model Management</h2>
            {render_toolbar("models", query_text, page_size, total_count, "models")}
            <div class="scroll-table">
                <table>
                    <thead>
                        <tr>
                            <th>File Idtag</th>
                            <th>Model Idtag</th>
                            <th>Name</th>
                            <th>Parent Model Idtag</th>
                            <th>Kind</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>{rows_block}</tbody>
                </table>
            </div>
            {render_pager("models", page, page_size, total_count, query_text)}
        </section>
    </div>
    """


def render_logs_section(query_text: str,
                        page: int,
                        page_size: int) -> str:
    """
    Render the in-memory log viewer section.

    :param query_text: Search text.
    :param page: Current page.
    :param page_size: Rows per page.
    :return: HTML fragment.
    """
    total_count: int = count_logs(query_text=query_text)
    offset_value: int = (page - 1) * page_size
    logs: List[Dict[str, str]] = list_logs(
        query_text=query_text,
        limit_value=page_size,
        offset_value=offset_value,
    )
    log_rows_html: List[str] = list()
    log_entry: Dict[str, str]

    for log_entry in logs:
        log_rows_html.append(
            '<div class="log-row">'
            f'<div class="log-cell">{html.escape(log_entry["timestamp"])}</div>'
            f'<div class="log-cell">{html.escape(log_entry["logger"])}</div>'
            f'<div class="log-cell">{html.escape(log_entry["level"])}</div>'
            f'<div class="log-cell">{html.escape(log_entry["message"])}</div>'
            '</div>'
        )

    log_block: str
    if len(log_rows_html) > 0:
        log_block = "".join(log_rows_html)
    else:
        log_block = '<div class="empty">No log entries found for the current filter.</div>'

    return f"""
    <section class="panel">
        <h2>Server Logs</h2>
        <p class="muted">The log viewer keeps the most recent {html.escape(str(LOG_BUFFER_MAXLEN))} records in memory so the admin page can inspect runtime behavior without shipping log files to the browser.</p>
        {render_toolbar("logs", query_text, page_size, total_count, "logs")}
        <div class="log-view">{log_block}</div>
        {render_pager("logs", page, page_size, total_count, query_text)}
    </section>
    """


def render_dashboard_page(active_section: str,
                          section_html: str,
                          message: str,
                          database_message: str,
                          database_enabled: bool) -> str:
    """
    Render the complete admin page shell.

    :param active_section: Selected admin section.
    :param section_html: Selected section body.
    :param message: Optional flash message.
    :param database_message: Human-readable database status.
    :param database_enabled: Whether the DB configuration is complete.
    :return: Full HTML page.
    """
    db_status_text: str
    if database_enabled:
        db_status_text = "connected"
    else:
        db_status_text = "disabled"

    body_html: str = f"""
    <div class="shell">
        <div class="hero">
            <div>
                <h1>VeraGrid Admin Console</h1>
                <p>Server-side management interface for organizations, users, files, models, runtime services, jobs, and live logs. The tables use server-side search and paging so the page remains usable even when the stored instance counts become very large.</p>
            </div>
            <div class="muted">Database: {html.escape(db_status_text)} | {html.escape(database_message)}</div>
        </div>
        {render_topbar(active_section=active_section)}
        {render_flash_message(message)}
        {section_html}
    </div>
    """
    return render_page(title="VeraGrid Admin", body_html=body_html)


def get_database_status_text() -> tuple[bool, str]:
    """
    Describe whether database-backed admin management is available.

    :return: Pair of ``(enabled, message)``.
    """
    database_settings = get_database_settings_or_none()

    if database_settings is None:
        return False, "No database configuration provided at server launch."
    else:
        return True, f"{database_settings.host}:{database_settings.port}/{database_settings.database}"


def coerce_optional_text(raw_value: str) -> str | None:
    """
    Convert one optional form field to ``None`` when blank.

    :param raw_value: Raw form value.
    :return: Stripped text or ``None``.
    """
    stripped_value: str = raw_value.strip()

    if len(stripped_value) == 0:
        return None
    else:
        return stripped_value


@router.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    """
    Render the admin login page.

    :param request: Incoming HTTP request.
    :return: HTML login page or redirect.
    """
    if is_admin_request_authenticated(request=request):
        return RedirectResponse(url="/admin", status_code=303)
    else:
        return HTMLResponse(render_login_page())


@router.post("/admin/login")
async def admin_login(request: Request):
    """
    Validate the admin password and create one session cookie.

    :param request: Incoming HTTP request.
    :return: Redirect response or login page with error.
    """
    configured_password: str = settings.this_password
    form_data: Dict[str, str] = parse_request_form(await request.body())
    password: str = form_data.get("password", "")

    if len(configured_password) == 0:
        return HTMLResponse(render_login_page("The server admin password is not configured."), status_code=503)
    elif hmac.compare_digest(password, configured_password):
        response: RedirectResponse = RedirectResponse(url="/admin", status_code=303)
        response.set_cookie(
            key=ADMIN_COOKIE_NAME,
            value=get_admin_cookie_value(),
            httponly=True,
            samesite="lax",
        )
        return response
    else:
        return HTMLResponse(render_login_page("Invalid admin password."), status_code=403)


@router.post("/admin/logout")
async def admin_logout():
    """
    Clear the admin session cookie.

    :return: Redirect response.
    """
    response: RedirectResponse = RedirectResponse(url="/admin/login", status_code=303)
    response.delete_cookie(ADMIN_COOKIE_NAME)
    return response


@router.get("/admin", response_class=HTMLResponse)
async def admin_console(request: Request):
    """
    Render the main admin console.

    :param request: Incoming HTTP request.
    :return: HTML dashboard or redirect.
    """
    redirect_response: RedirectResponse | None = require_admin_request(request=request)

    if redirect_response is not None:
        return redirect_response
    else:
        pass

    active_section: str = get_query_text(request=request, key_text="section", default_value="dashboard")
    message: str = get_query_text(request=request, key_text="msg", default_value="")
    query_text: str = get_query_text(request=request, key_text="q", default_value="")
    page: int = get_query_int(request=request, key_text="page", default_value=1, minimum_value=1, maximum_value=1000000)
    page_size: int = get_query_int(request=request, key_text="page_size", default_value=50, minimum_value=10, maximum_value=200)
    database_enabled: bool
    database_message: str
    database_enabled, database_message = get_database_status_text()

    if active_section == "dashboard":
        section_html = render_dashboard_section(
            database_enabled=database_enabled,
            database_message=database_message,
        )
    elif not database_enabled:
        section_html = '<section class="panel"><h2>Database Disabled</h2><div class="empty">This management section needs valid database settings at server launch.</div></section>'
    elif active_section == "organizations":
        section_html = render_organizations_section(query_text=query_text, page=page, page_size=page_size)
    elif active_section == "users":
        section_html = render_users_section(query_text=query_text, page=page, page_size=page_size)
    elif active_section == "files":
        section_html = render_files_section(query_text=query_text, page=page, page_size=page_size)
    elif active_section == "models":
        section_html = render_models_section(query_text=query_text, page=page, page_size=page_size)
    elif active_section == "logs":
        section_html = render_logs_section(query_text=query_text, page=page, page_size=page_size)
    else:
        section_html = render_dashboard_section(
            database_enabled=database_enabled,
            database_message=database_message,
        )
        active_section = "dashboard"

    return HTMLResponse(
        render_dashboard_page(
            active_section=active_section,
            section_html=section_html,
            message=message,
            database_message=database_message,
            database_enabled=database_enabled,
        )
    )


@router.post("/admin/organizations/create")
async def admin_create_organization(request: Request):
    """
    Create one organization from the admin console.

    :param request: Incoming HTTP request.
    :return: Redirect response.
    """
    redirect_response = require_admin_request(request=request)

    if redirect_response is not None:
        return redirect_response
    else:
        pass

    form_data: Dict[str, str] = parse_request_form(await request.body())

    try:
        create_organization(
            idtag=form_data["idtag"].strip(),
            name=form_data["name"].strip(),
        )
        message: str = "Organization created."
    except Exception as exc:
        message = f"Organization creation failed: {exc}"

    return RedirectResponse(url=build_admin_url(section="organizations", message=message), status_code=303)


@router.post("/admin/organizations/update")
async def admin_update_organization(request: Request):
    """
    Update one organization from the admin console.

    :param request: Incoming HTTP request.
    :return: Redirect response.
    """
    redirect_response = require_admin_request(request=request)

    if redirect_response is not None:
        return redirect_response
    else:
        pass

    form_data: Dict[str, str] = parse_request_form(await request.body())

    try:
        update_organization(
            idtag=form_data["idtag"].strip(),
            name=form_data["name"].strip(),
        )
        message: str = "Organization updated."
    except Exception as exc:
        message = f"Organization update failed: {exc}"

    return RedirectResponse(url=build_admin_url(section="organizations", message=message), status_code=303)


@router.post("/admin/organizations/delete")
async def admin_delete_organization(request: Request):
    """
    Delete one organization from the admin console.

    :param request: Incoming HTTP request.
    :return: Redirect response.
    """
    redirect_response = require_admin_request(request=request)

    if redirect_response is not None:
        return redirect_response
    else:
        pass

    form_data: Dict[str, str] = parse_request_form(await request.body())

    try:
        delete_organization(idtag=form_data["idtag"].strip())
        message: str = "Organization deleted."
    except Exception as exc:
        message = f"Organization deletion failed: {exc}"

    return RedirectResponse(url=build_admin_url(section="organizations", message=message), status_code=303)


@router.post("/admin/users/create")
async def admin_create_user(request: Request):
    """
    Create one user from the admin console.

    :param request: Incoming HTTP request.
    :return: Redirect response.
    """
    redirect_response = require_admin_request(request=request)

    if redirect_response is not None:
        return redirect_response
    else:
        pass

    database_settings = get_database_settings_or_none()
    form_data: Dict[str, str] = parse_request_form(await request.body())

    try:
        if database_settings is None:
            raise ValueError("Database settings are not configured")
        else:
            pass

        create_user(
            settings=database_settings,
            user_idtag=form_data["idtag"].strip(),
            user_name=form_data["name"].strip(),
            password=form_data["password"],
            organization_idtag=form_data["organization_idtag"].strip(),
        )
        message: str = "User created."
    except Exception as exc:
        message = f"User creation failed: {exc}"

    return RedirectResponse(url=build_admin_url(section="users", message=message), status_code=303)


@router.post("/admin/users/update")
async def admin_update_user(request: Request):
    """
    Update one user from the admin console.

    :param request: Incoming HTTP request.
    :return: Redirect response.
    """
    redirect_response = require_admin_request(request=request)

    if redirect_response is not None:
        return redirect_response
    else:
        pass

    database_settings = get_database_settings_or_none()
    form_data: Dict[str, str] = parse_request_form(await request.body())

    try:
        if database_settings is None:
            raise ValueError("Database settings are not configured")
        else:
            pass

        password_text: str = form_data.get("password", "")
        if len(password_text.strip()) == 0:
            existing_user: Dict[str, str] | None = get_user(
                settings=database_settings,
                user_idtag=form_data["idtag"].strip(),
            )
            if existing_user is None:
                raise ValueError("User does not exist")
            else:
                password_text = existing_user["password"]
        else:
            pass

        update_user(
            settings=database_settings,
            user_idtag=form_data["idtag"].strip(),
            user_name=form_data["name"].strip(),
            password=password_text,
            organization_idtag=form_data["organization_idtag"].strip(),
        )
        message: str = "User updated."
    except Exception as exc:
        message = f"User update failed: {exc}"

    return RedirectResponse(url=build_admin_url(section="users", message=message), status_code=303)


@router.post("/admin/users/delete")
async def admin_delete_user(request: Request):
    """
    Delete one user from the admin console.

    :param request: Incoming HTTP request.
    :return: Redirect response.
    """
    redirect_response = require_admin_request(request=request)

    if redirect_response is not None:
        return redirect_response
    else:
        pass

    database_settings = get_database_settings_or_none()
    form_data: Dict[str, str] = parse_request_form(await request.body())

    try:
        if database_settings is None:
            raise ValueError("Database settings are not configured")
        else:
            pass

        delete_user(
            settings=database_settings,
            user_idtag=form_data["idtag"].strip(),
            cascade=True,
        )
        message: str = "User deleted."
    except Exception as exc:
        message = f"User deletion failed: {exc}"

    return RedirectResponse(url=build_admin_url(section="users", message=message), status_code=303)


@router.post("/admin/files/create")
async def admin_create_file(request: Request):
    """
    Create one file from the admin console.

    :param request: Incoming HTTP request.
    :return: Redirect response.
    """
    redirect_response = require_admin_request(request=request)

    if redirect_response is not None:
        return redirect_response
    else:
        pass

    database_settings = get_database_settings_or_none()
    form_data: Dict[str, str] = parse_request_form(await request.body())

    try:
        if database_settings is None:
            raise ValueError("Database settings are not configured")
        else:
            pass

        optional_idtag: str | None = coerce_optional_text(form_data.get("idtag", ""))
        create_file(
            settings=database_settings,
            file_name=form_data["name"].strip(),
            user_idtag=form_data["user_idtag"].strip(),
            file_idtag=optional_idtag,
        )
        message: str = "File created."
    except Exception as exc:
        message = f"File creation failed: {exc}"

    return RedirectResponse(url=build_admin_url(section="files", message=message), status_code=303)


@router.post("/admin/uploads/model")
async def admin_upload_model(request: Request):
    """
    Import one uploaded model file into the database.

    The request body is streamed as raw binary so large files do not need to be
    base64-encoded in the browser first.

    :param request: Incoming HTTP request.
    :return: JSON upload result.
    """
    redirect_response = require_admin_request(request=request)

    if redirect_response is not None:
        return JSONResponse(
            {
                "success": False,
                "message": "Authentication required.",
                "redirect_url": "/admin/login",
            },
            status_code=401,
        )
    else:
        pass

    temp_path: str = ""
    try:
        encoded_file_name: str = request.headers.get("X-VeraGrid-File-Name", "").strip()
        encoded_user_idtag: str = request.headers.get("X-VeraGrid-User-Idtag", "").strip()
        file_name: str = unquote(encoded_file_name)
        user_idtag: str = unquote(encoded_user_idtag)
        suffix_text: str = Path(file_name).suffix
        bytes_written: int = 0
        chunk: bytes

        if len(file_name) == 0:
            raise ValueError("Missing file name")
        elif len(user_idtag) == 0:
            raise ValueError("Missing owner user idtag")
        else:
            pass

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix_text) as tmp_file:
            temp_path = tmp_file.name

            async for chunk in request.stream():
                if len(chunk) > 0:
                    tmp_file.write(chunk)
                    bytes_written += len(chunk)
                else:
                    pass

        if bytes_written == 0:
            raise ValueError("Missing file content")
        else:
            pass

        file_idtag: str = import_uploaded_model_file(
            file_name=file_name,
            temp_path=temp_path,
            user_idtag=user_idtag,
        )
        return JSONResponse(
            {
                "success": True,
                "message": "Model file imported successfully.",
                "redirect_url": build_admin_url(
                    section="files",
                    message=f"Imported '{file_name}' into file '{file_idtag}'.",
                ),
            }
        )
    except Exception as exc:
        return JSONResponse(
            {
                "success": False,
                "message": f"Upload failed: {exc}",
                "redirect_url": build_admin_url(section="files"),
            },
            status_code=400,
        )
    finally:
        if len(temp_path) > 0 and os.path.exists(temp_path):
            os.unlink(temp_path)
        else:
            pass


@router.post("/admin/files/update")
async def admin_update_file(request: Request):
    """
    Update one file from the admin console.

    :param request: Incoming HTTP request.
    :return: Redirect response.
    """
    redirect_response = require_admin_request(request=request)

    if redirect_response is not None:
        return redirect_response
    else:
        pass

    form_data: Dict[str, str] = parse_request_form(await request.body())

    try:
        update_file(
            file_idtag=form_data["idtag"].strip(),
            file_name=form_data["name"].strip(),
            user_idtag=form_data["user_idtag"].strip(),
        )
        message: str = "File updated."
    except Exception as exc:
        message = f"File update failed: {exc}"

    return RedirectResponse(url=build_admin_url(section="files", message=message), status_code=303)


@router.post("/admin/files/delete")
async def admin_delete_file(request: Request):
    """
    Delete one file from the admin console.

    :param request: Incoming HTTP request.
    :return: Redirect response.
    """
    redirect_response = require_admin_request(request=request)

    if redirect_response is not None:
        return redirect_response
    else:
        pass

    database_settings = get_database_settings_or_none()
    form_data: Dict[str, str] = parse_request_form(await request.body())

    try:
        if database_settings is None:
            raise ValueError("Database settings are not configured")
        else:
            pass

        delete_file(
            settings=database_settings,
            file_idtag=form_data["idtag"].strip(),
        )
        message: str = "File deleted."
    except Exception as exc:
        message = f"File deletion failed: {exc}"

    return RedirectResponse(url=build_admin_url(section="files", message=message), status_code=303)


@router.post("/admin/models/create")
async def admin_create_model(request: Request):
    """
    Create one model metadata row from the admin console.

    :param request: Incoming HTTP request.
    :return: Redirect response.
    """
    redirect_response = require_admin_request(request=request)

    if redirect_response is not None:
        return redirect_response
    else:
        pass

    database_settings = get_database_settings_or_none()
    form_data: Dict[str, str] = parse_request_form(await request.body())

    try:
        if database_settings is None:
            raise ValueError("Database settings are not configured")
        else:
            pass

        optional_parent: str | None = coerce_optional_text(form_data.get("parent_model_idtag", ""))
        optional_idtag: str | None = coerce_optional_text(form_data.get("idtag", ""))
        create_model(
            settings=database_settings,
            file_idtag=form_data["file_idtag"].strip(),
            model_name=form_data["name"].strip(),
            parent_model_idtag=optional_parent,
            model_idtag=optional_idtag,
        )
        message: str = "Model metadata created."
    except Exception as exc:
        message = f"Model creation failed: {exc}"

    return RedirectResponse(url=build_admin_url(section="models", message=message), status_code=303)


@router.post("/admin/models/update")
async def admin_update_model(request: Request):
    """
    Update one model metadata row from the admin console.

    :param request: Incoming HTTP request.
    :return: Redirect response.
    """
    redirect_response = require_admin_request(request=request)

    if redirect_response is not None:
        return redirect_response
    else:
        pass

    database_settings = get_database_settings_or_none()
    form_data: Dict[str, str] = parse_request_form(await request.body())

    try:
        if database_settings is None:
            raise ValueError("Database settings are not configured")
        else:
            pass

        optional_parent: str | None = coerce_optional_text(form_data.get("parent_model_idtag", ""))
        update_model(
            settings=database_settings,
            file_idtag=form_data["file_idtag"].strip(),
            model_idtag=form_data["idtag"].strip(),
            model_name=form_data["name"].strip(),
            parent_model_idtag=optional_parent,
        )
        message: str = "Model updated."
    except Exception as exc:
        message = f"Model update failed: {exc}"

    return RedirectResponse(url=build_admin_url(section="models", message=message), status_code=303)


@router.post("/admin/models/delete")
async def admin_delete_model(request: Request):
    """
    Delete one model metadata row from the admin console.

    :param request: Incoming HTTP request.
    :return: Redirect response.
    """
    redirect_response = require_admin_request(request=request)

    if redirect_response is not None:
        return redirect_response
    else:
        pass

    database_settings = get_database_settings_or_none()
    form_data: Dict[str, str] = parse_request_form(await request.body())

    try:
        if database_settings is None:
            raise ValueError("Database settings are not configured")
        else:
            pass

        delete_model(
            settings=database_settings,
            file_idtag=form_data["file_idtag"].strip(),
            model_idtag=form_data["idtag"].strip(),
            cascade=True,
        )
        message: str = "Model deleted."
    except Exception as exc:
        message = f"Model deletion failed: {exc}"

    return RedirectResponse(url=build_admin_url(section="models", message=message), status_code=303)
