# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Regression coverage against untouched native PowerFactory 2024 exports."""

from pathlib import Path
import csv
import hashlib
import json

import pytest

from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.IO.dgs.dgs_circuit import DgsCircuit
from VeraGridEngine.IO.dgs.dgs_objects import ElmComp, ElmGenstat, BlkDef, ElmDsl, ElmVsc, ElmVscmono
from VeraGridEngine.IO.dgs.dgs_to_blocks import (
    DgsExpressionParser,
    build_blkdef_statement_support_report,
    extract_elmcomp_direct_instances,
    parse_dgs_block_definitions_from_circuit,
)
from VeraGridEngine.IO.dgs.dgs_to_veragrid import dgs_to_circuit
from VeraGridEngine.IO.dgs.dynamic_models.dynamic_model_import import (
    convert_and_add_dgs_dynamic_templates_to_circuit,
    DynamicModelImport,
    get_unsupported_dgs_vsc_options,
)
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.enumerations import DeviceType, DynamicSimulationMode
from tests.FileFormats.PowerFactory.dgs_export_rows import read_rows_by_path


ROOT = Path(__file__).resolve().parents[4]
DATA = ROOT / 'src/tests/data/grids/DGS/native_options_pf2024'
MANIFEST = json.loads((DATA / 'manifest.json').read_text())


def read_circuit(name):
    circuit = DgsCircuit()
    circuit.parse_dgs(str(DATA / name))
    return circuit


@pytest.mark.parametrize('entry', MANIFEST['files'], ids=lambda entry: entry['file'])
def test_native_exports_are_intact_and_references_resolve(entry):
    path = DATA / entry['file']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == entry['sha256']
    assert entry['code'] == 0 and not entry['errors'] and not entry['warnings']
    ids, references, columns, pointer_indices = set(), [], [], []
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        if line.startswith('$$'):
            header = next(csv.reader([line[2:]], delimiter=';'))
            columns = header[1:]
            names = [column.rsplit("(", 1)[0] for column in columns]
            assert len(names) == len(set(names))
            pointer_indices = [i for i, col in enumerate(columns) if col.endswith('(p)')]
        elif line.startswith('  '):
            row = next(csv.reader([line.strip()], delimiter=';'))
            assert len(row) == len(columns)
            assert row[0] not in ids
            ids.add(row[0])
            references.extend(row[i] for i in pointer_indices if row[i] not in ('', '*', '0'))
    assert set(references) <= ids
    circuit = read_circuit(entry['file'])
    assert len(circuit.elmdsls) == entry['tables'].get('ElmDsl', 0)
    assert len(circuit.blkdefs) == entry['tables'].get('BlkDef', 0)


@pytest.mark.parametrize('entry', [e for e in MANIFEST['files'] if isinstance(e['variant'], dict)],
                         ids=lambda entry: entry['file'])
def test_native_option_pairs_change_exactly_one_field(entry):
    before = read_rows_by_path(DATA / 'bess_base.dgs')
    after = read_rows_by_path(DATA / entry['file'])
    assert before.keys() == after.keys()
    changes = [(key, field, old, after[key].get(field))
               for key, row in before.items() for field, old in row.items()
               if old != after[key].get(field)]
    assert len(changes) == 1
    key, field, old, new = changes[0]
    assert field == entry['variant']['attribute']
    assert float(old) == entry['variant']['before']
    assert float(new) == entry['variant']['after']


@pytest.mark.parametrize('filename,mode,expected', [
    ('bess_base.dgs', 0, 7.0), ('bess_virtual_admittance_dynamic.dgs', 1, 2.0)])
def test_native_dsl_selector_reaches_instance_and_select_equation(filename, mode, expected):
    circuit = read_circuit(filename)
    instance = next(d for d in circuit.elmdsls if d.loc_name == 'Virtual Admittance')
    assert instance.get_parameter_map() == {'xv': .1, 'rv': .01, 'f1': 50., 'va_mode': mode}
    root = next(c for c in circuit.elmcomps if c.loc_name == 'Grid Forming Converter')
    entry = next(e for e in extract_elmcomp_direct_instances(circuit, root) if e.element_id == instance.ID)
    assert entry.parameter_values['va_mode'] == mode
    parsed = parse_dgs_block_definitions_from_circuit(circuit)[instance.typ_id]
    assert not parsed.unsupported_lines
    assert len(parsed.state_rhs) == 4
    env = {parsed.symbol_table[name].uid: value for name, value in {
        'va_mode': mode, 'i1d_hat_dyn': 2., 'i1d_hat_nodyn': 7.}.items()}
    # Evaluate the accepted-step selector projection before its algebraic output.
    selector = next(logic for logic in parsed.procedural_logic
                    if logic.output_var_name.endswith('__proc_select_0'))
    env[selector.output_var_uid] = selector.source_expr.eval_uid(env)
    assert parsed.algebraic_rhs['i1d_hat'].eval_uid(env) == expected


@pytest.mark.parametrize('filename', sorted(p.name for p in DATA.glob('nine_bus*.dgs')))
def test_native_machine_and_excitation_definitions_parse(filename):
    circuit = read_circuit(filename)
    parsed = parse_dgs_block_definitions_from_circuit(circuit)
    assert parsed
    assert not [(b.blkdef.loc_name, b.unsupported_lines) for b in parsed.values() if b.unsupported_lines]
    assert len(circuit.elmsyms) == 3


def test_native_vsc_options_are_preserved_and_unsupported_modes_are_visible():
    base = read_circuit('bess_base.dgs').elmvscmonos[0]
    assert (base.i_ctrl, base.i_mod, base.iVIsource, base.iVacMax) == (0, 0, 1, 0)
    assert base.Pmmax == 1.0
    assert base.Kd == pytest.approx(.1)
    assert base.Td == pytest.approx(.01)
    coupled = read_circuit('bess_coupled_converter.dgs').elmvscmonos[0]
    assert get_unsupported_dgs_vsc_options(coupled) == []
    assert any('iVIsource=1' in item for item in get_unsupported_dgs_vsc_options(base))
    controller = read_circuit('bess_current_controller_on.dgs').elmvscmonos[0]
    assert any('i_ctrl=1' in item for item in get_unsupported_dgs_vsc_options(controller))
    modulation = read_circuit('bess_modulation_1.dgs').elmvscmonos[0]
    assert any('i_mod=1' in item for item in get_unsupported_dgs_vsc_options(modulation))


@pytest.mark.parametrize('kind', [ElmVsc, ElmVscmono])
def test_legacy_vsc_missing_selectors_remain_unknown(kind):
    value = kind.parse_line('1;VSC', {'FID': 0, 'loc_name': 1})
    assert value.i_ctrl is None and value.i_mod is None and value.iVIsource is None
    assert not get_unsupported_dgs_vsc_options(value)


def test_scalar_and_vector_symbol_fields_preserve_order_and_declared_size():
    scalar = BlkDef.parse_line('1;u;y;x;a,b;z', {
        'FID': 0, 'cInput': 1, 'cOutput': 2, 'cStates': 3, 'cParams': 4, 'cIntern': 5})
    vector = BlkDef.parse_line('1;u;y;x;2;a;b;ignored;z', {
        'FID': 0, 'cInput:0': 1, 'cOutput:0': 2, 'cStates:0': 3,
        'cParams:SIZEROW': 4, 'cParams:0': 5, 'cParams:1': 6, 'cParams:2': 7, 'cIntern:0': 8})
    assert (scalar.inputs, scalar.outputs, scalar.states, scalar.params, scalar.internals) == (
        vector.inputs, vector.outputs, vector.states, vector.params, vector.internals)
    legacy = ElmDsl.parse_line('1;a,b;2;3;4', {
        'FID': 0, 'parameterNames': 1, 'params:SIZEROW': 2, 'params:0': 3, 'params:1': 4})
    assert legacy.get_parameter_map() == {'a': 3., 'b': 4.}


def test_native_current_limit_symbols_keep_distinct_underscores():

    names = ['idpos_', 'idpos_sat', 'Iq_max', 'Iq_max_', 'Iq_max_0']
    symbols = {name: Var(name) for name in names}
    parser = DgsExpressionParser(symbols)
    values = {symbols[name].uid: float(index + 1) for index, name in enumerate(names)}
    for index, name in enumerate(names):
        assert parser.parse(name).eval_uid(values) == index + 1
    assert parser.parse('idpos_sat-Iq_max_+Iq_max_0').eval_uid(values) == 3.


@pytest.mark.parametrize('filename', ['bess_base.dgs', 'nine_bus_avr_pss.dgs'])
def test_native_statement_support_report_matches_parser(filename):

    circuit = read_circuit(filename)
    parsed = parse_dgs_block_definitions_from_circuit(circuit)
    assert not [(b.blkdef.loc_name, b.unsupported_lines) for b in parsed.values() if b.unsupported_lines]
    for definition in circuit.blkdefs:
        assert not [(entry.statement, entry.detail)
                    for entry in build_blkdef_statement_support_report(definition)
                    if entry.status == 'unsupported']


@pytest.mark.parametrize('field', ['i_ctrl', 'i_mod', 'iVIsource'])
def test_explicit_unsupported_vsc_option_prevents_physical_runtime_assignment(field):
    """Exercise the importer gate using a known complete graph, changed in memory."""

    path = DATA.parent / 'hvdc_vsc_v1_complete_static_dynamic.dgs'
    circuit = DgsCircuit()
    circuit.parse_dgs(str(path))
    for converter in circuit.elmvscmonos:
        setattr(converter, field, 1)
    destination = dgs_to_circuit(path=str(path))
    logger = Logger()
    result = convert_and_add_dgs_dynamic_templates_to_circuit(
        circuit, destination, DynamicSimulationMode.RMS, logger)
    assert result.templates_by_root_dgs_id
    assert all(template.tpe == DeviceType.DynamicModelHostDevice
               for template in result.templates_by_root_dgs_id.values())
    warnings = [entry for entry in logger.entries
                if entry.msg == 'DGS converter options require an unsupported RMS equipment model']
    assert len(warnings) == len(circuit.elmvscmonos)
    assert all(field + '=1' in str(entry.value) for entry in warnings)


@pytest.mark.parametrize('selected_root,outserv,expected', [
    ('selected', 0, True), ('other', 0, False), ('selected', 1, False),
])
def test_elmgenstat_native_model_selection_preserves_ownership(selected_root, outserv, expected):
    """Keep the incoming native workflow's class import and source selection."""

    source = ElmGenstat()
    source.ID = 'static-generator'
    source.c_pmod = selected_root
    source.outserv = outserv
    root = ElmComp()
    root.ID = 'selected'
    root.outserv = 0
    circuit = DgsCircuit()
    circuit.elmgenstats.append(source)
    circuit.elmcomps.append(root)
    importer = DynamicModelImport(circuit, MultiCircuit(), DynamicSimulationMode.RMS, Logger())
    identity = (source.ID, DeviceType.GeneratorDevice, 'ElmGenstat', 'Static generator')
    assert importer._is_selected_dgs_root_for_host(root, identity) is expected
