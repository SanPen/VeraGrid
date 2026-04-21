# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Tests for CGMES synchronous-generator conversion into VeraGrid devices."""
from typing import Dict, List, Tuple

import pytest

from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.IO.cim.cgmes import cgmes_enums
from VeraGridEngine.IO.cim.cgmes.cgmes_circuit import CgmesCircuit
from VeraGridEngine.IO.cim.cgmes.cgmes_to_veragrid import get_gcdev_generators
import VeraGridEngine.Devices as gcdev
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.base_voltage import BaseVoltage
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.generating_unit import GeneratingUnit
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.regulating_control import RegulatingControl
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.synchronous_machine import SynchronousMachine
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.terminal import Terminal
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.topological_node import TopologicalNode
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.voltage_level import VoltageLevel
from VeraGridEngine.data_logger import DataLogger
from VeraGridEngine.enumerations import CGMESVersions


def build_generator_case(p: float) -> Tuple[CgmesCircuit, Dict[str, gcdev.Bus], Dict[str, List[Terminal]], float]:
    """
    Build a deterministic CGMES generator import case.

    :param p: Active power in MW.
    :return: CGMES model, bus dictionary, device-to-terminal dictionary, expected PF.
    """
    circuit = CgmesCircuit(cgmes_version=CGMESVersions.v2_4_15)

    generator = SynchronousMachine("sm_rdfid", "SynchronousMachine")
    generator.GeneratingUnit = GeneratingUnit("gu_rdfid", "GeneratingUnit")
    generator.description = "test description"
    generator.name = "test name"
    generator.ratedS = 10.0
    generator.p = p
    generator.q = 3.0
    generator.maxQ = 50.0
    generator.minQ = 60.0
    generator.GeneratingUnit.minOperatingP = 30.0
    generator.GeneratingUnit.maxOperatingP = 40.0

    terminal = Terminal("term_rdfid", "Terminal")
    topological_node = TopologicalNode("tn_rdfid", "TopologicalNode")
    topological_node.BaseVoltage = BaseVoltage("tn_bv_rdfid", "BaseVoltage")
    topological_node.BaseVoltage.nominalVoltage = 3.0
    terminal.TopologicalNode = topological_node

    regulating_control = RegulatingControl("regulating_rdfid", "RegulatingControl")
    regulating_control.mode = cgmes_enums.RegulatingControlModeKind.voltage
    regulating_control.targetValue = 3.0
    regulating_control.enabled = True
    regulating_control.Terminal = terminal
    generator.RegulatingControl = regulating_control
    generator.controlEnabled = True

    generator.EquipmentContainer = VoltageLevel("equipmentcontainer_rdfid", "VoltageLevel")
    generator.EquipmentContainer.BaseVoltage = BaseVoltage("container_bv_rdfid", "BaseVoltage")
    generator.EquipmentContainer.BaseVoltage.nominalVoltage = 2.0

    circuit.cgmes_assets.SynchronousMachine_list = [generator]

    bus = gcdev.Bus(name="test_bus", idtag=topological_node.uuid, Vnom=3.0)
    bus_dict = dict()
    bus_dict[topological_node.uuid] = bus

    device_to_terminal_dict = dict()
    device_to_terminal_dict[generator.uuid] = [terminal]

    if p != 0.0:
        expected_power_factor = 0.55
    else:
        expected_power_factor = 1.0

    return circuit, bus_dict, device_to_terminal_dict, expected_power_factor


@pytest.mark.parametrize("p,expected_power_factor", [(2.0, 0.55), (0.0, 1.0)])
def test_get_gcdev_generators(p: float, expected_power_factor: float) -> None:
    """
    Convert a synchronous machine and verify the generator fields and power-factor fallback logic.
    """
    cgmes_model, calc_node_dict, device_to_terminal_dict, _ = build_generator_case(p=p)

    logger = DataLogger()
    multi_circuit = MultiCircuit()
    get_gcdev_generators(cgmes_model, multi_circuit, calc_node_dict, device_to_terminal_dict, logger)

    assert len(multi_circuit.generators) == 1
    created_generator = multi_circuit.generators[0]
    cgmes_syncronous_machine = cgmes_model.cgmes_assets.SynchronousMachine_list[0]

    assert created_generator.idtag == cgmes_syncronous_machine.uuid
    assert created_generator.code == cgmes_syncronous_machine.description
    assert created_generator.name == cgmes_syncronous_machine.name
    assert created_generator.active
    assert created_generator.Snom == cgmes_syncronous_machine.ratedS
    assert created_generator.P == -cgmes_syncronous_machine.p
    assert created_generator.Pmin == cgmes_syncronous_machine.GeneratingUnit.minOperatingP
    assert created_generator.Pmax == cgmes_syncronous_machine.GeneratingUnit.maxOperatingP
    assert created_generator.Qmax == cgmes_syncronous_machine.maxQ
    assert created_generator.Qmin == cgmes_syncronous_machine.minQ
    assert created_generator.Pf == pytest.approx(expected_power_factor, abs=0.01)

    if p == 0.0:
        assert any(entry.msg == 'GeneratingUnit p is 0.' for entry in logger.entries)
    else:
        assert len(logger.entries) == 0


def test_get_gcdev_generators_zero_terminals_log_error() -> None:
    """
    Log explicit errors when generator conversion cannot find any connected terminal.
    """
    cgmes_model, calc_node_dict, _, _ = build_generator_case(p=2.0)

    logger = DataLogger()
    multi_circuit = MultiCircuit()
    get_gcdev_generators(cgmes_model, multi_circuit, calc_node_dict, dict(), logger)

    assert len(logger.entries) == 2
    assert logger.entries[0].msg == 'No terminal for the device'
    assert logger.entries[1].msg == 'Not exactly one terminal'


def test_get_gcdev_generators_generating_unit_is_none_log_error() -> None:
    """
    Log an error when the synchronous machine lacks its required generating-unit reference.
    """
    cgmes_model, calc_node_dict, device_to_terminal_dict, _ = build_generator_case(p=2.0)
    cgmes_model.cgmes_assets.SynchronousMachine_list[0].GeneratingUnit = None

    logger = DataLogger()
    multi_circuit = MultiCircuit()
    get_gcdev_generators(cgmes_model, multi_circuit, calc_node_dict, device_to_terminal_dict, logger)

    assert len(logger.entries) == 1
    assert logger.entries[0].msg == 'SynchronousMachine has no generating unit'


def test_get_gcdev_generators_regulating_controls_none_log_warning() -> None:
    """
    Log a warning when the generator has no regulating control linked to it.
    """
    cgmes_model, calc_node_dict, device_to_terminal_dict, _ = build_generator_case(p=2.0)
    cgmes_model.cgmes_assets.SynchronousMachine_list[0].RegulatingControl = None

    logger = DataLogger()
    multi_circuit = MultiCircuit()
    get_gcdev_generators(cgmes_model, multi_circuit, calc_node_dict, device_to_terminal_dict, logger)

    assert len(logger.entries) == 1
    assert logger.entries[0].msg == 'RegulatingCondEq has no control'


def test_get_gcdev_generators_regulating_control_mode_kind_not_voltage_log_warning() -> None:
    """
    Log a warning when regulating control exists but does not operate in voltage mode.
    """
    cgmes_model, calc_node_dict, device_to_terminal_dict, _ = build_generator_case(p=2.0)
    cgmes_model.cgmes_assets.SynchronousMachine_list[0].RegulatingControl.mode = "aaa"

    logger = DataLogger()
    multi_circuit = MultiCircuit()
    get_gcdev_generators(cgmes_model, multi_circuit, calc_node_dict, device_to_terminal_dict, logger)

    assert len(logger.entries) == 1
    assert logger.entries[0].msg == 'RegulatingCondEq has control, but not voltage'


def test_get_gcdev_generators_unrealistic_target_value_fallback_to_one_pu() -> None:
    """
    Fallback to 1.0 p.u. when CGMES target voltage produces an unrealistic setpoint.
    """
    cgmes_model, calc_node_dict, device_to_terminal_dict, _ = build_generator_case(p=2.0)

    synchronous_machine = cgmes_model.cgmes_assets.SynchronousMachine_list[0]
    synchronous_machine.RegulatingControl.targetValue = 0.001
    synchronous_machine.RegulatingControl.targetValueUnitMultiplier = cgmes_enums.UnitMultiplier.k

    logger = DataLogger()
    multi_circuit = MultiCircuit()
    get_gcdev_generators(cgmes_model, multi_circuit, calc_node_dict, device_to_terminal_dict, logger)

    assert len(multi_circuit.generators) == 1
    assert multi_circuit.generators[0].Vset == pytest.approx(1.0)
    assert any(entry.msg == 'RegulatingControl targetValue yields unrealistic voltage setpoint; fallback to 1.0 p.u.'
               for entry in logger.entries)
