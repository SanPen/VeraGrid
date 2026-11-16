# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Run one isolated optional-pygslv startup scenario for the activation test."""

from __future__ import annotations

import json
import importlib
import importlib.abc
import sys
from types import ModuleType


def _parse_bool(value: str) -> bool:
    """Parse one command-line boolean value.

    :param value: Lower-case command-line boolean spelling.
    :return: Parsed boolean value.
    """
    if value == "true":
        return True
    else:
        return False


class _FakeEnums:
    """Provide every enum member read by the optional backend adapter."""

    Planned = 1
    Commissioned = 2
    Candidate = 3
    Decommissioned = 4
    PlannedDecommission = 5
    fixed = 6
    Qf = 7
    Qt = 8
    Vm = 9
    Pf = 10
    Pt = 11
    Q = 12
    V = 13
    QVDroop = 14
    Grid = 15
    PlantChargeGridDischarge = 16
    PlantChargeAndDisCharge = 17
    Vmin = 18
    Vmax = 19
    Loading = 20
    ContingencyLoading = 21
    type_0_free = 22
    type_1_Pset = 23
    GenericGroup = 24
    TransformerGroup = 25
    LineSegmentsGroup = 26
    Active = 27
    PowerPercentage = 28
    PTDF = 29
    PowerFlow = 30
    HELM = 31
    Vm_dc = 32
    Vm_ac = 33
    Va_ac = 34
    Q_ac = 35
    P_dc = 36
    P_ac = 37
    P_dc_angle_droop = 38
    P_dc_droop = 39
    Q_droop = 40
    P_droop = 41
    Imax = 42
    Fault1 = 43
    Fault2 = 44
    PQ = 45
    PV = 46
    Slack = 47
    P = 48
    PQV = 49
    GroundedStar = 50
    FloatingStar = 51
    NeutralStar = 52
    Delta = 53
    NeutralZigZag = 54
    FloatingZigZag = 55
    GroundedZigZag = 56


class _MissingPygslvFinder(importlib.abc.MetaPathFinder):
    """Make the isolated absent-backend scenario independent of local installs."""

    def find_spec(
            self, fullname: str, path: object, target: object,
    ) -> object:
        """Reject only pygslv and defer every other import to Python.

        :param fullname: Absolute module name requested by the importer.
        :param path: Parent package search path, when applicable.
        :param target: Existing module used by reloads, when applicable.
        :return: No custom module specification for unrelated modules.
        """
        if fullname == "pygslv":
            raise ModuleNotFoundError("No module named 'pygslv'", name="pygslv")
        else:
            return None


class _VersionReader:
    """Return a selected version or model native library startup failure."""

    __slots__ = ("_scenario", "_version")

    def __init__(self, scenario: str, version: str) -> None:
        """Store the requested backend behavior.

        :param scenario: Backend startup condition.
        :param version: Version reported by a working backend.
        :return: None.
        """
        self._scenario = scenario
        self._version = version

    def __call__(self) -> str:
        """Return the version after the simulated native load boundary.

        :return: Backend version string.
        """
        if self._scenario == "binary_failure":
            raise OSError("native library failed")
        else:
            return self._version


class _LicenseActivator:
    """Model pygslv license discovery without accessing the real environment."""

    __slots__ = ("_scenario",)

    def __init__(self, scenario: str) -> None:
        """Store the requested activation outcome.

        :param scenario: Backend startup condition.
        :return: None.
        """
        self._scenario = scenario

    def __call__(self, verbose: bool) -> None:
        """Complete or fail the simulated activation request.

        :param verbose: Ignored wrapper verbosity setting.
        :return: None.
        """
        if self._scenario == "activation_failure":
            raise RuntimeError("license discovery failed")
        else:
            pass


class _LicenseStateReader:
    """Return the selected fake license state."""

    __slots__ = ("_licensed",)

    def __init__(self, licensed: bool) -> None:
        """Store the requested license state.

        :param licensed: License state reported to the adapter.
        :return: None.
        """
        self._licensed = licensed

    def __call__(self) -> bool:
        """Return the requested fake license state.

        :return: Whether the fake backend is licensed.
        """
        return self._licensed


def _install_fake_pygslv(
        scenario: str, version: str, licensed: bool, missing_api: bool,
) -> bool:
    """Install the selected fake pygslv module before the Engine imports it.

    :param scenario: Requested backend startup condition.
    :param version: Backend version returned by the fake module.
    :param licensed: License state reported by the fake module.
    :param missing_api: Whether the required battery enum is omitted.
    :return: Whether the scenario reaches license evaluation after version checks.
    """
    if scenario == "absent":
        sys.modules.pop("pygslv", None)
        sys.meta_path.insert(0, _MissingPygslvFinder())
        return False
    else:
        pass

    module: ModuleType = ModuleType("pygslv")

    module.get_version = _VersionReader(scenario, version)
    module.search_license_and_activate = _LicenseActivator(scenario)
    module.isLicensed = _LicenseStateReader(licensed)
    module.BuildStatus = _FakeEnums
    module.TapModuleControl = _FakeEnums
    module.TapPhaseControl = _FakeEnums
    module.GeneratorControlMode = _FakeEnums
    if missing_api:
        pass
    else:
        module.BatteryDispatchMode = _FakeEnums
    module.RemedialActionPropertyEnum = _FakeEnums
    module.HvdcControlType = _FakeEnums
    module.BranchGroupTypes = _FakeEnums
    module.ContingencyOperationTypes = _FakeEnums
    module.ContingencyMethod = _FakeEnums
    module.ConverterControlType = _FakeEnums
    module.BusMode = _FakeEnums
    module.ShuntConnectionType = _FakeEnums
    module.WindingType = _FakeEnums
    sys.modules["pygslv"] = module
    return scenario in ("unlicensed", "missing_api", "compatible", "newer")


def main() -> None:
    """Import the Engine after configuring one fake pygslv startup condition.

    :return: None.
    """
    scenario: str = sys.argv[1]
    version: str = sys.argv[2]
    licensed: bool = _parse_bool(sys.argv[3])
    missing_api: bool = _parse_bool(sys.argv[4])
    license_evaluation_reached: bool = _install_fake_pygslv(
        scenario, version, licensed, missing_api,
    )
    importlib.import_module("VeraGridEngine")
    activation: ModuleType = importlib.import_module(
        "VeraGridEngine.Compilers.Gslv.activation",
    )

    status: list[object] = list()
    status.append(activation.GSLV_AVAILABLE)
    status.append(activation.GSLV_VERSION)
    status.append(activation.GSLV_UNAVAILABLE_REASON)
    status.append(license_evaluation_reached)
    print(json.dumps(status))


if __name__ == "__main__":
    main()
