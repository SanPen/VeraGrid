# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Tests for CGMES transformer conversion into VeraGrid devices."""

from typing import Dict, List
import VeraGridEngine.Devices as gcdev
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.DataStructures import BusData
from VeraGridEngine.IO.cim.cgmes.cgmes_circuit import CgmesCircuit
from VeraGridEngine.IO.cim.cgmes import cgmes_enums
from VeraGridEngine.IO.cim.cgmes.cgmes_to_veragrid import (get_gcdev_ac_transformers,
                                                            get_gcdev_device_to_terminal_dict,
                                                            get_transformer_tap_changers)
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.connectivity_node import ConnectivityNode
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.power_transformer import PowerTransformer
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.power_transformer_end import PowerTransformerEnd
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.ratio_tap_changer import RatioTapChanger
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.tap_changer_control import TapChangerControl
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.terminal import Terminal
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.topological_node import TopologicalNode
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.base_voltage import BaseVoltage
from VeraGridEngine.data_logger import DataLogger
from VeraGridEngine.enumerations import CGMESVersions, TapChangerTypes, TapModuleControl

tn_test = TopologicalNode(rdfid="tn1")
cn_test = ConnectivityNode(rdfid="cn1")


def cgmes_object():
    circuit = CgmesCircuit(cgmes_version=CGMESVersions.v2_4_15)
    circuit.PowerTransformer_list = [PowerTransformer()]
    ptend = PowerTransformerEnd()
    ptend.BaseVoltage = BaseVoltage("a", "b")
    ptend.BaseVoltage.nominalVoltage = 100
    ptend.endNumber = 1

    circuit.PowerTransformer_list[0].references_to_me["PowerTransformerEnd"] = [ptend, ptend]
    return circuit


def calc_node_dict_object() -> Dict[str, gcdev.Bus]:
    d = dict()
    d["tn1"] = gcdev.Bus(Vnom=10)
    d["tn2"] = gcdev.Bus(Vnom=10)
    return d


def cn_dict_object() -> Dict[str, List[ConnectivityNode]]:
    d = dict()
    d["cn1"] = [cn_test]
    return d


def device_to_terminal_dict_object_2_terminals() -> Dict[str, List[Terminal]]:
    d = dict()
    t = Terminal("rdfterminal", "tpeterminal")

    t.TopologicalNode = tn_test
    t.ConnectivityNode = cn_test
    d['a'] = [t, t]
    d['b'] = [t]
    return d


def device_to_terminal_dict_object_3_terminals() -> Dict[str, List[Terminal]]:
    d = dict()
    t = Terminal("rdfterminal", "tpeterminal")

    t.TopologicalNode = tn_test
    t.ConnectivityNode = cn_test
    d['a'] = [t, t, t]
    return d


def test_ac_transformers_one_power_transformer_end_log_error():
    """Log an error when transformer conversion receives a one-ended transformer."""
    logger = DataLogger()
    multi_circuit = MultiCircuit()

    cgmes = CgmesCircuit(cgmes_version=CGMESVersions.v2_4_15)
    cgmes.cgmes_assets.PowerTransformer_list = [PowerTransformer()]
    power_transformer_end = PowerTransformerEnd()
    power_transformer_end.endNumber = 1
    cgmes.cgmes_assets.PowerTransformer_list[0].PowerTransformerEnd = [power_transformer_end]
    get_gcdev_ac_transformers(
        cgmes,
        multi_circuit,
        None,
        get_gcdev_device_to_terminal_dict(cgmes_model=cgmes, logger=logger),
        logger,
        0
    )
    assert len(logger.entries) > 0
    assert any(d.msg == 'Transformers with 1 windings not supported yet' for d in logger)


def test_ac_transformers_zero_calc_node_log_error():
    """Log missing-terminal errors when the transformer cannot be mapped to calculation nodes."""
    logger = DataLogger()
    multi_circuit = MultiCircuit()
    calc_node_dict = dict()
    bus_data = BusData(1)
    bus_data.Vnom = 10
    calc_node_dict["tn1"] = bus_data

    cgmes = CgmesCircuit(cgmes_version=CGMESVersions.v2_4_15)
    cgmes.cgmes_assets.PowerTransformer_list = [PowerTransformer()]
    power_transformer_end1 = PowerTransformerEnd()
    power_transformer_end1.endNumber = 1
    power_transformer_end2 = PowerTransformerEnd()
    power_transformer_end2.endNumber = 2
    cgmes.cgmes_assets.PowerTransformer_list[0].PowerTransformerEnd = [power_transformer_end1,
                                                                       power_transformer_end2]

    get_gcdev_ac_transformers(cgmes, multi_circuit, calc_node_dict,
                              device_to_terminal_dict_object_2_terminals(),
                              logger,
                              10)
    assert len(logger.entries) == 2
    assert logger.entries[0].msg == 'No terminal for the device'
    assert logger.entries[1].msg == 'Not exactly two terminals'


def test_ac_transformers2w():
    """Convert a two-winding transformer and verify the created VeraGrid transformer values."""
    logger = DataLogger()
    multi_circuit = MultiCircuit()

    cgmes = CgmesCircuit(cgmes_version=CGMESVersions.v2_4_15)
    cgmes.cgmes_assets.PowerTransformer_list = [PowerTransformer("a")]
    power_transformer_end = PowerTransformerEnd()
    power_transformer_end.ratedS = 1
    power_transformer_end.ratedU = 2

    power_transformer_end.r = 1
    power_transformer_end.x = 1
    power_transformer_end.g = 1
    power_transformer_end.b = 1
    power_transformer_end.r0 = 1
    power_transformer_end.x0 = 1
    power_transformer_end.g0 = 1
    power_transformer_end.b0 = 1
    power_transformer_end.endNumber = 1
    power_transformer_end.BaseVoltage = BaseVoltage("a", "b")
    power_transformer_end.BaseVoltage.nominalVoltage = 100

    power_transformer_end2 = PowerTransformerEnd()
    power_transformer_end2.ratedS = 1
    power_transformer_end2.ratedU = 2
    power_transformer_end2.r = 1
    power_transformer_end2.x = 1
    power_transformer_end2.g = 1
    power_transformer_end2.b = 1
    power_transformer_end2.r0 = 1
    power_transformer_end2.x0 = 1
    power_transformer_end2.g0 = 1
    power_transformer_end2.b0 = 1
    power_transformer_end2.BaseVoltage = BaseVoltage("a", "b")
    power_transformer_end2.BaseVoltage.nominalVoltage = 100
    power_transformer_end2.endNumber = 2
    cgmes.cgmes_assets.PowerTransformer_list[0].PowerTransformerEnd = [power_transformer_end,
                                                                       power_transformer_end2]
    get_gcdev_ac_transformers(cgmes, multi_circuit, calc_node_dict_object(),
                              device_to_terminal_dict_object_2_terminals(), logger,
                              10)
    generated_transtormer2w = multi_circuit.transformers2w[0]
    assert generated_transtormer2w.B == 80.0
    assert generated_transtormer2w.B0 == 80.0
    assert generated_transtormer2w.Cost == 100.0
    assert generated_transtormer2w.G == 80.0
    assert generated_transtormer2w.G0 == 80.0
    assert generated_transtormer2w.HV == 2
    assert generated_transtormer2w.I0 == 0
    assert generated_transtormer2w.LV == 2
    assert generated_transtormer2w.Pcu == 0
    assert generated_transtormer2w.Pfe == 0
    assert generated_transtormer2w.Pset == 0
    assert generated_transtormer2w.R == 5.0
    assert generated_transtormer2w.R0 == 5.0
    assert generated_transtormer2w.R_corrected == 5.0
    assert generated_transtormer2w.Sn == 1
    assert generated_transtormer2w.Vf == 10
    assert generated_transtormer2w.Vsc == 0.0
    assert generated_transtormer2w.Vt == 10
    assert generated_transtormer2w.X == 5.0
    assert generated_transtormer2w.X0 == 5.0
    assert generated_transtormer2w.alpha == 0.0033
    assert generated_transtormer2w.rate == 9999.0
    assert generated_transtormer2w.tap_module == 1.0
    assert generated_transtormer2w.tap_module_max == 1.2
    assert generated_transtormer2w.tap_module_min == 0.5
    assert generated_transtormer2w.tap_phase == 0
    assert generated_transtormer2w.tap_phase_max == 6.28
    assert generated_transtormer2w.tap_phase_min == -6.28
    assert generated_transtormer2w.temp_base == 20
    assert generated_transtormer2w.temp_oper == 20


def test_ac_transformers3w_only_two_terminals_log_error():
    """Log an error when a three-winding transformer is connected to only two terminals."""
    logger = DataLogger()
    multi_circuit = MultiCircuit()

    cgmes = CgmesCircuit(cgmes_version=CGMESVersions.v2_4_15)
    cgmes.cgmes_assets.PowerTransformer_list = [PowerTransformer("a")]
    power_transformer_end = PowerTransformerEnd()
    power_transformer_end2 = PowerTransformerEnd()
    power_transformer_end3 = PowerTransformerEnd()
    power_transformer_end.ratedS = 1
    power_transformer_end.ratedU = 2

    power_transformer_end.r = 1
    power_transformer_end.x = 1
    power_transformer_end.g = 1
    power_transformer_end.b = 1
    power_transformer_end.r0 = 1
    power_transformer_end.x0 = 1
    power_transformer_end.g0 = 1
    power_transformer_end.b0 = 1
    power_transformer_end.endNumber = 1
    power_transformer_end.BaseVoltage = BaseVoltage("a", "b")
    power_transformer_end.BaseVoltage.nominalVoltage = 100

    power_transformer_end2.ratedS = 1
    power_transformer_end2.ratedU = 2

    power_transformer_end2.r = 1
    power_transformer_end2.x = 1
    power_transformer_end2.g = 1
    power_transformer_end2.b = 1
    power_transformer_end2.r0 = 1
    power_transformer_end2.x0 = 1
    power_transformer_end2.g0 = 1
    power_transformer_end2.b0 = 1
    power_transformer_end2.endNumber = 2
    power_transformer_end2.BaseVoltage = BaseVoltage("a", "b")
    power_transformer_end2.BaseVoltage.nominalVoltage = 100

    power_transformer_end3.ratedS = 1
    power_transformer_end3.ratedU = 2

    power_transformer_end3.r = 1
    power_transformer_end3.x = 1
    power_transformer_end3.g = 1
    power_transformer_end3.b = 1
    power_transformer_end3.r0 = 1
    power_transformer_end3.x0 = 1
    power_transformer_end3.g0 = 1
    power_transformer_end3.b0 = 1
    power_transformer_end3.endNumber = 3
    power_transformer_end3.BaseVoltage = BaseVoltage("a", "b")
    power_transformer_end3.BaseVoltage.nominalVoltage = 100

    cgmes.cgmes_assets.PowerTransformer_list[0].PowerTransformerEnd = [power_transformer_end,
                                                                       power_transformer_end2,
                                                                       power_transformer_end3]
    get_gcdev_ac_transformers(cgmes, multi_circuit, calc_node_dict_object(),
                              device_to_terminal_dict_object_2_terminals(), logger,
                              10)
    assert len(logger.entries) == 1
    assert logger.entries[0].msg == 'Not exactly three terminals'


def test_ac_transformers3w():
    """Convert a three-winding transformer and verify the derived three-winding parameters."""
    logger = DataLogger()
    multi_circuit = MultiCircuit()

    cgmes = CgmesCircuit(cgmes_version=CGMESVersions.v2_4_15)
    power_transformer = PowerTransformer("a")
    power_transformer.name = "pt_name"
    cgmes.cgmes_assets.PowerTransformer_list = [power_transformer]
    power_transformer_end = PowerTransformerEnd()
    power_transformer_end2 = PowerTransformerEnd()
    power_transformer_end3 = PowerTransformerEnd()
    power_transformer_end.ratedS = 1
    power_transformer_end.ratedU = 2

    power_transformer_end.r = 1
    power_transformer_end.x = 1
    power_transformer_end.g = 1
    power_transformer_end.b = 1
    power_transformer_end.r0 = 1
    power_transformer_end.x0 = 1
    power_transformer_end.g0 = 1
    power_transformer_end.b0 = 1
    power_transformer_end.BaseVoltage = BaseVoltage("a", "b")
    power_transformer_end.BaseVoltage.nominalVoltage = 100
    power_transformer_end.endNumber = 1

    power_transformer_end2.ratedS = 1
    power_transformer_end2.ratedU = 2

    power_transformer_end2.r = 1
    power_transformer_end2.x = 1
    power_transformer_end2.g = 1
    power_transformer_end2.b = 1
    power_transformer_end2.r0 = 1
    power_transformer_end2.x0 = 1
    power_transformer_end2.g0 = 1
    power_transformer_end2.b0 = 1
    power_transformer_end2.endNumber = 2
    power_transformer_end2.BaseVoltage = BaseVoltage("a", "b")
    power_transformer_end2.BaseVoltage.nominalVoltage = 100

    power_transformer_end3.ratedS = 1
    power_transformer_end3.ratedU = 2

    power_transformer_end3.r = 1
    power_transformer_end3.x = 1
    power_transformer_end3.g = 1
    power_transformer_end3.b = 1
    power_transformer_end3.r0 = 1
    power_transformer_end3.x0 = 1
    power_transformer_end3.g0 = 1
    power_transformer_end3.b0 = 1
    power_transformer_end3.endNumber = 3
    power_transformer_end3.BaseVoltage = BaseVoltage("a", "b")
    power_transformer_end3.BaseVoltage.nominalVoltage = 100

    cgmes.cgmes_assets.PowerTransformer_list[0].PowerTransformerEnd = [power_transformer_end,
                                                                       power_transformer_end2,
                                                                       power_transformer_end3]
    get_gcdev_ac_transformers(cgmes, multi_circuit, calc_node_dict_object(),
                              device_to_terminal_dict_object_3_terminals(), logger,
                              10)
    generated_transformers3w = multi_circuit.transformers3w[0]
    assert len(logger.entries) == 0
    assert generated_transformers3w.V1 == 2
    assert generated_transformers3w.V2 == 2
    assert generated_transformers3w.V3 == 2
    assert generated_transformers3w.r12 == 7.5
    assert generated_transformers3w.r23 == 7.5
    assert generated_transformers3w.r31 == 7.5
    assert generated_transformers3w.rate1 == 1
    assert generated_transformers3w.rate2 == 1
    assert generated_transformers3w.rate3 == 1
    assert generated_transformers3w.x == 0.0
    assert generated_transformers3w.x12 == 7.5
    assert generated_transformers3w.x23 == 7.5
    assert generated_transformers3w.x31 == 7.5
    assert generated_transformers3w.y == 0.0


def build_transformer_with_ratio_tap_case(control_terminal_node: TopologicalNode) -> tuple[CgmesCircuit,
                                                                                            Dict[str, gcdev.Bus],
                                                                                            Dict[str, List[Terminal]],
                                                                                            PowerTransformer]:
    """
    Build a two-winding transformer case with one ratio tap changer and explicit control terminal.

    :param control_terminal_node: TopologicalNode used by TapChangerControl terminal.
    :return: CGMES model, bus dictionary, device-terminal map and created power transformer.
    """
    circuit: CgmesCircuit = CgmesCircuit(cgmes_version=CGMESVersions.v2_4_15)
    transformer: PowerTransformer = PowerTransformer("a")
    circuit.cgmes_assets.PowerTransformer_list = [transformer]

    winding_one: PowerTransformerEnd = PowerTransformerEnd("w1", "PowerTransformerEnd")
    winding_one.ratedS = 1.0
    winding_one.ratedU = 220.0
    winding_one.r = 1.0
    winding_one.x = 1.0
    winding_one.g = 0.0
    winding_one.b = 0.0
    winding_one.endNumber = 1
    winding_one.BaseVoltage = BaseVoltage("bv1", "BaseVoltage")
    winding_one.BaseVoltage.nominalVoltage = 220.0
    winding_one.PowerTransformer = transformer

    winding_two: PowerTransformerEnd = PowerTransformerEnd("w2", "PowerTransformerEnd")
    winding_two.ratedS = 1.0
    winding_two.ratedU = 110.0
    winding_two.r = 1.0
    winding_two.x = 1.0
    winding_two.g = 0.0
    winding_two.b = 0.0
    winding_two.endNumber = 2
    winding_two.BaseVoltage = BaseVoltage("bv2", "BaseVoltage")
    winding_two.BaseVoltage.nominalVoltage = 110.0
    winding_two.PowerTransformer = transformer
    transformer.PowerTransformerEnd = [winding_one, winding_two]

    tap_changer: RatioTapChanger = RatioTapChanger("rtc1", "RatioTapChanger")
    tap_changer.TransformerEnd = winding_one
    tap_changer.lowStep = -5
    tap_changer.highStep = 5
    tap_changer.neutralStep = 0
    tap_changer.normalStep = 0
    tap_changer.step = 0
    tap_changer.stepVoltageIncrement = 1.0
    tap_changer.controlEnabled = True

    tap_control: TapChangerControl = TapChangerControl("tcc1", "TapChangerControl")
    tap_control.enabled = True
    tap_control.mode = cgmes_enums.RegulatingControlModeKind.voltage
    tap_control_terminal: Terminal = Terminal("tc_term", "Terminal")
    tap_control_terminal.TopologicalNode = control_terminal_node
    tap_control.Terminal = tap_control_terminal
    tap_changer.TapChangerControl = tap_control
    circuit.cgmes_assets.RatioTapChanger_list = [tap_changer]
    circuit.cgmes_assets.PhaseTapChangerSymmetrical_list = list()
    circuit.cgmes_assets.PhaseTapChangerAsymmetrical_list = list()

    transformer_terminal_one: Terminal = Terminal("tr_term_1", "Terminal")
    transformer_terminal_one.TopologicalNode = TopologicalNode("tn1")
    transformer_terminal_one.ConnectivityNode = ConnectivityNode("cn1")
    transformer_terminal_two: Terminal = Terminal("tr_term_2", "Terminal")
    transformer_terminal_two.TopologicalNode = TopologicalNode("tn2")
    transformer_terminal_two.ConnectivityNode = ConnectivityNode("cn2")
    device_to_terminal_dict: Dict[str, List[Terminal]] = dict()
    device_to_terminal_dict[transformer.uuid] = [transformer_terminal_one, transformer_terminal_two]

    bus_dict: Dict[str, gcdev.Bus] = dict()
    bus_dict["tn1"] = gcdev.Bus(Vnom=220.0, idtag="tn1")
    bus_dict["tn2"] = gcdev.Bus(Vnom=110.0, idtag="tn2")
    return circuit, bus_dict, device_to_terminal_dict, transformer


def test_ratio_tap_changer_voltage_control_requires_regulation_bus() -> None:
    """
    Keep ratio tap changer fixed when TapChangerControl terminal cannot be mapped to a bus.
    """
    logger: DataLogger = DataLogger()
    multi_circuit: MultiCircuit = MultiCircuit()
    missing_control_node: TopologicalNode = TopologicalNode("tn_missing")
    cgmes_model, bus_dict, device_to_terminal_dict, _ = build_transformer_with_ratio_tap_case(
        control_terminal_node=missing_control_node
    )

    get_gcdev_ac_transformers(cgmes_model,
                              multi_circuit,
                              bus_dict,
                              device_to_terminal_dict,
                              logger,
                              100.0)
    get_transformer_tap_changers(cgmes_model, multi_circuit, bus_dict, logger)

    assert len(multi_circuit.transformers2w) == 1
    converted_transformer = multi_circuit.transformers2w[0]
    assert converted_transformer.tap_module_control_mode == TapModuleControl.fixed
    assert converted_transformer.regulation_bus is None
    assert converted_transformer.tap_changer.tc_type == TapChangerTypes.NoRegulation
    assert any(entry.msg == 'TapChangerControl voltage mode ignored: regulation terminal not mapped to bus'
               for entry in logger.entries)


def test_ratio_tap_changer_voltage_control_sets_regulation_bus_when_available() -> None:
    """
    Enable ratio-tap voltage control and store regulation bus when control terminal can be mapped.
    """
    logger: DataLogger = DataLogger()
    multi_circuit: MultiCircuit = MultiCircuit()
    mapped_control_node: TopologicalNode = TopologicalNode("tn1")
    cgmes_model, bus_dict, device_to_terminal_dict, _ = build_transformer_with_ratio_tap_case(
        control_terminal_node=mapped_control_node
    )

    get_gcdev_ac_transformers(cgmes_model,
                              multi_circuit,
                              bus_dict,
                              device_to_terminal_dict,
                              logger,
                              100.0)
    get_transformer_tap_changers(cgmes_model, multi_circuit, bus_dict, logger)

    assert len(multi_circuit.transformers2w) == 1
    converted_transformer = multi_circuit.transformers2w[0]
    assert converted_transformer.tap_module_control_mode == TapModuleControl.Vm
    assert converted_transformer.regulation_bus is not None
    assert converted_transformer.regulation_bus.idtag == "tn1"
    assert converted_transformer.tap_changer.tc_type == TapChangerTypes.VoltageRegulation
