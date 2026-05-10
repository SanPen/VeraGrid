# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from types import SimpleNamespace

import numpy as np

from VeraGridEngine.Devices.Branches.dc_line import DcLine
from VeraGridEngine.Devices.Branches.line import Line
from VeraGridEngine.Devices.Branches.transformer import Transformer2W
from VeraGridEngine.Devices.Branches.vsc import VSC
from VeraGridEngine.Devices.Injections.external_grid import ExternalGrid
from VeraGridEngine.Devices.Injections.generator import Generator
from VeraGridEngine.Devices.Injections.current_injection import CurrentInjection
from VeraGridEngine.Devices.Injections.load import Load
from VeraGridEngine.Devices.Injections.shunt import Shunt
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Utils.Symbolic.static_parameter_mapping import (
    assign_api_mapping_value_if_present,
    assign_static_api_object_mapping_for_device,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Var
from VeraGridEngine.enumerations import (
    ConverterControlType,
    ExternalGridMode,
    ParamPowerFlowRefferenceType,
    WindingType,
)


def _make_grid(sbase: float = 100.0, fbase: float = 50.0) -> SimpleNamespace:
    """Create a small grid-like object for static-mapping tests."""
    return SimpleNamespace(Sbase=sbase, fBase=fbase)


def _make_var(name: str) -> Var:
    """Create one symbolic parameter variable for test blocks."""
    return Var(name=name)


def _make_block(mapping: dict[ParamPowerFlowRefferenceType, Var | None]) -> Block:
    """Create a symbolic block exposing an ``api_obj_mapping``."""
    return Block(api_obj_mapping=dict(mapping))


def _const_value(block: Block, key: ParamPowerFlowRefferenceType) -> float:
    """Return the assigned constant value for one exposed mapping key."""
    target: Var | None = block.api_obj_mapping[key]
    assert target is not None
    value: Const = block.parameters[target]
    assert isinstance(value, Const)
    assert value.value is not None
    return float(value.value)


def test_assign_api_mapping_never_writes_event_dict() -> None:
    """Static api-object mapping must skip ``event_dict`` targets."""
    target: Var = _make_var("static_param")
    block: Block = Block(
        api_obj_mapping=dict({ParamPowerFlowRefferenceType.device_active: target}),
        event_dict=dict({target: Const(9.0)}),
    )

    assigned: bool = assign_api_mapping_value_if_present(
        mdl=block,
        key=ParamPowerFlowRefferenceType.device_active,
        value=1.0,
        logger=None,
        device_name="device",
    )

    assert assigned is False
    assert target not in block.parameters
    assert float(block.event_dict[target].value) == 9.0


def test_missing_keys_are_skipped_silently() -> None:
    """Missing ``api_obj_mapping`` keys must not create parameters."""
    block: Block = _make_block(dict())

    assigned: bool = assign_api_mapping_value_if_present(
        mdl=block,
        key=ParamPowerFlowRefferenceType.device_active,
        value=1.0,
        logger=None,
        device_name="device",
    )

    assert assigned is False
    assert len(block.parameters) == 0


def test_load_subset_mapping_assigns_only_requested_keys() -> None:
    """A model exposing a subset of load keys must receive only that subset."""
    grid: SimpleNamespace = _make_grid()
    bus: Bus = Bus(name="bus", Vnom=20.0)
    load: Load = Load(name="load", P1=30.0, Q1=12.0, active=False)
    load.bus = bus

    block: Block = _make_block(
        dict({
            ParamPowerFlowRefferenceType.device_active: _make_var("active"),
            ParamPowerFlowRefferenceType.load_pa_pu: _make_var("pa"),
        })
    )

    assign_static_api_object_mapping_for_device(grid=grid, device=load, mdl=block, logger=None)

    assert len(block.parameters) == 2
    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.device_active), 0.0)
    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.load_pa_pu), 0.3)


def test_external_grid_enum_mapping_is_explicit() -> None:
    """External-grid modes must map through explicit enum conversion."""
    grid: SimpleNamespace = _make_grid()
    bus: Bus = Bus(name="bus", Vnom=20.0)
    external_grid: ExternalGrid = ExternalGrid(name="eg", Vm=1.03, Va=0.2, mode=ExternalGridMode.VD)
    external_grid.bus = bus

    block: Block = _make_block(
        dict({
            ParamPowerFlowRefferenceType.external_grid_mode_code: _make_var("mode"),
            ParamPowerFlowRefferenceType.external_grid_vm_pu: _make_var("vm"),
        })
    )

    assign_static_api_object_mapping_for_device(grid=grid, device=external_grid, mdl=block, logger=None)

    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.external_grid_mode_code), 3.0)
    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.external_grid_vm_pu), 1.03)


def test_existing_load_mapping_values_remain_unchanged() -> None:
    """Historical AC-load EMT keys must keep their existing values."""
    grid: SimpleNamespace = _make_grid(sbase=100.0, fbase=60.0)
    bus: Bus = Bus(name="bus", Vnom=20.0)
    load: Load = Load(name="load", P1=30.0, P2=20.0, P3=10.0, Q1=15.0, Q2=10.0, Q3=5.0)
    load.bus = bus

    block: Block = _make_block(
        dict({
            ParamPowerFlowRefferenceType.Pl0_A: _make_var("pla"),
            ParamPowerFlowRefferenceType.Pl0_B: _make_var("plb"),
            ParamPowerFlowRefferenceType.Pl0_C: _make_var("plc"),
            ParamPowerFlowRefferenceType.Ql0_A: _make_var("qla"),
            ParamPowerFlowRefferenceType.Ql0_B: _make_var("qlb"),
            ParamPowerFlowRefferenceType.Ql0_C: _make_var("qlc"),
            ParamPowerFlowRefferenceType.omega_base: _make_var("omega"),
        })
    )

    assign_static_api_object_mapping_for_device(grid=grid, device=load, mdl=block, logger=None)

    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.Pl0_A), 0.3)
    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.Pl0_B), 0.2)
    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.Pl0_C), 0.1)
    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.Ql0_A), 0.15)
    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.Ql0_B), 0.1)
    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.Ql0_C), 0.05)
    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.omega_base), 2.0 * np.pi * 60.0)


def test_balanced_load_values_are_distributed_to_phase_keys() -> None:
    """Balanced load totals must feed per-phase static keys when phases are empty."""
    grid: SimpleNamespace = _make_grid(sbase=90.0, fbase=50.0)
    bus: Bus = Bus(name="bus", Vnom=20.0)
    load: Load = Load(name="load", P=27.0, Q=9.0, G=18.0, B=6.0, Ir=12.0, Ii=3.0)
    load.bus = bus

    block: Block = _make_block(
        dict({
            ParamPowerFlowRefferenceType.load_pa_pu: _make_var("pa"),
            ParamPowerFlowRefferenceType.load_qb_pu: _make_var("qb"),
            ParamPowerFlowRefferenceType.load_gc_pu: _make_var("gc"),
            ParamPowerFlowRefferenceType.load_ba_pu: _make_var("ba"),
            ParamPowerFlowRefferenceType.load_irb_pu: _make_var("irb"),
            ParamPowerFlowRefferenceType.load_iic_pu: _make_var("iic"),
            ParamPowerFlowRefferenceType.Pl0_C: _make_var("plc"),
            ParamPowerFlowRefferenceType.Ql0_A: _make_var("qla"),
        })
    )

    assign_static_api_object_mapping_for_device(grid=grid, device=load, mdl=block, logger=None)

    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.load_pa_pu), 0.1)
    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.load_qb_pu), 1.0 / 30.0)
    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.load_gc_pu), 1.0 / 15.0)
    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.load_ba_pu), 1.0 / 45.0)
    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.load_irb_pu), 2.0 / 45.0)
    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.load_iic_pu), 1.0 / 90.0)
    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.Pl0_C), 0.1)
    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.Ql0_A), 1.0 / 30.0)


def test_load_static_api_mapping_does_not_seed_runtime_event_dict_targets() -> None:
    """Load static api-object mapping must not write runtime event targets."""
    grid: SimpleNamespace = _make_grid(sbase=100.0, fbase=60.0)
    bus: Bus = Bus(name="bus", Vnom=20.0)
    load: Load = Load(name="load", P=90.0, Q=30.0)
    load.bus = bus

    p_target: Var = _make_var("pla_evt")
    q_target: Var = _make_var("qla_evt")
    omega_target: Var = _make_var("omega_evt")
    block: Block = Block(
        api_obj_mapping=dict({
            ParamPowerFlowRefferenceType.Pl0_A: p_target,
            ParamPowerFlowRefferenceType.Ql0_A: q_target,
            ParamPowerFlowRefferenceType.omega_base: omega_target,
        }),
        event_dict=dict({
            p_target: Const(0.0),
            q_target: Const(0.0),
            omega_target: Const(0.0),
        }),
    )

    assign_static_api_object_mapping_for_device(grid=grid, device=load, mdl=block, logger=None)

    assert p_target not in block.parameters
    assert q_target not in block.parameters
    assert omega_target not in block.parameters
    assert np.isclose(float(block.event_dict[p_target].value), 0.0)
    assert np.isclose(float(block.event_dict[q_target].value), 0.0)
    assert np.isclose(float(block.event_dict[omega_target].value), 0.0)


def test_existing_generator_mapping_values_remain_unchanged() -> None:
    """Historical generator EMT keys must keep their existing values."""
    grid: SimpleNamespace = _make_grid(fbase=60.0)
    bus: Bus = Bus(name="bus", Vnom=20.0)
    generator: Generator = Generator(name="gen", r1=0.01, x1=0.2, x0=0.08)
    generator.bus = bus

    block: Block = _make_block(
        dict({
            ParamPowerFlowRefferenceType.omega_base: _make_var("omega"),
            ParamPowerFlowRefferenceType.R1: _make_var("r1"),
            ParamPowerFlowRefferenceType.X1: _make_var("x1"),
            ParamPowerFlowRefferenceType.X0: _make_var("x0"),
        })
    )

    assign_static_api_object_mapping_for_device(grid=grid, device=generator, mdl=block, logger=None)

    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.omega_base), 2.0 * np.pi * 60.0)
    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.R1), 0.01)
    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.X1), 0.2)
    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.X0), 0.08)


def test_generator_nominal_frequency_candidates_are_available() -> None:
    """Generator static mapping must expose RMS-relevant frequency-base candidates."""
    grid: SimpleNamespace = _make_grid(fbase=60.0)
    bus: Bus = Bus(name="bus", Vnom=20.0)
    generator: Generator = Generator(name="gen", freq=55.0)
    generator.bus = bus

    block: Block = _make_block(
        dict({
            ParamPowerFlowRefferenceType.fn: _make_var("fn"),
            ParamPowerFlowRefferenceType.ws: _make_var("ws"),
            ParamPowerFlowRefferenceType.freq: _make_var("freq"),
        })
    )

    assign_static_api_object_mapping_for_device(grid=grid, device=generator, mdl=block, logger=None)

    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.fn), 60.0)
    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.ws), 2.0 * np.pi * 60.0)
    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.freq), 55.0)


def test_existing_vsc_static_values_remain_unchanged() -> None:
    """Historical VSC EMT keys must keep their existing values."""
    grid: SimpleNamespace = _make_grid(sbase=150.0, fbase=50.0)
    bus_dc: Bus = Bus(name="dc", Vnom=2.0, is_dc=True)
    bus_ac: Bus = Bus(name="ac", Vnom=20.0, is_dc=False)
    vsc: VSC = VSC(
        name="vsc",
        bus_from=bus_dc,
        bus_to=bus_ac,
        control1=ConverterControlType.Vm_dc,
        control2=ConverterControlType.Pac,
        control1_val=1.05,
        control2_val=20.0,
    )

    block: Block = _make_block(
        dict({
            ParamPowerFlowRefferenceType.Sbase: _make_var("sbase"),
            ParamPowerFlowRefferenceType.omega_base: _make_var("omega"),
            ParamPowerFlowRefferenceType.converter_control_mode_1: _make_var("c1"),
            ParamPowerFlowRefferenceType.converter_control_mode_2: _make_var("c2"),
            ParamPowerFlowRefferenceType.converter_control_target_1: _make_var("t1"),
            ParamPowerFlowRefferenceType.converter_control_target_2: _make_var("t2"),
        })
    )

    assign_static_api_object_mapping_for_device(grid=grid, device=vsc, mdl=block, logger=None)

    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.Sbase), 150.0)
    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.omega_base), 2.0 * np.pi * 50.0)
    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.converter_control_mode_1), 1.0)
    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.converter_control_mode_2), 6.0)
    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.converter_control_target_1), 1.05)
    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.converter_control_target_2), 20.0)


def test_existing_dc_line_mapping_values_remain_unchanged() -> None:
    """Historical DC-line EMT keys must keep their existing values."""
    grid: SimpleNamespace = _make_grid()
    bus_from: Bus = Bus(name="dcf", Vnom=2.0, is_dc=True)
    bus_to: Bus = Bus(name="dct", Vnom=2.0, is_dc=True)
    dc_line: DcLine = DcLine(name="dc", bus_from=bus_from, bus_to=bus_to, r=0.5)

    block: Block = _make_block(
        dict({
            ParamPowerFlowRefferenceType.g: _make_var("g"),
            ParamPowerFlowRefferenceType.b: _make_var("b"),
            ParamPowerFlowRefferenceType.bsh: _make_var("bsh"),
        })
    )

    assign_static_api_object_mapping_for_device(grid=grid, device=dc_line, mdl=block, logger=None)

    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.g), 2.0)
    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.b), 0.0)
    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.bsh), 0.0)


def test_transformer_direct_static_keys_receive_only_direct_values() -> None:
    """A direct-only transformer model must receive only direct static values."""
    grid: SimpleNamespace = _make_grid(fbase=50.0)
    bus_hv: Bus = Bus(name="hv", Vnom=110.0)
    bus_lv: Bus = Bus(name="lv", Vnom=20.0)
    transformer: Transformer2W = Transformer2W(
        name="xfmr",
        bus_from=bus_hv,
        bus_to=bus_lv,
        nominal_power=40.0,
        copper_losses=120.0,
        iron_losses=30.0,
        no_load_current=1.2,
        short_circuit_voltage=8.0,
        tap_module=1.05,
    )
    transformer.conn_f = WindingType.GroundedStar
    transformer.conn_t = WindingType.GroundedStar
    transformer.vector_group_number = 0

    block: Block = _make_block(
        dict({
            ParamPowerFlowRefferenceType.omega_base: _make_var("omega"),
            ParamPowerFlowRefferenceType.transformer_rated_power_mva: _make_var("sn"),
            ParamPowerFlowRefferenceType.transformer_open_circuit_current_pct: _make_var("i0"),
            ParamPowerFlowRefferenceType.transformer_open_circuit_loss_kw: _make_var("pfe"),
            ParamPowerFlowRefferenceType.transformer_short_circuit_voltage_pct: _make_var("vsc"),
            ParamPowerFlowRefferenceType.transformer_short_circuit_loss_kw: _make_var("pcu"),
            ParamPowerFlowRefferenceType.transformer_tap_module: _make_var("tap_module"),
            ParamPowerFlowRefferenceType.transformer_nominal_voltage_ratio: _make_var("nominal_ratio"),
            ParamPowerFlowRefferenceType.transformer_total_voltage_ratio: _make_var("total_ratio"),
            ParamPowerFlowRefferenceType.transformer_from_connection_aa: _make_var("faa"),
            ParamPowerFlowRefferenceType.transformer_to_connection_cc: _make_var("tcc"),
        })
    )

    assign_static_api_object_mapping_for_device(grid=grid, device=transformer, mdl=block, logger=None)

    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.omega_base), 2.0 * np.pi * 50.0)
    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.transformer_rated_power_mva), 40.0)
    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.transformer_open_circuit_current_pct), 1.2)
    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.transformer_open_circuit_loss_kw), 30.0)
    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.transformer_short_circuit_voltage_pct), 8.0)
    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.transformer_short_circuit_loss_kw), 120.0)
    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.transformer_tap_module), 1.05)
    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.transformer_nominal_voltage_ratio), 110.0 / 20.0)
    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.transformer_total_voltage_ratio), (110.0 / 20.0) * 1.05)
    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.transformer_from_connection_aa), 1.0)
    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.transformer_to_connection_cc), 1.0)
    assert len(block.parameters) == 11


def test_transformer_equivalent_circuit_keys_receive_only_derived_values() -> None:
    """A derived-only transformer model must receive only derived equivalent-circuit values."""
    grid: SimpleNamespace = _make_grid(fbase=50.0)
    bus_hv: Bus = Bus(name="hv", Vnom=110.0)
    bus_lv: Bus = Bus(name="lv", Vnom=20.0)
    transformer: Transformer2W = Transformer2W(
        name="xfmr_classical",
        bus_from=bus_hv,
        bus_to=bus_lv,
        HV=110.0,
        LV=20.0,
        r=0.02,
        x=0.08,
        g=0.001,
        b=0.0,
        tap_module=1.1,
        tap_phase=0.0,
    )

    block: Block = _make_block(
        dict({
            ParamPowerFlowRefferenceType.transformer_winding1_resistance_pu: _make_var("r1"),
            ParamPowerFlowRefferenceType.transformer_winding2_resistance_pu: _make_var("r2"),
            ParamPowerFlowRefferenceType.transformer_winding1_inductance_pu_s: _make_var("l1"),
            ParamPowerFlowRefferenceType.transformer_winding2_inductance_pu_s: _make_var("l2"),
            ParamPowerFlowRefferenceType.transformer_mutual_inductance_pu_s: _make_var("m"),
            ParamPowerFlowRefferenceType.transformer_magnetizing_conductance_pu: _make_var("g"),
        })
    )

    assign_static_api_object_mapping_for_device(grid=grid, device=transformer, mdl=block, logger=None)

    omega: float = 2.0 * np.pi * 50.0
    total_ratio: float = (110.0 / 20.0) * 1.1
    total_ratio_square: float = total_ratio * total_ratio
    magnetizing_l_primary: float = 1000.0 / omega
    magnetizing_l_secondary: float = magnetizing_l_primary / total_ratio_square
    mutual_inductance: float = magnetizing_l_primary / total_ratio
    leakage_l_primary: float = 0.5 * 0.08 / omega
    leakage_l_secondary: float = leakage_l_primary / total_ratio_square

    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.transformer_winding1_resistance_pu), 0.01)
    assert np.isclose(
        _const_value(block, ParamPowerFlowRefferenceType.transformer_winding2_resistance_pu),
        0.01 / total_ratio_square,
    )
    assert np.isclose(
        _const_value(block, ParamPowerFlowRefferenceType.transformer_winding1_inductance_pu_s),
        leakage_l_primary + magnetizing_l_primary,
    )
    assert np.isclose(
        _const_value(block, ParamPowerFlowRefferenceType.transformer_winding2_inductance_pu_s),
        leakage_l_secondary + magnetizing_l_secondary,
    )
    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.transformer_mutual_inductance_pu_s), mutual_inductance)
    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.transformer_magnetizing_conductance_pu), 0.001)
    assert len(block.parameters) == 6


def test_transformer_direct_and_derived_keys_receive_both_sets() -> None:
    """A transformer model exposing direct and derived keys must receive both sets."""
    grid: SimpleNamespace = _make_grid(fbase=50.0)
    bus_hv: Bus = Bus(name="hv", Vnom=110.0)
    bus_lv: Bus = Bus(name="lv", Vnom=20.0)
    transformer: Transformer2W = Transformer2W(
        name="xfmr_both",
        bus_from=bus_hv,
        bus_to=bus_lv,
        HV=110.0,
        LV=20.0,
        nominal_power=40.0,
        copper_losses=120.0,
        iron_losses=30.0,
        no_load_current=1.2,
        short_circuit_voltage=8.0,
        r=0.02,
        x=0.08,
        g=0.001,
        b=0.0,
        tap_module=1.1,
        tap_phase=0.0,
    )

    block: Block = _make_block(
        dict({
            ParamPowerFlowRefferenceType.transformer_tap_module: _make_var("tap_module"),
            ParamPowerFlowRefferenceType.transformer_total_voltage_ratio: _make_var("total_ratio"),
            ParamPowerFlowRefferenceType.transformer_winding1_resistance_pu: _make_var("r1"),
            ParamPowerFlowRefferenceType.transformer_mutual_inductance_pu_s: _make_var("m"),
        })
    )

    assign_static_api_object_mapping_for_device(grid=grid, device=transformer, mdl=block, logger=None)

    omega: float = 2.0 * np.pi * 50.0
    total_ratio: float = (110.0 / 20.0) * 1.1
    magnetizing_l_primary: float = 1000.0 / omega
    mutual_inductance: float = magnetizing_l_primary / total_ratio

    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.transformer_tap_module), 1.1)
    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.transformer_total_voltage_ratio), total_ratio)
    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.transformer_winding1_resistance_pu), 0.01)
    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.transformer_mutual_inductance_pu_s), mutual_inductance)
    assert len(block.parameters) == 4


def test_transformer_missing_keys_are_skipped() -> None:
    """Transformer mapping must skip missing direct and derived keys."""
    grid: SimpleNamespace = _make_grid(fbase=50.0)
    bus_hv: Bus = Bus(name="hv", Vnom=110.0)
    bus_lv: Bus = Bus(name="lv", Vnom=20.0)
    transformer: Transformer2W = Transformer2W(name="xfmr_skip", bus_from=bus_hv, bus_to=bus_lv)

    block: Block = _make_block(dict())

    assign_static_api_object_mapping_for_device(grid=grid, device=transformer, mdl=block, logger=None)

    assert len(block.parameters) == 0


def test_transformer_ratio_key_semantics_are_not_ambiguous() -> None:
    """Transformer ratio keys must keep one stable meaning each."""
    grid: SimpleNamespace = _make_grid(fbase=50.0)
    bus_hv: Bus = Bus(name="hv", Vnom=110.0)
    bus_lv: Bus = Bus(name="lv", Vnom=20.0)
    transformer: Transformer2W = Transformer2W(name="xfmr_ratio", bus_from=bus_hv, bus_to=bus_lv, HV=110.0, LV=20.0, tap_module=1.1)

    block: Block = _make_block(
        dict({
            ParamPowerFlowRefferenceType.transformer_tap_ratio: _make_var("tap_ratio_legacy"),
            ParamPowerFlowRefferenceType.transformer_tap_module: _make_var("tap_module"),
            ParamPowerFlowRefferenceType.transformer_nominal_voltage_ratio: _make_var("nominal_ratio"),
            ParamPowerFlowRefferenceType.transformer_total_voltage_ratio: _make_var("total_ratio"),
        })
    )

    assign_static_api_object_mapping_for_device(grid=grid, device=transformer, mdl=block, logger=None)

    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.transformer_tap_ratio), 1.1)
    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.transformer_tap_module), 1.1)
    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.transformer_nominal_voltage_ratio), 5.5)
    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.transformer_total_voltage_ratio), 6.05)


def test_existing_line_mapping_values_remain_unchanged() -> None:
    """Historical line EMT matrix values must keep their existing values."""
    grid: SimpleNamespace = _make_grid(fbase=50.0)
    bus_from: Bus = Bus(name="from", Vnom=20.0)
    bus_to: Bus = Bus(name="to", Vnom=20.0)
    line: Line = Line(name="line", bus_from=bus_from, bus_to=bus_to, r=0.1, x=0.2, b=0.3)
    line.ys.phA = 1
    line.ys.phB = 1
    line.ys.phC = 1

    block: Block = _make_block(
        dict({
            ParamPowerFlowRefferenceType.Rnn: _make_var("rnn"),
            ParamPowerFlowRefferenceType.Raa: _make_var("raa"),
            ParamPowerFlowRefferenceType.Rbb: _make_var("rbb"),
            ParamPowerFlowRefferenceType.Rcc: _make_var("rcc"),
            ParamPowerFlowRefferenceType.Linv_aa: _make_var("laa"),
            ParamPowerFlowRefferenceType.Caa: _make_var("caa"),
        })
    )

    assign_static_api_object_mapping_for_device(grid=grid, device=line, mdl=block, logger=None)

    omega: float = 2.0 * np.pi * 50.0
    expected_linv: float = omega / 0.3
    expected_c: float = 0.2 / (2.0 * omega)

    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.Rnn), 0.0)
    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.Raa), 0.1)
    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.Rbb), 0.1)
    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.Rcc), 0.1)
    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.Linv_aa), expected_linv)
    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.Caa), expected_c)


def test_uncoupled_line_mapping_uses_direct_reactance_when_historical_slot_is_zero() -> None:
    """Pure-reactive uncoupled lines must keep a non-zero EMT series inductance."""
    grid: SimpleNamespace = _make_grid(fbase=50.0)
    bus_from: Bus = Bus(name="from", Vnom=20.0)
    bus_to: Bus = Bus(name="to", Vnom=20.0)
    line: Line = Line(name="line_rx_only", bus_from=bus_from, bus_to=bus_to, r=0.0, x=0.2, b=0.0)
    line.ys.phA = 1
    line.ys.phB = 1
    line.ys.phC = 1

    block: Block = _make_block(
        dict({
            ParamPowerFlowRefferenceType.Linv_aa: _make_var("laa"),
            ParamPowerFlowRefferenceType.Caa: _make_var("caa"),
        })
    )

    assign_static_api_object_mapping_for_device(grid=grid, device=line, mdl=block, logger=None)

    omega: float = 2.0 * np.pi * 50.0

    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.Linv_aa), omega / 0.2)
    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.Caa), 0.0)


def test_shunt_phase_keys_fall_back_to_balanced_totals() -> None:
    """Balanced shunt totals must feed per-phase shunt keys when phases are empty."""
    grid: SimpleNamespace = _make_grid(sbase=120.0)
    bus: Bus = Bus(name="bus", Vnom=20.0)
    shunt: Shunt = Shunt(name="shunt", G=12.0, B=6.0)
    shunt.bus = bus

    block: Block = _make_block(
        dict({
            ParamPowerFlowRefferenceType.shunt_ga_pu: _make_var("ga"),
            ParamPowerFlowRefferenceType.shunt_bb_pu: _make_var("bb"),
        })
    )

    assign_static_api_object_mapping_for_device(grid=grid, device=shunt, mdl=block, logger=None)

    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.shunt_ga_pu), 1.0 / 30.0)
    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.shunt_bb_pu), 1.0 / 60.0)


def test_current_injection_phase_keys_fall_back_to_balanced_totals() -> None:
    """Balanced current-injection totals must feed per-phase keys when phases are empty."""
    grid: SimpleNamespace = _make_grid(sbase=150.0)
    bus: Bus = Bus(name="bus", Vnom=20.0)
    current_injection: CurrentInjection = CurrentInjection(name="inj", Ir=9.0, Ii=6.0)
    current_injection.bus = bus

    block: Block = _make_block(
        dict({
            ParamPowerFlowRefferenceType.current_injection_ira_pu: _make_var("ira"),
            ParamPowerFlowRefferenceType.current_injection_iic_pu: _make_var("iic"),
        })
    )

    assign_static_api_object_mapping_for_device(grid=grid, device=current_injection, mdl=block, logger=None)

    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.current_injection_ira_pu), 0.02)
    assert np.isclose(_const_value(block, ParamPowerFlowRefferenceType.current_injection_iic_pu), 1.0 / 75.0)
