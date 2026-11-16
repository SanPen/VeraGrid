# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Native single-option exports reveal equipment-mode coverage and import gaps."""

from pathlib import Path
import csv
import hashlib
import json

import pytest

from VeraGridEngine.Devices.Injections.static_generator import StaticGenerator
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.IO.dgs.dgs_circuit import DgsCircuit
from VeraGridEngine.IO.dgs.dgs_objects import BlkDef, ElmGenstat
from VeraGridEngine.IO.dgs.dgs_rms_preparation import (
    _build_dgs_elmgenstat_rms_template,
    build_dgs_elmgenstat_fallback,
    resolve_dgs_elmgenstat_source,
)
from VeraGridEngine.IO.dgs.dgs_to_blocks import parse_dgs_block_definitions_from_circuit
from VeraGridEngine.IO.dgs.dgs_to_veragrid import dgs_to_circuit
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.enumerations import DeviceType, VarPowerFlowReferenceType, DynamicSimulationMode
from tests.FileFormats.PowerFactory.dgs_export_rows import read_rows_by_path


ROOT = Path(__file__).resolve().parents[4]
DATA = ROOT / 'src/tests/data/grids/DGS/native_equipment_options_pf2024'
MANIFEST = json.loads((DATA / 'manifest.json').read_text())


@pytest.mark.parametrize('record', MANIFEST['files'], ids=lambda record: record['file'])
def test_native_equipment_export_integrity_and_pointer_closure(record):
    path = DATA / record['file']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == record['sha256']
    assert record['code'] == 0 and not record['errors'] and not record['warnings']
    ids, pointers = set(), []
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        if line.startswith('$$'):
            columns = next(csv.reader([line[2:]], delimiter=';'))[1:]
            names = [col.rsplit('(', 1)[0] for col in columns]
            assert len(names) == len(set(names))
            pointer_indices = [i for i, col in enumerate(columns) if col.endswith('(p)')]
        elif line.startswith('  '):
            values = next(csv.reader([line.strip()], delimiter=';'))
            assert len(values) == len(columns)
            assert values[0] not in ids
            ids.add(values[0])
            pointers.extend(values[i] for i in pointer_indices if values[i] not in ('', '*', '0'))
    assert set(pointers) <= ids


@pytest.mark.parametrize('record', [r for r in MANIFEST['files'] if r['change']],
                         ids=lambda record: record['file'])
def test_native_equipment_pair_changes_one_intended_field(record):
    before = read_rows_by_path(DATA / record['baseline'])
    after = read_rows_by_path(DATA / record['file'])
    assert before.keys() == after.keys()
    changes = [(key, field, value, after[key].get(field))
               for key, row in before.items() for field, value in row.items()
               if after[key].get(field) != value]
    assert len(changes) == 1
    key, field, old, new = changes[0]
    assert key[0] == record['class']
    assert field == record['change']['attribute']
    assert float(old) == pytest.approx(record['change']['before'])
    assert float(new) == pytest.approx(record['change']['after'])


@pytest.mark.parametrize('record', [r for r in MANIFEST['files'] if r['class'] == 'ElmVsc' and r['change']],
                         ids=lambda record: record['file'])
def test_native_vsc_selector_is_preserved(record):
    source = DgsCircuit()
    source.parse_dgs(str(DATA / record['file']))
    target = next(obj for obj in source.elmvscs if obj.loc_name == record['target'])
    values = {'vsctype': target.vsctype, 'i_ctrl': target.i_ctrl, 'i_mod': target.i_mod,
              'iVIsource': target.iVIsource, 'iZarmDCside': target.iZarmDCside,
              'iVacMax': target.iVacMax}
    assert values[record['change']['attribute']] == record['change']['after']


@pytest.mark.parametrize('filename,mode', [('genstat_base.dgs', 1), ('genstat_model_0.dgs', 0),
                                         ('genstat_model_2.dgs', 2), ('genstat_model_3.dgs', 3),
                                         ('genstat_model_4.dgs', 4)])
def test_native_genstat_model_selector_is_preserved(filename, mode):
    source = DgsCircuit()
    source.parse_dgs(str(DATA / filename))
    assert source.elmgenstats[0].iSimModel == mode


@pytest.mark.parametrize('filename', ['vsc_base.dgs', 'vsc_two_level_base.dgs', 'genstat_base.dgs'])
def test_native_equipment_network_rms_import_completes(filename):
    logger = Logger()
    grid = dgs_to_circuit(str(DATA / filename), use_dynamic_information=True,
                          dynamic_simulation_mode=DynamicSimulationMode.RMS, logger_=logger)
    assert grid.buses and grid.rms_models
    if filename.startswith('vsc_'):
        # Native offshore-wind data contains transformer windings. RMS binding
        # must use their two endpoints, never the single-bus injection path.
        assert grid.vsc_devices and grid.windings
        assert all(not winding.rms_model.empty() for winding in grid.windings)


@pytest.mark.parametrize('model,exponent', [(1, 1), (3, 2), (4, 0)])
def test_genstat_source_law_voltage_response(model, exponent):

    block = _build_dgs_elmgenstat_rms_template(
        MultiCircuit(), DeviceType.StaticGeneratorDevice, model).block
    p = block.external_mapping[VarPowerFlowReferenceType.P]
    q = block.external_mapping[VarPowerFlowReferenceType.Q]
    voltage = block.external_mapping[VarPowerFlowReferenceType.Vm]
    for vm in (.8, 1., 1.2):
        values = {voltage.uid: vm, p.uid: .4 * vm ** exponent, q.uid: .1 * vm ** exponent}
        for variable, initial in block.event_dict.items():
            values[variable.uid] = .4 if initial is p else .1 if initial is q else 1.
        assert all(abs(eq.eval_uid(values)) < 1e-12 for eq in block.algebraic_eqs)


@pytest.mark.parametrize('filename,label', [
    ('genstat_base.dgs', 'constant current'), ('genstat_model_3.dgs', 'constant impedance'),
    ('genstat_model_4.dgs', 'constant power')])
def test_parallel_native_genstat_units_keep_selected_source_law(filename, label):
    grid = dgs_to_circuit(str(DATA / filename), use_dynamic_information=True,
                          dynamic_simulation_mode=DynamicSimulationMode.RMS)
    assert len(grid.static_generators) == 37
    assert all(device.rms_template is not None and label in device.rms_template.name
               for device in grid.static_generators)


@pytest.mark.parametrize('filename', ['genstat_model_0.dgs', 'genstat_model_2.dgs',
                                    'genstat_reference_machine.dgs'])
def test_unsupported_genstat_selection_has_no_wrong_fallback(filename):
    logger = Logger()
    grid = dgs_to_circuit(str(DATA / filename), use_dynamic_information=True,
                          dynamic_simulation_mode=DynamicSimulationMode.RMS, logger_=logger)
    assert len(grid.static_generators) == 37
    assert all(not device.active and device.rms_template is None for device in grid.static_generators)
    assert sum(entry.msg == 'DGS ElmGenstat RMS model unsupported; device kept inactive'
               for entry in logger.entries) == 37


@pytest.mark.parametrize('state,input_value,output,derivative', [
    (.2, .3, .5, .6), (2., .5, 1., 0.), (2., -.5, 1., 0.),
    (-2., .5, -1., 0.), (.5, .5, 1., 1.), (-.5, -.5, -1., -1.),
])
def test_powerfactory_pi_output_and_integrator_freeze(state, input_value, output, derivative):
    definition = BlkDef()
    definition.ID = 'PI'
    definition.loc_name = 'PI'
    definition.inputs = ['u']
    definition.outputs = ['y']
    definition.states = ['x']
    definition.params = ['lo', 'hi', 'kp', 'ki']
    definition.equations_raw = ['inc(x)=0', 'x.=ki*u', 'y=picontrol_const(x,lo,hi,kp*u)']
    circuit = DgsCircuit()
    circuit.blkdefs.append(definition)
    parsed = parse_dgs_block_definitions_from_circuit(circuit)['PI']
    assert not parsed.unsupported_lines
    values = {parsed.symbol_table[name].uid: value for name, value in {
        'x': state, 'u': input_value, 'lo': -1., 'hi': 1., 'kp': 1., 'ki': 2.}.items()}
    assert parsed.algebraic_rhs['y'].eval_uid(values) == pytest.approx(output)
    assert parsed.state_rhs['x'].eval_uid(values) == pytest.approx(derivative)
    assert parsed.init_rhs['x'].eval_uid({}) == 0.


def test_native_vsc_pi_definition_is_supported():
    circuit = DgsCircuit()
    circuit.parse_dgs(str(DATA / 'vsc_base.dgs'))
    parsed = parse_dgs_block_definitions_from_circuit(circuit)
    native_pi = [block for block in parsed.values()
                 if any('picontrol_const' in line for line in block.blkdef.equations_raw)]
    assert native_pi
    assert all(not block.unsupported_lines for block in native_pi)


def test_pi_constant_bounds_reject_signal_dependent_limits():
    definition = BlkDef()
    definition.ID = 'invalidPI'
    definition.inputs = ['u', 'limit']
    definition.states = ['x']
    definition.outputs = ['y']
    definition.equations_raw = ['x.=u', 'y=picontrol_const(x,-limit,limit,u)']
    circuit = DgsCircuit()
    circuit.blkdefs.append(definition)
    parsed = parse_dgs_block_definitions_from_circuit(circuit)[definition.ID]
    assert parsed.unsupported_lines == ['y=picontrol_const(x,-limit,limit,u)']


@pytest.mark.parametrize('delay,threshold,model,supported', [
    (1, None, 1, False), (None, .5, 1, False), (None, .5, 3, True),
])
def test_genstat_fallback_rejects_incomplete_protection_and_unsupported_delay(delay, threshold, model, supported):
    source = ElmGenstat()
    source.iSimModel, source.iDelay, source.umin = model, delay, threshold
    device = StaticGenerator()
    result = build_dgs_elmgenstat_fallback(MultiCircuit(), device, source, Logger())
    assert (result is not None) is supported
    assert device.active is supported


def test_parallel_genstat_resolution_uses_exact_ids_and_declared_unit_count():
    source = ElmGenstat()
    source.ID, source.ngnum = 'native', 37
    exact = ElmGenstat()
    exact.ID = 'native:1'
    assert resolve_dgs_elmgenstat_source('native:1', [source, exact]) is exact
    assert resolve_dgs_elmgenstat_source('native:37', [source]) is source
    assert resolve_dgs_elmgenstat_source('native:38', [source]) is None
    assert resolve_dgs_elmgenstat_source('native:01', [source]) is None
