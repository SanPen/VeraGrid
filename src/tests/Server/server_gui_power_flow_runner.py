from __future__ import annotations

import asyncio
import json
import os
import socket
import sys
import threading
import time
import traceback
from pathlib import Path

import numpy as np
from PySide6 import QtWidgets
import requests
import uvicorn

import VeraGridEngine.api as vge
from VeraGrid.Gui.Main.SubClasses.io import IoMain
from VeraGridEngine.IO.veragrid.remote import (
    RemoteInstruction,
    gather_model_as_jsons_for_communication,
)
from VeraGridEngine.IO.veragrid.pack_unpack import parse_veragrid_data
from VeraGridEngine.enumerations import SimulationTypes
from VeraGridServer.endpoints import jobs as jobs_endpoint
from VeraGridServer.main import app as server_app


GRID_FOLDER = Path(__file__).resolve().parents[1] / "data" / "grids"
TEST_GRID = GRID_FOLDER / "case14.gridcal"


def _load_grid_in_gui() -> IoMain:
    """
    Build one real GUI instance and install a shipped grid into it.
    """
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    _unused_app = app

    gui = IoMain()
    gui.hide()
    gui.new_project_now(create_default_diagrams=False)
    gui.circuit = vge.open_file(str(TEST_GRID))
    gui.file_name = str(TEST_GRID)
    QtWidgets.QApplication.processEvents()

    assert gui.file_name == str(TEST_GRID)
    assert gui.circuit.get_bus_number() > 0

    return gui


def _get_free_tcp_port() -> int:
    """
    Allocate one free loopback TCP port for the temporary test server.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        sock.listen(1)
        return int(sock.getsockname()[1])


def _start_local_server() -> tuple[uvicorn.Server, threading.Thread, str]:
    """
    Start one real local uvicorn server for the VeraGrid FastAPI app.
    """
    jobs_endpoint.JOBS_LIST.clear()

    port = _get_free_tcp_port()
    base_url = f"http://127.0.0.1:{port}"
    config = uvicorn.Config(server_app, host="127.0.0.1", port=port, log_level="error")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    deadline = time.monotonic() + 30.0
    while time.monotonic() < deadline:
        try:
            response = requests.get(f"{base_url}/", timeout=1.0)
            if response.status_code == 200:
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
    """
    server.should_exit = True
    thread.join(timeout=10.0)
    jobs_endpoint.JOBS_LIST.clear()


def _assert_server_power_flow_matches_local(gui: IoMain) -> None:
    """
    Submit the GUI-loaded circuit to the server endpoint and compare with a local solve.
    """
    local_results = vge.power_flow(gui.circuit)
    local_payload = local_results.get_dict()

    assert local_results.converged

    instruction = RemoteInstruction(operation=SimulationTypes.PowerFlow_run)
    request_payload = gather_model_as_jsons_for_communication(
        circuit=gui.circuit,
        instruction=instruction,
    )
    roundtrip_payload = json.loads(json.dumps(request_payload))

    parsed_grid = parse_veragrid_data(data=request_payload)
    assert parsed_grid.get_bus_number() == gui.circuit.get_bus_number(), (
        f"Direct parse lost buses: {parsed_grid.get_bus_number()} "
        f"vs {gui.circuit.get_bus_number()}"
    )

    roundtrip_grid = parse_veragrid_data(data=roundtrip_payload)
    assert roundtrip_grid.get_bus_number() == gui.circuit.get_bus_number(), (
        f"JSON roundtrip parse lost buses: {roundtrip_grid.get_bus_number()} "
        f"vs {gui.circuit.get_bus_number()}"
    )

    direct_endpoint_payload = asyncio.run(
        jobs_endpoint.process_json_data(json_data=roundtrip_payload)
    )
    assert len(direct_endpoint_payload["voltage"]["real"]) == gui.circuit.get_bus_number(), (
        "Direct endpoint execution returned an unexpected voltage vector size: "
        f"{len(direct_endpoint_payload['voltage']['real'])}"
    )

    server, thread, base_url = _start_local_server()
    try:
        response = requests.post(
            f"{base_url}/upload_job/",
            json=roundtrip_payload,
            timeout=120.0,
        )
    finally:
        _stop_local_server(server, thread)

    assert response.status_code == 200, response.text

    payload = response.json()
    assert payload["success"] is True, payload
    assert payload["results"] is not None
    assert payload["msg"] == "all good"
    assert len(jobs_endpoint.JOBS_LIST) == 0

    server_results = payload["results"]

    if "voltage" not in server_results or "Sf" not in server_results:
        raise AssertionError(
            "Server power-flow payload is missing expected fields. "
            f"Available keys: {sorted(server_results.keys())}"
        )

    assert len(server_results["voltage"]["real"]) == gui.circuit.get_bus_number(), (
        f"Unexpected server voltage count: {len(server_results['voltage']['real'])} "
        f"for {gui.circuit.get_bus_number()} buses"
    )
    assert len(server_results["Sf"]["real"]) == len(local_payload["Sf"]["real"]), (
        f"Unexpected server branch-flow count: {len(server_results['Sf']['real'])} "
        f"for {len(local_payload['Sf']['real'])} branches"
    )

    np.testing.assert_allclose(server_results["voltage"]["real"], local_payload["voltage"]["real"])
    np.testing.assert_allclose(server_results["voltage"]["imag"], local_payload["voltage"]["imag"])
    np.testing.assert_allclose(server_results["Sf"]["real"], local_payload["Sf"]["real"])
    np.testing.assert_allclose(server_results["Sf"]["imag"], local_payload["Sf"]["imag"])


def main() -> None:
    """
    Load one grid through the GUI and run one server-side power-flow regression.
    """
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    if not TEST_GRID.exists():
        raise FileNotFoundError(f"Missing test grid: {TEST_GRID}")

    gui = _load_grid_in_gui()
    _assert_server_power_flow_matches_local(gui)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(1)
    else:
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(0)
