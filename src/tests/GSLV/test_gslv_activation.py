# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Exercise optional-backend startup in fresh interpreters without a native solver."""

import json
from pathlib import Path
import subprocess
import sys

import pytest

@pytest.mark.parametrize(
    'scenario, version, licensed, missing_api, expected_reason, available',
    (
        ('absent', '', False, False, 'not installed', False),
        ('binary_failure', '', False, False, 'native library failed', False),
        ('old', '0.9.4', True, True, 'requires pygslv >= 1.0.0', False),
        ('prerelease', '1.0.0rc1', True, False, 'requires pygslv >= 1.0.0', False),
        ('invalid', 'broken', True, False, 'Invalid version', False),
        ('unlicensed', '1.0.0', False, True, 'no valid license', False),
        ('activation_failure', '1.0.0', False, False, 'license discovery failed', False),
        ('missing_api', '1.0.0', True, True, 'BatteryDispatchMode', False),
        ('compatible', '1.0.0', True, False, '', True),
        ('newer', '1.1.0', True, False, '', True),
    ),
)
def test_backend_startup(
        scenario: str, version: str, licensed: bool,
        missing_api: bool, expected_reason: str, available: bool,
) -> None:
    """Import the complete engine against absent, old, and supported backend APIs.

    :param scenario: Backend installation condition.
    :param version: Backend version.
    :param licensed: License availability.
    :param missing_api: Whether required API symbols are absent.
    :param expected_reason: Required diagnostic fragment.
    :param available: Expected dispatch availability.
    :return: None.
    """
    command: list[str] = [
        sys.executable,
        '-m',
        'tests.GSLV.gslv_activation_worker',
        scenario,
        version,
        str(licensed).lower(),
        str(missing_api).lower(),
    ]
    source_root: Path = Path(__file__).resolve().parents[2]
    result: subprocess.CompletedProcess[str] = subprocess.run(
        command, cwd=source_root, capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    status: list[object] = json.loads(result.stdout.splitlines()[-1])
    assert status[0] is available
    assert status[1] == version
    assert expected_reason in status[2]
    assert status[3] is (
        scenario in ('unlicensed', 'missing_api', 'compatible', 'newer')
    )
    if scenario == 'absent':
        assert 'GSLV disabled' not in result.stderr
    elif available:
        assert status[2] == ''
        assert 'GSLV disabled' not in result.stderr
    else:
        assert 'GSLV disabled' in result.stderr
        assert expected_reason in result.stderr
