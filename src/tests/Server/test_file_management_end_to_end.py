from __future__ import annotations

import socket
import threading
import time
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
import requests
import uvicorn

import VeraGridEngine.api as vge
from VeraGridServer.db.database import PostgreSqlConnectionSettings
from VeraGridServer.db.model_ops import (
    create_file,
    delete_file,
    get_file_models_json,
    put_multiverse_in_database,
)
from VeraGridServer.endpoints import jobs as jobs_endpoint
from VeraGridServer.main import app as server_app
from VeraGridServer.settings import settings


GRID_FOLDER: Path = Path(__file__).resolve().parents[1] / "data" / "grids"
SERVER_PASSWORD: str = "veragrid is great"


def _assert_circuits_equal(grid1: vge.MultiCircuit, grid2: vge.MultiCircuit) -> None:
    """
    Assert semantic circuit equality and print the engine logger on mismatch.

    :param grid1: First circuit.
    :param grid2: Second circuit.
    :return: None.
    """
    equal: bool
    logger: vge.Logger
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


def _skip_when_local_db_is_unavailable(db_settings: PostgreSqlConnectionSettings) -> None:
    """
    Skip the test when the expected localhost PostgreSQL instance is unreachable.

    :param db_settings: PostgreSQL connection settings.
    :return: None.
    """
    try:
        with psycopg.connect(
            host=db_settings.host,
            port=db_settings.port,
            dbname="postgres",
            user=db_settings.user_name,
            password=db_settings.password,
            connect_timeout=2,
        ) as connection:
            _unused_connection = connection
    except psycopg.Error as exc:
        pytest.skip(f"Local PostgreSQL is not accessible: {exc}")


def _configure_server_settings(db_settings: PostgreSqlConnectionSettings) -> None:
    """
    Point the FastAPI app to the local PostgreSQL instance used by the tests.

    :param db_settings: PostgreSQL connection settings.
    :return: None.
    """
    # The server app reads this module-level settings object at request time,
    # so the tests update it before instantiating the TestClient.
    settings.this_password = SERVER_PASSWORD
    settings.db_host = db_settings.host
    settings.db_port = db_settings.port
    settings.db_name = db_settings.database
    settings.db_user = db_settings.user_name
    settings.db_password = db_settings.password


def _get_api_headers() -> dict[str, str]:
    """
    Build the authenticated API headers for the file-management endpoints.

    :return: HTTP header mapping.
    """
    headers: dict[str, str] = dict()
    headers["API-Key"] = SERVER_PASSWORD
    return headers


def _write_response_to_file(tmp_path: Path, file_name: str, content: bytes) -> Path:
    """
    Persist one HTTP download payload into a temporary archive file.

    :param tmp_path: Pytest temporary directory.
    :param file_name: Archive file name.
    :param content: Raw archive bytes.
    :return: Saved archive path.
    """
    output_path: Path = tmp_path / file_name
    output_path.write_bytes(content)
    return output_path


def _load_circuit_from_archive(file_name: Path) -> vge.MultiCircuit:
    """
    Load one circuit archive and require a flat circuit payload.

    :param file_name: Archive file path.
    :return: Loaded circuit.
    """
    loader: vge.FileOpen = vge.FileOpen(str(file_name))
    loaded_circuit: vge.MultiCircuit | None = loader.open()

    if loaded_circuit is None:
        raise AssertionError(f"Expected a circuit in '{file_name}'")
    else:
        return loaded_circuit


def _load_multiverse_from_archive(file_name: Path) -> vge.MultiVerse:
    """
    Load one archive and require a multiverse payload.

    :param file_name: Archive file path.
    :return: Loaded multiverse.
    """
    loader: vge.FileOpen = vge.FileOpen(str(file_name))
    _loaded_circuit: vge.MultiCircuit | None = loader.open()

    if loader.multiverse is None:
        raise AssertionError(f"Expected a multiverse in '{file_name}'")
    else:
        return loader.multiverse


def _save_circuit_to_archive(circuit: vge.MultiCircuit, file_name: Path) -> None:
    """
    Save one flat circuit into a VeraGrid-compatible archive.

    :param circuit: Circuit to serialize.
    :param file_name: Output archive path.
    :return: None.
    """
    vge.save_file(grid=circuit, filename=str(file_name))


def _save_multiverse_to_archive(multiverse: vge.MultiVerse, file_name: Path) -> None:
    """
    Save one multiverse into a VeraGrid archive.

    :param multiverse: Multiverse to serialize.
    :param file_name: Output archive path.
    :return: None.
    """
    vge.save_multiverse(mv=multiverse, filename=str(file_name))


def _delete_file_if_present(db_settings: PostgreSqlConnectionSettings, file_idtag: str) -> None:
    """
    Remove one test file row when it still exists.

    :param db_settings: PostgreSQL connection settings.
    :param file_idtag: File identifier.
    :return: None.
    """
    file_json: dict[str, object] | None = get_file_models_json(
        settings=db_settings,
        file_idtag=file_idtag,
    )

    if file_json is None:
        pass
    else:
        delete_file(settings=db_settings, file_idtag=file_idtag)


def _build_unique_name(prefix: str) -> str:
    """
    Create one deterministic-enough test artifact name.

    :param prefix: Human-readable prefix.
    :return: Unique name string.
    """
    return f"{prefix}_{uuid4().hex}"


def _get_free_tcp_port() -> int:
    """
    Allocate one free loopback TCP port for the temporary test server.

    :return: Free TCP port.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        sock.listen(1)
        return int(sock.getsockname()[1])


def _start_local_server() -> tuple[uvicorn.Server, threading.Thread, str]:
    """
    Start one real local uvicorn server for the VeraGrid FastAPI app.

    :return: Running server, backing thread, and base URL.
    """
    jobs_endpoint.JOBS_LIST.clear()

    port: int = _get_free_tcp_port()
    base_url: str = f"http://127.0.0.1:{port}"
    config: uvicorn.Config = uvicorn.Config(server_app, host="127.0.0.1", port=port, log_level="error")
    server: uvicorn.Server = uvicorn.Server(config)
    thread: threading.Thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    deadline: float = time.monotonic() + 30.0
    while time.monotonic() < deadline:
        try:
            response: requests.Response = requests.get(
                f"{base_url}/",
                timeout=1.0,
                allow_redirects=False,
            )
            if response.status_code in {200, 303, 307}:
                return server, thread, base_url
            else:
                pass
        except requests.RequestException:
            pass

        time.sleep(0.05)

    raise TimeoutError("Timed out waiting for the local VeraGrid server to start")


def _stop_local_server(server: uvicorn.Server, thread: threading.Thread) -> None:
    """
    Stop the temporary uvicorn server and wait for its thread to exit.

    :param server: Uvicorn server instance.
    :param thread: Backing server thread.
    :return: None.
    """
    server.should_exit = True
    thread.join(timeout=10.0)
    jobs_endpoint.JOBS_LIST.clear()


def test_single_model_crud_via_file_management_api(tmp_path: Path) -> None:
    """
    Verify flat single-model file CRUD through the file-management API.

    :param tmp_path: Pytest temporary directory.
    :return: None.
    """
    db_settings: PostgreSqlConnectionSettings = _get_local_db_settings()
    _skip_when_local_db_is_unavailable(db_settings=db_settings)
    _configure_server_settings(db_settings=db_settings)

    source_grid: vge.MultiCircuit = vge.open_file(str(GRID_FOLDER / "case14.gridcal"))
    file_idtag: str = create_file(
        settings=db_settings,
        file_name=_build_unique_name("server_single_model"),
        user_idtag="admin",
    )
    try:
        # Seed the file once directly in the DB, because the public API only
        # exposes read/update/delete for the file row itself.
        single_multiverse: vge.MultiVerse = vge.MultiVerse(source_grid)
        model_idtag: str = single_multiverse.root_nodes[0].circuit.idtag
        put_multiverse_in_database(
            settings=db_settings,
            multiverse=single_multiverse,
            file_idtag=file_idtag,
            user_idtag="admin",
        )

        headers: dict[str, str] = _get_api_headers()

        server: uvicorn.Server
        thread: threading.Thread
        base_url: str
        server, thread, base_url = _start_local_server()

        try:
            list_response = requests.get(f"{base_url}/api/db/files", headers=headers, timeout=30.0)
            assert list_response.status_code == 200

            files_payload: list[dict[str, object]] = list_response.json()
            current_file_payload: dict[str, object] = next(
                file_json for file_json in files_payload if str(file_json["idtag"]) == file_idtag
            )

            assert current_file_payload["user"] == "admin"
            assert isinstance(current_file_payload["created_at"], str)
            assert len(str(current_file_payload["created_at"])) > 0
            assert len(list(current_file_payload["models"])) == 1

            get_response = requests.get(f"{base_url}/api/db/files/{file_idtag}", headers=headers, timeout=30.0)
            assert get_response.status_code == 200
            assert get_response.json()["idtag"] == file_idtag

            base_download = requests.get(
                f"{base_url}/api/db/files/{file_idtag}/download",
                headers=headers,
                params={"base_only": True},
                timeout=120.0,
            )
            assert base_download.status_code == 200
            base_file_name: Path = _write_response_to_file(
                tmp_path=tmp_path,
                file_name="single_base_download.veragrid",
                content=base_download.content,
            )
            base_grid: vge.MultiCircuit = _load_circuit_from_archive(file_name=base_file_name)
            _assert_circuits_equal(source_grid, base_grid)

            model_download = requests.get(
                f"{base_url}/api/db/files/{file_idtag}/download",
                headers=headers,
                params={"model_idtag": model_idtag},
                timeout=120.0,
            )
            assert model_download.status_code == 200
            model_file_name: Path = _write_response_to_file(
                tmp_path=tmp_path,
                file_name="single_model_download.veragrid",
                content=model_download.content,
            )
            downloaded_model_grid: vge.MultiCircuit = _load_circuit_from_archive(file_name=model_file_name)
            _assert_circuits_equal(source_grid, downloaded_model_grid)

            full_download = requests.get(
                f"{base_url}/api/db/files/{file_idtag}/download",
                headers=headers,
                timeout=120.0,
            )
            assert full_download.status_code == 200
            full_file_name: Path = _write_response_to_file(
                tmp_path=tmp_path,
                file_name="single_full_download.veragrid",
                content=full_download.content,
            )
            downloaded_multiverse: vge.MultiVerse = _load_multiverse_from_archive(file_name=full_file_name)
            assert downloaded_multiverse.roots_number() == 1
            _assert_circuits_equal(source_grid, downloaded_multiverse.current_model)

            # Update the stored single model through the same replace endpoint used by the GUI.
            modified_grid: vge.MultiCircuit = source_grid.copy()
            modified_grid.lines[0].name = "server_api_single_model_update"
            upload_file_name: Path = tmp_path / "single_model_update.veragrid"
            _save_circuit_to_archive(circuit=modified_grid, file_name=upload_file_name)

            replace_response = requests.post(
                f"{base_url}/api/db/files/{file_idtag}/replace",
                headers={
                    "API-Key": SERVER_PASSWORD,
                    "Content-Type": "application/octet-stream",
                    "X-VeraGrid-File-Name": upload_file_name.name,
                },
                data=upload_file_name.read_bytes(),
                timeout=120.0,
            )
            assert replace_response.status_code == 200
            assert bool(replace_response.json()["success"]) is True

            updated_download = requests.get(
                f"{base_url}/api/db/files/{file_idtag}/download",
                headers=headers,
                params={"base_only": True},
                timeout=120.0,
            )
            assert updated_download.status_code == 200
            updated_file_name: Path = _write_response_to_file(
                tmp_path=tmp_path,
                file_name="single_model_updated_download.veragrid",
                content=updated_download.content,
            )
            updated_grid: vge.MultiCircuit = _load_circuit_from_archive(file_name=updated_file_name)
            _assert_circuits_equal(modified_grid, updated_grid)

            delete_response = requests.delete(f"{base_url}/api/db/files/{file_idtag}", headers=headers, timeout=30.0)
            assert delete_response.status_code == 200

            missing_response = requests.get(f"{base_url}/api/db/files/{file_idtag}", headers=headers, timeout=30.0)
            assert missing_response.status_code == 404
        finally:
            _stop_local_server(server=server, thread=thread)
    finally:
        _delete_file_if_present(db_settings=db_settings, file_idtag=file_idtag)


def test_multiverse_model_crud_via_file_management_api(tmp_path: Path) -> None:
    """
    Verify multiverse model read, update, and delete through the file-management API.

    :param tmp_path: Pytest temporary directory.
    :return: None.
    """
    db_settings: PostgreSqlConnectionSettings = _get_local_db_settings()
    _skip_when_local_db_is_unavailable(db_settings=db_settings)
    _configure_server_settings(db_settings=db_settings)

    base_grid: vge.MultiCircuit = vge.open_file(str(GRID_FOLDER / "lynn5node.gridcal"))
    multiverse: vge.MultiVerse = vge.MultiVerse(base_grid)
    root_node: vge.ScenarioNode = multiverse.root_nodes[0]
    child_node: vge.ScenarioNode = multiverse.create_node(
        data=vge.MultiCircuit(name="server child"),
        parent_id=root_node.node_id,
        position=root_node.child_count(),
    )

    # The child scenario must be materialized through delta storage so the test
    # exercises the same multiverse semantics that the server stores.
    multiverse.activate_scenario(child_node.node_id)
    multiverse.current_model.lines[0].name = "server_multiverse_child_override"
    multiverse.commit_current()

    child_before_upload: vge.MultiCircuit = multiverse.checkout(child_node)

    file_idtag: str = create_file(
        settings=db_settings,
        file_name=_build_unique_name("server_multiverse"),
        user_idtag="admin",
    )

    try:
        put_multiverse_in_database(
            settings=db_settings,
            multiverse=multiverse,
            file_idtag=file_idtag,
            user_idtag="admin",
        )

        headers: dict[str, str] = _get_api_headers()

        server: uvicorn.Server
        thread: threading.Thread
        base_url: str
        server, thread, base_url = _start_local_server()

        try:
            file_response = requests.get(f"{base_url}/api/db/files/{file_idtag}", headers=headers, timeout=30.0)
            assert file_response.status_code == 200

            file_payload: dict[str, object] = file_response.json()
            models_payload: list[dict[str, object]] = list(file_payload["models"])
            assert len(models_payload) == 2
            assert any(bool(model_json["is_base_model"]) for model_json in models_payload)
            assert any(
                str(model_json["parent_model_idtag"]) == root_node.circuit.idtag
                for model_json in models_payload
                if model_json["parent_model_idtag"] is not None
            )

            full_download = requests.get(
                f"{base_url}/api/db/files/{file_idtag}/download",
                headers=headers,
                timeout=120.0,
            )
            assert full_download.status_code == 200
            full_file_name: Path = _write_response_to_file(
                tmp_path=tmp_path,
                file_name="multiverse_download.veragrid",
                content=full_download.content,
            )
            loaded_multiverse: vge.MultiVerse = _load_multiverse_from_archive(file_name=full_file_name)
            loaded_child_node: vge.ScenarioNode = next(
                node for node in loaded_multiverse.iter_nodes_depth_first()
                if node.circuit.idtag == child_node.circuit.idtag
            )
            loaded_child_grid: vge.MultiCircuit = loaded_multiverse.checkout(loaded_child_node)
            _assert_circuits_equal(child_before_upload, loaded_child_grid)

            child_download = requests.get(
                f"{base_url}/api/db/files/{file_idtag}/download",
                headers=headers,
                params={"model_idtag": child_node.circuit.idtag},
                timeout=120.0,
            )
            assert child_download.status_code == 200
            child_file_name: Path = _write_response_to_file(
                tmp_path=tmp_path,
                file_name="multiverse_child_download.veragrid",
                content=child_download.content,
            )
            child_grid: vge.MultiCircuit = _load_circuit_from_archive(file_name=child_file_name)
            _assert_circuits_equal(child_before_upload, child_grid)

            # Update the full multiverse by adding one sibling scenario and re-uploading the archive.
            updated_multiverse: vge.MultiVerse = multiverse
            sibling_node: vge.ScenarioNode = updated_multiverse.create_node(
                data=vge.MultiCircuit(name="server sibling"),
                parent_id=root_node.node_id,
                position=root_node.child_count(),
            )
            updated_multiverse.activate_scenario(sibling_node.node_id)
            updated_multiverse.current_model.lines[0].name = "server_multiverse_sibling_override"
            updated_multiverse.commit_current()

            upload_file_name: Path = tmp_path / "multiverse_update.veragrid"
            _save_multiverse_to_archive(multiverse=updated_multiverse, file_name=upload_file_name)

            replace_response = requests.post(
                f"{base_url}/api/db/files/{file_idtag}/replace",
                headers={
                    "API-Key": SERVER_PASSWORD,
                    "Content-Type": "application/octet-stream",
                    "X-VeraGrid-File-Name": upload_file_name.name,
                },
                data=upload_file_name.read_bytes(),
                timeout=120.0,
            )
            assert replace_response.status_code == 200

            updated_file_response = requests.get(
                f"{base_url}/api/db/files/{file_idtag}",
                headers=headers,
                timeout=30.0,
            )
            assert updated_file_response.status_code == 200
            updated_models_payload: list[dict[str, object]] = list(updated_file_response.json()["models"])
            assert len(updated_models_payload) == 3

            delete_response = requests.delete(
                f"{base_url}/api/db/files/{file_idtag}/models/{child_node.circuit.idtag}",
                headers=headers,
                timeout=30.0,
            )
            assert delete_response.status_code == 200

            after_delete_response = requests.get(
                f"{base_url}/api/db/files/{file_idtag}",
                headers=headers,
                timeout=30.0,
            )
            assert after_delete_response.status_code == 200
            remaining_models_payload: list[dict[str, object]] = list(after_delete_response.json()["models"])
            assert len(remaining_models_payload) == 2
            assert all(
                str(model_json["idtag"]) != child_node.circuit.idtag
                for model_json in remaining_models_payload
            )
        finally:
            _stop_local_server(server=server, thread=thread)
    finally:
        _delete_file_if_present(db_settings=db_settings, file_idtag=file_idtag)


def test_single_model_diff_roundtrip_via_file_management_api(tmp_path: Path) -> None:
    """
    Verify one time-series differential model survives upload/download through the file API.

    :param tmp_path: Pytest temporary directory.
    :return: None.
    """
    db_settings: PostgreSqlConnectionSettings = _get_local_db_settings()
    _skip_when_local_db_is_unavailable(db_settings=db_settings)
    _configure_server_settings(db_settings=db_settings)

    original_grid: vge.MultiCircuit = vge.open_file(str(GRID_FOLDER / "IEEE39_1W.gridcal"))
    modified_grid: vge.MultiCircuit = vge.open_file(str(GRID_FOLDER / "IEEE39_1W.gridcal"))

    assert original_grid.time_profile is not None
    assert modified_grid.time_profile is not None

    # The diff must include both topology-state changes and time-series profile changes.
    modified_grid.buses[0].active_prof[0] = not modified_grid.buses[0].active_prof[0]
    modified_grid.loads[0].P_prof[0] *= 1.1

    diff_ok: bool
    diff_logger: vge.Logger
    diff_grid: vge.MultiCircuit
    diff_ok, diff_logger, diff_grid = modified_grid.differentiate_circuits(base_grid=original_grid)

    if not diff_ok:
        diff_logger.print()
    else:
        pass

    assert diff_ok
    assert diff_grid.time_profile is not None

    file_idtag: str = create_file(
        settings=db_settings,
        file_name=_build_unique_name("server_single_diff"),
        user_idtag="admin",
    )

    try:
        upload_file_name: Path = tmp_path / "single_diff_upload.dveragrid"
        _save_circuit_to_archive(circuit=diff_grid, file_name=upload_file_name)

        headers: dict[str, str] = _get_api_headers()

        server: uvicorn.Server
        thread: threading.Thread
        base_url: str
        server, thread, base_url = _start_local_server()

        try:
            replace_response = requests.post(
                f"{base_url}/api/db/files/{file_idtag}/replace",
                headers={
                    "API-Key": SERVER_PASSWORD,
                    "Content-Type": "application/octet-stream",
                    "X-VeraGrid-File-Name": upload_file_name.name,
                },
                data=upload_file_name.read_bytes(),
                timeout=120.0,
            )
            assert replace_response.status_code == 200

            file_response = requests.get(f"{base_url}/api/db/files/{file_idtag}", headers=headers, timeout=30.0)
            assert file_response.status_code == 200
            models_payload: list[dict[str, object]] = list(file_response.json()["models"])
            assert len(models_payload) == 1
            uploaded_model_idtag: str = str(models_payload[0]["idtag"])

            diff_download = requests.get(
                f"{base_url}/api/db/files/{file_idtag}/download",
                headers=headers,
                params={"model_idtag": uploaded_model_idtag},
                timeout=120.0,
            )
            assert diff_download.status_code == 200
            diff_file_name: Path = _write_response_to_file(
                tmp_path=tmp_path,
                file_name="single_diff_download.dveragrid",
                content=diff_download.content,
            )
            downloaded_diff: vge.MultiCircuit = _load_circuit_from_archive(file_name=diff_file_name)

            reconstructed_grid: vge.MultiCircuit = original_grid.copy()
            reconstructed_grid.merge_circuit(downloaded_diff)
            _assert_circuits_equal(modified_grid, reconstructed_grid)

            # Deleting the base model through the model endpoint must delete the entire file.
            delete_response = requests.delete(
                f"{base_url}/api/db/files/{file_idtag}/models/{uploaded_model_idtag}",
                headers=headers,
                timeout=30.0,
            )
            assert delete_response.status_code == 200

            missing_response = requests.get(f"{base_url}/api/db/files/{file_idtag}", headers=headers, timeout=30.0)
            assert missing_response.status_code == 404
        finally:
            _stop_local_server(server=server, thread=thread)
    finally:
        _delete_file_if_present(db_settings=db_settings, file_idtag=file_idtag)


def test_multiverse_diff_roundtrip_via_file_management_api(tmp_path: Path) -> None:
    """
    Verify one time-series multiverse delta survives upload/download through the file API.

    :param tmp_path: Pytest temporary directory.
    :return: None.
    """
    db_settings: PostgreSqlConnectionSettings = _get_local_db_settings()
    _skip_when_local_db_is_unavailable(db_settings=db_settings)
    _configure_server_settings(db_settings=db_settings)

    base_grid: vge.MultiCircuit = vge.open_file(str(GRID_FOLDER / "IEEE39_1W.gridcal"))
    multiverse: vge.MultiVerse = vge.MultiVerse(base_grid)
    root_node: vge.ScenarioNode = multiverse.root_nodes[0]
    child_node: vge.ScenarioNode = multiverse.create_node(
        data=vge.MultiCircuit(name="ieee39 child"),
        parent_id=root_node.node_id,
        position=root_node.child_count(),
    )

    # The child keeps only the differential payload in storage, so these edits
    # exercise the server-side delta reconstruction path.
    multiverse.activate_scenario(child_node.node_id)
    multiverse.current_model.buses[0].active_prof[0] = not multiverse.current_model.buses[0].active_prof[0]
    multiverse.current_model.loads[0].P_prof[0] *= 0.95
    multiverse.commit_current()

    expected_child_grid: vge.MultiCircuit = multiverse.checkout(child_node)
    file_idtag: str = create_file(
        settings=db_settings,
        file_name=_build_unique_name("server_multiverse_diff"),
        user_idtag="admin",
    )

    try:
        upload_file_name: Path = tmp_path / "multiverse_diff_upload.veragrid"
        _save_multiverse_to_archive(multiverse=multiverse, file_name=upload_file_name)

        headers: dict[str, str] = _get_api_headers()

        server: uvicorn.Server
        thread: threading.Thread
        base_url: str
        server, thread, base_url = _start_local_server()

        try:
            replace_response = requests.post(
                f"{base_url}/api/db/files/{file_idtag}/replace",
                headers={
                    "API-Key": SERVER_PASSWORD,
                    "Content-Type": "application/octet-stream",
                    "X-VeraGrid-File-Name": upload_file_name.name,
                },
                data=upload_file_name.read_bytes(),
                timeout=120.0,
            )
            assert replace_response.status_code == 200

            file_response = requests.get(f"{base_url}/api/db/files/{file_idtag}", headers=headers, timeout=30.0)
            assert file_response.status_code == 200
            models_payload: list[dict[str, object]] = list(file_response.json()["models"])
            child_model_payload: dict[str, object] = next(
                model_json for model_json in models_payload if model_json["parent_model_idtag"] is not None
            )

            full_download = requests.get(
                f"{base_url}/api/db/files/{file_idtag}/download",
                headers=headers,
                timeout=120.0,
            )
            assert full_download.status_code == 200
            full_file_name: Path = _write_response_to_file(
                tmp_path=tmp_path,
                file_name="multiverse_diff_download.veragrid",
                content=full_download.content,
            )
            loaded_multiverse: vge.MultiVerse = _load_multiverse_from_archive(file_name=full_file_name)
            loaded_child_node: vge.ScenarioNode = next(
                node for node in loaded_multiverse.iter_nodes_depth_first() if node.parent is not None
            )
            loaded_child_grid: vge.MultiCircuit = loaded_multiverse.checkout(loaded_child_node)
            _assert_circuits_equal(expected_child_grid, loaded_child_grid)

            child_download = requests.get(
                f"{base_url}/api/db/files/{file_idtag}/download",
                headers=headers,
                params={"model_idtag": str(child_model_payload["idtag"])},
                timeout=120.0,
            )
            assert child_download.status_code == 200
            child_file_name: Path = _write_response_to_file(
                tmp_path=tmp_path,
                file_name="multiverse_diff_child_download.veragrid",
                content=child_download.content,
            )
            loaded_child_flat_grid: vge.MultiCircuit = _load_circuit_from_archive(file_name=child_file_name)
            _assert_circuits_equal(expected_child_grid, loaded_child_flat_grid)
        finally:
            _stop_local_server(server=server, thread=thread)
    finally:
        _delete_file_if_present(db_settings=db_settings, file_idtag=file_idtag)
