# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import hmac
import os
import tempfile
from typing import Any, Dict, List
from urllib.parse import unquote

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from starlette.background import BackgroundTask

from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Devices.multiverse import MultiVerse
from VeraGridEngine.IO.file_open import FileOpen
from VeraGridEngine.IO.file_save import FileSave, FileSavingOptions
from VeraGridServer.db.model_ops import (
    delete_file,
    delete_model,
    get_file,
    get_file_models_json,
    get_files_with_models_json,
    get_multicircuit_from_database,
    get_multiverse_from_database,
    put_multiverse_in_database,
)
from VeraGridServer.settings import settings


router = APIRouter(prefix="/api/db")


def verify_api_key_header(api_key: str | None = Header(default=None, alias="API-Key")) -> None:
    """
    Validate one API key against the configured server password.

    :param api_key: Incoming API key header.
    :return: None.
    """
    if api_key is None:
        raise HTTPException(status_code=401, detail="API Key is missing")
    else:
        pass

    expected_api_key: str = settings.this_password

    if len(expected_api_key) == 0:
        raise HTTPException(status_code=503, detail="API key verification is not configured")
    elif not hmac.compare_digest(api_key, expected_api_key):
        raise HTTPException(status_code=403, detail="Invalid API Key")
    else:
        pass


def get_database_settings_or_raise():
    """
    Resolve the configured database settings or raise one HTTP error.

    :return: PostgreSQL connection settings.
    """
    database_settings = settings.get_database_settings()

    if database_settings is None:
        raise HTTPException(status_code=503, detail="Database configuration is incomplete")
    else:
        return database_settings


def remove_file_if_exists(file_path: str) -> None:
    """
    Remove one temporary file when it exists.

    :param file_path: Temporary file path.
    :return: None.
    """
    if os.path.exists(file_path):
        os.unlink(file_path)
    else:
        pass


def save_multiverse_to_temporary_file(multiverse: MultiVerse) -> str:
    """
    Serialize one multiverse into a temporary VeraGrid archive.

    :param multiverse: Multiverse to serialize.
    :return: Temporary file path.
    """
    options: FileSavingOptions = FileSavingOptions()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".veragrid") as tmp_file:
        temp_path: str = tmp_file.name

    saver: FileSave = FileSave(
        circuit=multiverse.current_model,
        file_name=temp_path,
        options=options,
        multiverse=multiverse,
    )
    saver.save()
    return temp_path


def save_circuit_to_temporary_file(circuit: MultiCircuit) -> str:
    """
    Serialize one circuit into a temporary VeraGrid archive.

    :param circuit: Circuit to serialize.
    :return: Temporary file path.
    """
    options: FileSavingOptions = FileSavingOptions()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".veragrid") as tmp_file:
        temp_path: str = tmp_file.name

    saver: FileSave = FileSave(
        circuit=circuit,
        file_name=temp_path,
        options=options,
        multiverse=None,
    )
    saver.save()
    return temp_path


@router.get("/files")
def list_database_files(api_key: str | None = Header(default=None, alias="API-Key")) -> List[Dict[str, Any]]:
    """
    List every stored file and its nested model rows.

    :param api_key: API key header.
    :return: File tree JSON payload.
    """
    verify_api_key_header(api_key=api_key)
    database_settings = get_database_settings_or_raise()
    return get_files_with_models_json(settings=database_settings)


@router.get("/files/{file_idtag}")
def get_database_file(file_idtag: str,
                      api_key: str | None = Header(default=None, alias="API-Key")) -> Dict[str, Any]:
    """
    Read one stored file and its nested model rows.

    :param file_idtag: File identifier.
    :param api_key: API key header.
    :return: File JSON payload.
    """
    verify_api_key_header(api_key=api_key)
    database_settings = get_database_settings_or_raise()
    file_payload: Dict[str, Any] | None = get_file_models_json(settings=database_settings, file_idtag=file_idtag)

    if file_payload is None:
        raise HTTPException(status_code=404, detail="File not found")
    else:
        return file_payload


@router.get("/files/{file_idtag}/download")
def download_database_file(file_idtag: str,
                           model_idtag: str = "",
                           base_only: bool = False,
                           api_key: str | None = Header(default=None, alias="API-Key")) -> FileResponse:
    """
    Download one stored file or one selected model as a VeraGrid archive.

    :param file_idtag: File identifier.
    :param model_idtag: Optional model identifier to export as one flat circuit.
    :param base_only: Export only the base model when ``True``.
    :param api_key: API key header.
    :return: Streaming file response.
    """
    verify_api_key_header(api_key=api_key)
    database_settings = get_database_settings_or_raise()
    file_row: Dict[str, str] | None = get_file(settings=database_settings, file_idtag=file_idtag)

    if file_row is None:
        raise HTTPException(status_code=404, detail="File not found")
    else:
        pass

    if len(model_idtag.strip()) > 0:
        circuit: MultiCircuit = get_multicircuit_from_database(
            settings=database_settings,
            file_idtag=file_idtag,
            model_idtag=model_idtag.strip(),
        )
        temp_path: str = save_circuit_to_temporary_file(circuit=circuit)
        download_name: str = f"{circuit.name or model_idtag}.veragrid"
    elif base_only:
        circuit = get_multicircuit_from_database(
            settings=database_settings,
            file_idtag=file_idtag,
            model_idtag=None,
        )
        temp_path = save_circuit_to_temporary_file(circuit=circuit)
        download_name = f"{circuit.name or file_row['name']}.veragrid"
    else:
        multiverse: MultiVerse = get_multiverse_from_database(
            settings=database_settings,
            file_idtag=file_idtag,
        )
        temp_path = save_multiverse_to_temporary_file(multiverse=multiverse)
        download_name = f"{file_row['name']}.veragrid"

    return FileResponse(
        path=temp_path,
        filename=download_name,
        media_type="application/octet-stream",
        background=BackgroundTask(remove_file_if_exists, temp_path),
    )


@router.delete("/files/{file_idtag}")
def delete_database_file(file_idtag: str,
                         api_key: str | None = Header(default=None, alias="API-Key")) -> Dict[str, str]:
    """
    Delete one stored file and every model contained in it.

    :param file_idtag: File identifier.
    :param api_key: API key header.
    :return: Result payload.
    """
    verify_api_key_header(api_key=api_key)
    database_settings = get_database_settings_or_raise()
    delete_file(settings=database_settings, file_idtag=file_idtag)
    return {"message": f"File '{file_idtag}' deleted"}


@router.delete("/files/{file_idtag}/models/{model_idtag}")
def delete_database_model(file_idtag: str,
                          model_idtag: str,
                          api_key: str | None = Header(default=None, alias="API-Key")) -> Dict[str, str]:
    """
    Delete one stored model or the whole file when the model is the base node.

    :param file_idtag: File identifier.
    :param model_idtag: Model identifier.
    :param api_key: API key header.
    :return: Result payload.
    """
    verify_api_key_header(api_key=api_key)
    database_settings = get_database_settings_or_raise()
    file_payload: Dict[str, Any] | None = get_file_models_json(settings=database_settings, file_idtag=file_idtag)

    if file_payload is None:
        raise HTTPException(status_code=404, detail="File not found")
    else:
        pass

    model_payload: Dict[str, Any] | None = None
    model_entry: Dict[str, Any]
    for model_entry in file_payload["models"]:
        if str(model_entry["idtag"]) == model_idtag:
            model_payload = model_entry
        else:
            pass

    if model_payload is None:
        raise HTTPException(status_code=404, detail="Model not found")
    elif bool(model_payload["is_base_model"]):
        delete_file(settings=database_settings, file_idtag=file_idtag)
        return {"message": f"Base model '{model_idtag}' deleted together with file '{file_idtag}'"}
    else:
        delete_model(
            settings=database_settings,
            file_idtag=file_idtag,
            model_idtag=model_idtag,
            cascade=True,
        )
        return {"message": f"Model '{model_idtag}' deleted"}


@router.post("/files/{file_idtag}/replace")
async def replace_database_file(file_idtag: str,
                                request: Request,
                                api_key: str | None = Header(default=None, alias="API-Key")) -> JSONResponse:
    """
    Replace one stored file contents from one uploaded VeraGrid-compatible archive.

    :param file_idtag: File identifier.
    :param request: Incoming HTTP request.
    :param api_key: API key header.
    :return: JSON result payload.
    """
    verify_api_key_header(api_key=api_key)
    database_settings = get_database_settings_or_raise()
    file_row: Dict[str, str] | None = get_file(settings=database_settings, file_idtag=file_idtag)

    if file_row is None:
        raise HTTPException(status_code=404, detail="File not found")
    else:
        pass

    encoded_upload_name: str = request.headers.get("X-VeraGrid-File-Name", "").strip()
    upload_name: str = unquote(encoded_upload_name)
    resolved_upload_name: str
    if len(upload_name) > 0:
        resolved_upload_name = upload_name
    else:
        resolved_upload_name = file_row["name"]

    suffix_text: str = os.path.splitext(resolved_upload_name)[1]
    if len(suffix_text) == 0:
        suffix_text = ".veragrid"
    else:
        pass

    temp_path: str = ""
    bytes_written: int = 0
    chunk: bytes

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix_text) as tmp_file:
            temp_path = tmp_file.name

            async for chunk in request.stream():
                if len(chunk) > 0:
                    tmp_file.write(chunk)
                    bytes_written += len(chunk)
                else:
                    pass

        if bytes_written == 0:
            raise HTTPException(status_code=400, detail="Missing file content")
        else:
            pass

        loader: FileOpen = FileOpen(file_name=temp_path)
        loaded_circuit: MultiCircuit | None = loader.open()
        owner_idtag: str = file_row["user"]

        if loader.multiverse is not None:
            put_multiverse_in_database(
                settings=database_settings,
                multiverse=loader.multiverse,
                file_idtag=file_idtag,
                user_idtag=owner_idtag,
                file_name=resolved_upload_name,
            )
        elif loaded_circuit is not None:
            replacement_multiverse: MultiVerse = MultiVerse(current_model=loaded_circuit)
            put_multiverse_in_database(
                settings=database_settings,
                multiverse=replacement_multiverse,
                file_idtag=file_idtag,
                user_idtag=owner_idtag,
                file_name=resolved_upload_name,
            )
        else:
            raise HTTPException(status_code=400, detail="The uploaded file could not be parsed into a grid")

        return JSONResponse(
            {
                "success": True,
                "message": f"File '{file_idtag}' replaced successfully.",
            }
        )
    finally:
        if len(temp_path) > 0:
            remove_file_if_exists(temp_path)
        else:
            pass
