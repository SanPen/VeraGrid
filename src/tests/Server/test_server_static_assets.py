from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import HTTPException
from starlette.responses import FileResponse

from VeraGridServer.main import get_cert, get_server_runtime_path
from VeraGridServer.run import resolve_server_runtime_file_path


def test_get_server_runtime_path_resolves_relative_paths_under_server_package() -> None:
    """
    Check that relative runtime asset paths resolve under the server package directory.

    :return: None.
    """
    resolved_path: Path = get_server_runtime_path(file_name="cert.pem")
    expected_parent: Path = Path(__file__).resolve().parents[2] / "VeraGridServer"

    assert resolved_path == expected_parent / "cert.pem"


def test_resolve_server_runtime_file_path_keeps_absolute_paths() -> None:
    """
    Check that absolute runtime paths pass through unchanged.

    :return: None.
    """
    absolute_path: Path = Path("/tmp/veragrid-cert.pem")

    assert resolve_server_runtime_file_path(file_name=str(absolute_path)) == str(absolute_path)


def test_get_cert_serves_certificate_from_server_runtime_directory(monkeypatch: pytest.MonkeyPatch,
                                                                   tmp_path: Path) -> None:
    """
    Check that the certificate endpoint returns one file response for an existing cert.

    :param monkeypatch: Pytest monkeypatch fixture.
    :param tmp_path: Temporary directory.
    :return: None.
    """
    cert_path: Path = tmp_path / "cert.pem"
    cert_path.write_text("dummy cert", encoding="utf-8")

    monkeypatch.setattr(
        "VeraGridServer.main.get_server_runtime_path",
        lambda file_name: cert_path,
    )

    response = get_cert()

    assert isinstance(response, FileResponse)
    assert response.path == str(cert_path)
    assert response.media_type == "application/x-pem-file"
    assert response.filename == "cert.pem"


def test_get_cert_returns_http_404_when_certificate_is_missing(monkeypatch: pytest.MonkeyPatch,
                                                               tmp_path: Path) -> None:
    """
    Check that the certificate endpoint returns one normal HTTP 404 for a missing cert.

    :param monkeypatch: Pytest monkeypatch fixture.
    :param tmp_path: Temporary directory.
    :return: None.
    """
    cert_path: Path = tmp_path / "missing-cert.pem"

    monkeypatch.setattr(
        "VeraGridServer.main.get_server_runtime_path",
        lambda file_name: cert_path,
    )

    with pytest.raises(HTTPException) as exc_info:
        get_cert()

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Certificate file not found"
