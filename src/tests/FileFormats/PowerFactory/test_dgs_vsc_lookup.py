# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Native VSC lookup decoding and instance-specific symbolic specialization."""
from pathlib import Path

import pytest

from VeraGridEngine.IO.dgs.dgs_circuit import DgsCircuit
from VeraGridEngine.IO.dgs.dgs_objects import BlkDef
from VeraGridEngine.IO.dgs.dgs_to_blocks import (
    DgsLookupTable,
    _bind_graphical_reference_lookup_tables,
    _build_dgs_lookup_table,
    _expand_dgs_lookup_calls,
    _parse_blkdef,
    get_elmdsl_lookup_tables,
)
from VeraGridEngine.Templates.basic_block_runtime import (
    _build_clipped_lookup_expression,
)
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
from VeraGridEngine.enumerations import DynamicSimulationMode

DATA = Path(__file__).resolve().parents[2] / 'data/grids/DGS/native_lookup_pf2024'


def _evaluate(expression: Expr, values: dict[int, float], point_values: dict[Var, Const]) -> float:
    """Evaluate an expanded lookup with its point parameters.

    :param expression: Expression after lookup expansion.
    :param values: Input values by variable UID.
    :param point_values: Point parameters of the instance.
    :return: Numeric value.
    """
    full: dict[int, float] = dict(values)
    full.update((variable.uid, float(value.value)) for variable, value in point_values.items())
    return expression.eval_uid(full)


@pytest.mark.parametrize('value,expected', [(-2., 1.), (0., 1.), (.5, 2.),
                                          (1., 3.), (2., 2.), (3., 1.), (5., 1.)])
def test_linear_lookup_interpolates_and_clamps(value, expected):
    argument = Var('u')
    x_vars = [Var(f'x{i}') for i in range(3)]
    y_vars = [Var(f'y{i}') for i in range(3)]
    expression = _build_clipped_lookup_expression(argument, x_vars, y_vars)
    values = {argument.uid: value}
    values.update((x.uid, xv) for x, xv in zip(x_vars, (0., 1., 3.)))
    values.update((y.uid, yv) for y, yv in zip(y_vars, (1., 3., 1.)))
    assert expression.eval_uid(values) == pytest.approx(expected)


@pytest.mark.parametrize('points', [[], [[0., 1.]], [[0., 1.], [0., 2.]],
                                   [[1., 1.], [0., 2.]], [[0., 1.], [1., float('nan')]]])
def test_ambiguous_or_invalid_tables_fail_explicitly(points):
    assert _build_dgs_lookup_table(points) is None


def test_native_vsc_arrays_bind_through_reference_aliases():
    circuit = DgsCircuit()
    circuit.parse_dgs(str(DATA / 'vsc_lookup_tables.dgs'))
    types = {definition.ID: definition for definition in circuit.blkdefs}
    instances = {instance.loc_name: instance for instance in circuit.elmdsls}
    for instance_name, reference_name, array_name, count in [
        ('AC Offshore Controller_V3', 'Udc_Feedforward', 'array_Pm', 8),
        ('Control', 'CurrLim', 'array_iqlim', 23),
    ]:
        instance = instances[instance_name]
        tables = get_elmdsl_lookup_tables(instance, types[instance.typ_id], circuit.intmats)
        assert len(tables[array_name].x_points) == count
        reference = next(ref for ref in circuit.blkrefs if ref.cdisName == reference_name)
        child = types[reference.typ_id]
        parsed = _parse_blkdef(child, {})
        bound = _bind_graphical_reference_lookup_tables(reference, parsed, tables)
        assert bound[array_name] is tables[array_name]
        assert not any('lapprox' in line for line in parsed.unsupported_lines)
        _expand_dgs_lookup_calls(parsed, bound, dict())


def test_shared_definition_keeps_instance_curves_and_domain_separate():
    definition = BlkDef()
    definition.ID = 'lookup'
    definition.inputs = ['u']
    definition.outputs = ['y']
    definition.params = ['array_curve']
    definition.equations_raw = ['y=lapprox(u,array_curve)']
    parsed = _parse_blkdef(definition, {}, simulation_domain=DynamicSimulationMode.EMT)
    assert not parsed.unsupported_lines
    assert parsed.simulation_domain == DynamicSimulationMode.EMT
    results = list()
    for slope in (2., 4.):
        mapping: dict = dict()
        points = _expand_dgs_lookup_calls(parsed, {'array_curve': DgsLookupTable((0., 1.), (0., slope))}, mapping)
        results.append(_evaluate(parsed.algebraic_rhs['y'].subs(mapping), {parsed.symbol_table['u'].uid: .5}, points))
    assert results == [1., 2.]


@pytest.mark.parametrize('enabled,expected', [(0., 2.), (1., 1.)])
def test_native_menu_selector_chooses_the_instance_table(enabled, expected):
    definition = BlkDef()
    definition.ID = 'select_lookup'
    definition.inputs = ['u']
    definition.outputs = ['y']
    definition.params = ['enabled', 'array_a', 'array_b']
    definition.equations_raw = ['y=lapprox(u,select_const(enabled,array_a,array_b))']
    parsed = _parse_blkdef(definition, {})
    assert not parsed.unsupported_lines
    mapping: dict = dict()
    points = _expand_dgs_lookup_calls(parsed, {'array_a': DgsLookupTable((0., 1.), (0., 2.)),
                                               'array_b': DgsLookupTable((0., 1.), (0., 4.))}, mapping)
    values = {parsed.symbol_table['u'].uid: .5, parsed.symbol_table['enabled'].uid: enabled}
    assert len(parsed.procedural_logic) == 1
    selector = parsed.procedural_logic[0]
    values[selector.output_var_uid] = _evaluate(selector.source_expr.subs(mapping), values, points)
    assert _evaluate(parsed.algebraic_rhs['y'].subs(mapping), values, points) == pytest.approx(expected)
