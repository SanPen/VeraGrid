# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Regression evidence for native equipment and composite interfaces."""
from pathlib import Path
import math
import pytest
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.IO.dgs.dynamic_models.dynamic_model_import import (
    _apply_composite_child_interface_if_missing, build_dgs_dynamic_model_import_bundle)
from VeraGridEngine.IO.dgs.dynamic_models.dgs_adapter_block_from_native_dgs import build_dgs_elmgenstat_block

DATA = Path(__file__).resolve().parents[2] / 'data/grids/DGS/native_options_pf2024'


def test_output_only_child_exposes_composite_output():
    output = Var('signal')
    root = Block(name='root', children=[Block(name='source', out_vars=[output])])
    _apply_composite_child_interface_if_missing(root)
    assert root.in_vars == []
    assert [v.uid for v in root.out_vars] == [output.uid]


def test_internal_output_does_not_hide_unrelated_public_output():
    internal, external, incoming = Var('internal'), Var('external'), Var('incoming')
    source = Block(name='source', in_vars=[incoming], out_vars=[internal, external])
    sink = Block(name='sink', in_vars=[internal])
    root = Block(name='root', children=[source, sink])
    _apply_composite_child_interface_if_missing(root)
    assert [v.uid for v in root.out_vars] == [external.uid]


@pytest.mark.parametrize('filename', ['bess_base.dgs', 'nine_bus_avr_pss.dgs', 'nine_bus_avr_amplidyne.dgs'])
def test_native_catalogue_assembly_has_no_diagnostics(filename):
    bundle, logger = build_dgs_dynamic_model_import_bundle(str(DATA / filename))
    assert any(entry.is_importable() for entry in bundle.get_entries())
    assert not logger.entries


@pytest.mark.parametrize('system,equipment', [(100., 25.), (50., 200.)])
@pytest.mark.parametrize('angle', [0., .7, -1.2])
def test_genstat_power_base_and_frame_rotation(system, equipment, angle):
    block = build_dgs_elmgenstat_block(system, equipment)
    vm, active_current, reactive_current = .93, .6, -.2
    expected = [vm*active_current*equipment/system, -vm*reactive_current*equipment/system,
                vm*active_current, -vm*reactive_current, vm*math.cos(angle), vm*math.sin(angle),
                active_current*math.cos(angle)-reactive_current*math.sin(angle),
                active_current*math.sin(angle)+reactive_current*math.cos(angle)]
    values = {v.uid: x for v, x in zip(block.in_vars, [vm, angle, active_current, reactive_current])}
    values.update({v.uid: x for v, x in zip(block.out_vars, expected)})
    assert all(abs(eq.eval_uid(values)) < 1e-12 for eq in block.algebraic_eqs)


def test_genstat_angle_lag_matches_analytic_step_derivative():
    tau, angle, time = .02, .6, .03
    block = build_dgs_elmgenstat_block(100., 25., angle_delay_seconds=tau)
    targets = [math.cos(angle), math.sin(angle)]
    initial = [1., 0.]
    states = [target + (start-target)*math.exp(-time/tau) for start, target in zip(initial, targets)]
    values = {block.in_vars[1].uid: angle}
    values.update({v.uid: value for v, value in zip(block.state_vars, states)})
    for equation, start, target in zip(block.state_eqs, initial, targets):
        assert equation.eval_uid(values) == pytest.approx((target-start)*math.exp(-time/tau)/tau)


def _genstat_plan(source):
    from VeraGridEngine.IO.dgs.dgs_to_blocks import ElmCompInstanceEntry
    from VeraGridEngine.IO.dgs.dynamic_models.dgs_native_model_workflow import NativeDgsEquipmentPlan, NativeDgsEquipmentKind
    entry = ElmCompInstanceEntry('slot', 'generator', source.ID, source.loc_name,
                                 'ElmGenstat', 0, None, None)
    return NativeDgsEquipmentPlan(NativeDgsEquipmentKind.StaticGenerator, entry)


def _construct_genstat(delay_flag, delay=.02, mode=1):
    from VeraGridEngine.IO.dgs.dgs_circuit import DgsCircuit
    from VeraGridEngine.IO.dgs.dynamic_models.dgs_native_model_workflow import construct_native_dgs_equipment
    from VeraGridEngine.Devices.Injections.generator import Generator
    source = DgsCircuit()
    source.parse_dgs(str(DATA.parent / 'native_equipment_options_pf2024/genstat_base.dgs'))
    target = source.elmgenstats[0]
    target.iDelay, target.Tdelay, target.iSimModel = delay_flag, delay, mode
    return construct_native_dgs_equipment(_genstat_plan(target), Generator(Snom=25.), source, 100., 50.)


@pytest.mark.parametrize('flag,count', [(None, 0), (0, 0), (1, 2)])
def test_genstat_delay_is_enabled_by_selector_not_time_constant(flag, count):
    assert len(_construct_genstat(flag).state_vars) == count


@pytest.mark.parametrize('delay', [None, 0., -.01, float('inf'), float('nan')])
def test_genstat_enabled_delay_requires_valid_time_constant(delay):
    with pytest.raises(ValueError, match='positive finite Tdelay'):
        _construct_genstat(1, delay)


@pytest.mark.parametrize('mode', [3, 4, 99])
def test_controlled_genstat_does_not_silently_use_wrong_source_equations(mode):
    with pytest.raises(ValueError, match='Unsupported native ElmGenstat RMS model'):
        _construct_genstat(0, mode=mode)


def test_bess_network_import_reports_unsupported_contract_without_crashing():
    from VeraGridEngine.IO.dgs.dgs_to_veragrid import dgs_to_circuit
    from VeraGridEngine.enumerations import DynamicSimulationMode
    from VeraGridEngine.basic_structures import Logger
    logger = Logger()
    grid = dgs_to_circuit(str(DATA / 'bess_base.dgs'), use_dynamic_information=True,
                          dynamic_simulation_mode=DynamicSimulationMode.RMS, logger_=logger)
    assert grid.buses
    assert any('unsupported RMS equipment model' in entry.msg for entry in logger.entries)
    assert not any(device.active for device in grid.vsc_devices)


@pytest.mark.parametrize('filename,flag,delay', [
    ('genstat_delay_base.dgs', 0, .01), ('genstat_delay_on.dgs', 1, .01),
    ('genstat_delay_20ms.dgs', 0, .02)])
def test_native_delay_exports_preserve_enable_flag_and_time(filename, flag, delay):
    from VeraGridEngine.IO.dgs.dgs_circuit import DgsCircuit
    from VeraGridEngine.IO.dgs.dynamic_models.dgs_native_model_workflow import construct_native_dgs_equipment
    from VeraGridEngine.Devices.Injections.generator import Generator
    source = DgsCircuit()
    source.parse_dgs(str(DATA.parent / 'native_equipment_options_pf2024' / filename))
    target = source.elmgenstats[0]
    assert target.iDelay == flag
    assert target.Tdelay == pytest.approx(delay)
    block = construct_native_dgs_equipment(_genstat_plan(target), Generator(Snom=25.), source, 100., 50.)
    assert len(block.state_vars) == 2*flag


@pytest.mark.parametrize('filename', ['nine_bus_avr_pss.dgs', 'nine_bus_avr_amplidyne.dgs'])
def test_native_avr_assigns_machine_and_keeps_bus_voltage_external(filename):
    from VeraGridEngine.IO.dgs.dgs_to_veragrid import dgs_to_circuit
    from VeraGridEngine.enumerations import DynamicSimulationMode, VarPowerFlowReferenceType as Ref
    grid = dgs_to_circuit(str(DATA / filename), use_dynamic_information=True,
                          dynamic_simulation_mode=DynamicSimulationMode.RMS)
    host = next(device for device in grid.generators if device.name == 'G2')
    assert grid.fBase == 60.0
    block = host.rms_template.block
    assert host.rms_template.name == 'Plant_G2'
    assert {Ref.Vm, Ref.Va} <= {v.ref for v in block.in_vars}
    terminal_uid = block.external_mapping[Ref.Vm].uid
    for child in block.get_all_blocks():
        assert terminal_uid not in {v.uid for v in child.algebraic_vars}
    held_power = next(v for v in block.event_dict if v.name == 'pt')
    # Template normalization moves event initialization to its unique owner.
    from VeraGridEngine.Utils.Symbolic.symbolic import get_expression_vars
    assert get_expression_vars(block.event_dict[held_power])
    assert held_power.uid not in {v.uid for v in block.in_vars}


def test_voltage_source_requires_exported_series_reactor_data():
    with pytest.raises(ValueError, match='requires exported uk and Pcu'):
        _construct_genstat(0, mode=2)


def test_missing_active_sum_columns_preserve_native_subtraction():
    from VeraGridEngine.IO.dgs.dgs_objects import BlkSum
    from VeraGridEngine.IO.dgs.dgs_to_blocks import _blk_sum_slot_mode
    block=BlkSum.parse_line('sum;0;1;2;0',{'FID':0,'iInput0':1,'iInput1':2,'iInput2':3,'iInput3':4})
    assert block.iInput1_act is None
    assert [_blk_sum_slot_mode(block,i) for i in range(4)]==[0,1,2,0]
    block.iInput1_act=0
    assert _blk_sum_slot_mode(block,1)==0


def test_native_avr_parent_initialization_owns_executable_child_states():
    from VeraGridEngine.IO.dgs.dgs_to_veragrid import dgs_to_circuit
    from VeraGridEngine.enumerations import DynamicSimulationMode
    grid=dgs_to_circuit(str(DATA/'nine_bus_avr_pss.dgs'),use_dynamic_information=True,
                         dynamic_simulation_mode=DynamicSimulationMode.RMS)
    machine=next(d for d in grid.generators if d.name=='G2').rms_model
    avr=next(b for b in machine.get_all_blocks() if b.name=='avr_IEEET1S')
    initial_uids={v.uid for v in avr.init_eqs}
    child_states=[v for b in avr.get_all_blocks() for v in b.state_vars]
    assert len(child_states)==4
    assert {v.uid for v in child_states}<=initial_uids
