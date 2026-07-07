# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Tests for CGMES external-grid conversion into VeraGrid devices."""

from typing import Dict, List

import pytest

import VeraGridEngine.Devices as gcdev
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.IO.cim.cgmes import cgmes_enums
from VeraGridEngine.IO.cim.cgmes.cgmes_circuit import CgmesCircuit
from VeraGridEngine.IO.cim.cgmes.cgmes_to_veragrid import get_gcdev_external_grids
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.equivalent_injection import EquivalentInjection
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.external_network_injection import ExternalNetworkInjection
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.regulating_control import RegulatingControl
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.terminal import Terminal
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.topological_node import TopologicalNode
from VeraGridEngine.data_logger import DataLogger
from VeraGridEngine.enumerations import CGMESVersions, ExternalGridMode


def build_external_grid_context() -> tuple[CgmesCircuit, Dict[str, gcdev.Bus], Dict[str, List[Terminal]], Terminal]:
    """
    Build a minimal deterministic context for external-grid conversion.

    :return: CGMES model, bus dictionary, device-to-terminal mapping and shared terminal.
    """
    circuit: CgmesCircuit = CgmesCircuit(cgmes_version=CGMESVersions.v2_4_15)

    topological_node: TopologicalNode = TopologicalNode("tn_rdfid", "TopologicalNode")
    terminal: Terminal = Terminal("term_rdfid", "Terminal")
    terminal.TopologicalNode = topological_node

    bus: gcdev.Bus = gcdev.Bus(name="test_bus", idtag=topological_node.uuid, Vnom=400.0)
    bus_dict: Dict[str, gcdev.Bus] = dict()
    bus_dict[topological_node.uuid] = bus

    return circuit, bus_dict, dict(), terminal


def test_external_grid_equivalent_injection_sanitizes_vm_target() -> None:
    """
    Sanitize out-of-range EquivalentInjection regulation target and keep voltage mode.
    """
    cgmes_model, calc_node_dict, device_to_terminal_dict, terminal = build_external_grid_context()
    equivalent_injection: EquivalentInjection = EquivalentInjection("eqi_rdfid", "EquivalentInjection")
    equivalent_injection.regulationCapability = True
    equivalent_injection.regulationTarget = 0.1
    equivalent_injection.p = 1.0
    equivalent_injection.q = 0.0

    cgmes_model.cgmes_assets.EquivalentInjection_list = [equivalent_injection]
    device_to_terminal_dict[equivalent_injection.uuid] = [terminal]

    logger: DataLogger = DataLogger()
    multi_circuit: MultiCircuit = MultiCircuit()

    get_gcdev_external_grids(cgmes_model, multi_circuit, calc_node_dict, device_to_terminal_dict, logger)

    assert len(multi_circuit.external_grids) == 1
    created_external_grid = multi_circuit.external_grids[0]
    assert created_external_grid.mode == ExternalGridMode.VD
    assert created_external_grid.Vm == pytest.approx(1.0)
    assert any(entry.msg == 'RegulatingControl targetValue yields unrealistic voltage setpoint; fallback to 1.0 p.u.'
               for entry in logger.entries)


def test_external_grid_missing_regulating_target_keeps_pq_mode() -> None:
    """
    Keep PQ mode when ExternalNetworkInjection control is enabled but target is missing.
    """
    cgmes_model, calc_node_dict, device_to_terminal_dict, terminal = build_external_grid_context()
    external_network_injection: ExternalNetworkInjection = ExternalNetworkInjection("eni_rdfid", "ExternalNetworkInjection")
    external_network_injection.controlEnabled = True
    external_network_injection.p = 1.0
    external_network_injection.q = 0.0

    regulating_control: RegulatingControl = RegulatingControl("reg_rdfid", "RegulatingControl")
    regulating_control.mode = cgmes_enums.RegulatingControlModeKind.voltage
    regulating_control.enabled = True
    regulating_control.Terminal = terminal
    regulating_control.targetValue = None
    external_network_injection.RegulatingControl = regulating_control

    cgmes_model.cgmes_assets.EquivalentInjection_list = list()
    cgmes_model.cgmes_assets.ExternalNetworkInjection_list = [external_network_injection]
    device_to_terminal_dict[external_network_injection.uuid] = [terminal]

    logger: DataLogger = DataLogger()
    multi_circuit: MultiCircuit = MultiCircuit()

    get_gcdev_external_grids(cgmes_model, multi_circuit, calc_node_dict, device_to_terminal_dict, logger)

    assert len(multi_circuit.external_grids) == 1
    created_external_grid = multi_circuit.external_grids[0]
    assert created_external_grid.mode == ExternalGridMode.PQ
    assert created_external_grid.Vm == pytest.approx(1.0)
    assert any(entry.msg == 'ExternalNetworkInjection voltage regulation ignored due to missing target or nominal voltage'
               for entry in logger.entries)
