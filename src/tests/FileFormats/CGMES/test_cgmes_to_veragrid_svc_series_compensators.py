# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Tests for CGMES StaticVarCompensator and SeriesCompensator conversion."""

from typing import Dict, List

import pytest

import VeraGridEngine.Devices as gcdev
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.IO.cim.cgmes.cgmes_circuit import CgmesCircuit
from VeraGridEngine.IO.cim.cgmes.cgmes_to_veragrid import (get_gcdev_series_compensators,
                                                            get_gcdev_static_var_compensators)
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.base_voltage import BaseVoltage
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.series_compensator import SeriesCompensator
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.static_var_compensator import StaticVarCompensator
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.terminal import Terminal
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.topological_node import TopologicalNode
from VeraGridEngine.data_logger import DataLogger
from VeraGridEngine.enumerations import CGMESVersions, ShuntControlMode


def test_static_var_compensator_converts_to_controllable_shunt() -> None:
    """
    Convert a StaticVarCompensator to a ControllableShunt preserving Q and V-setpoint intent.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit(cgmes_version=CGMESVersions.v2_4_15)
    svc: StaticVarCompensator = StaticVarCompensator("svc_rdfid", "StaticVarCompensator")
    svc.name = "svc_name"
    svc.description = "svc_description"
    svc.q = -50.0
    svc.voltageSetPoint = 220.0
    cgmes_model.cgmes_assets.StaticVarCompensator_list = [svc]

    topological_node: TopologicalNode = TopologicalNode("tn_rdfid", "TopologicalNode")
    terminal: Terminal = Terminal("term_rdfid", "Terminal")
    terminal.TopologicalNode = topological_node

    bus_dict: Dict[str, gcdev.Bus] = dict()
    bus_dict[topological_node.uuid] = gcdev.Bus(name="bus", idtag=topological_node.uuid, Vnom=220.0)
    device_to_terminal_dict: Dict[str, List[Terminal]] = dict()
    device_to_terminal_dict[svc.uuid] = [terminal]

    logger: DataLogger = DataLogger()
    multi_circuit: MultiCircuit = MultiCircuit()

    get_gcdev_static_var_compensators(cgmes_model=cgmes_model,
                                      gcdev_model=multi_circuit,
                                      bus_dict=bus_dict,
                                      device_to_terminal_dict=device_to_terminal_dict,
                                      logger=logger)

    assert len(multi_circuit.controllable_shunts) == 1
    converted = multi_circuit.controllable_shunts[0]
    assert converted.idtag == svc.uuid
    assert converted.name == svc.name
    assert converted.B == pytest.approx(-50.0)
    assert converted.Vset == pytest.approx(1.0)
    assert converted.control_mode == ShuntControlMode.Locked


def test_series_compensator_converts_to_series_reactance() -> None:
    """
    Convert a SeriesCompensator to SeriesReactance with p.u. impedance conversion.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit(cgmes_version=CGMESVersions.v2_4_15)
    series_compensator: SeriesCompensator = SeriesCompensator("sc_rdfid", "SeriesCompensator")
    series_compensator.name = "series_name"
    series_compensator.description = "series_description"
    series_compensator.r = 2.0
    series_compensator.x = 10.0
    series_compensator.r0 = 1.0
    series_compensator.x0 = 5.0
    series_compensator.BaseVoltage = BaseVoltage("bv_rdfid", "BaseVoltage")
    series_compensator.BaseVoltage.nominalVoltage = 220.0
    cgmes_model.cgmes_assets.SeriesCompensator_list = [series_compensator]

    terminal_f: Terminal = Terminal("termf_rdfid", "Terminal")
    topological_node_f: TopologicalNode = TopologicalNode("tnf_rdfid", "TopologicalNode")
    terminal_f.TopologicalNode = topological_node_f

    terminal_t: Terminal = Terminal("termt_rdfid", "Terminal")
    topological_node_t: TopologicalNode = TopologicalNode("tnt_rdfid", "TopologicalNode")
    terminal_t.TopologicalNode = topological_node_t

    bus_dict: Dict[str, gcdev.Bus] = dict()
    bus_dict[topological_node_f.uuid] = gcdev.Bus(name="bus_f", idtag=topological_node_f.uuid, Vnom=220.0)
    bus_dict[topological_node_t.uuid] = gcdev.Bus(name="bus_t", idtag=topological_node_t.uuid, Vnom=220.0)
    device_to_terminal_dict: Dict[str, List[Terminal]] = dict()
    device_to_terminal_dict[series_compensator.uuid] = [terminal_f, terminal_t]

    logger: DataLogger = DataLogger()
    multi_circuit: MultiCircuit = MultiCircuit()

    get_gcdev_series_compensators(cgmes_model=cgmes_model,
                                  gcdev_model=multi_circuit,
                                  bus_dict=bus_dict,
                                  device_to_terminal_dict=device_to_terminal_dict,
                                  logger=logger,
                                  Sbase=100.0)

    assert len(multi_circuit.series_reactances) == 1
    converted = multi_circuit.series_reactances[0]
    z_base = (220.0 * 220.0) / 100.0
    assert converted.idtag == series_compensator.uuid
    assert converted.R == pytest.approx(series_compensator.r / z_base)
    assert converted.X == pytest.approx(series_compensator.x / z_base)
    assert converted.R0 == pytest.approx(series_compensator.r0 / z_base)
    assert converted.X0 == pytest.approx(series_compensator.x0 / z_base)
