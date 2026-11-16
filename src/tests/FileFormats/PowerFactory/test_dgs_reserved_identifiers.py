# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Keep DSL identifiers distinct from Python keywords, functions and aliases."""

import math

import pytest

from VeraGridEngine.IO.dgs.dgs_circuit import DgsCircuit
from VeraGridEngine.IO.dgs.dgs_objects import BlkDef
from VeraGridEngine.IO.dgs.dgs_to_blocks import DgsExpressionParser, ParsedDgsBlockDefinition, parse_dgs_block_definitions_from_circuit
from VeraGridEngine.Utils.Symbolic.symbolic import Expr, Var


@pytest.mark.parametrize('name', ('in', 'lambda', 'class', 'and', 'or', 'not', 'True', 'None'))
def test_keyword_identifiers_keep_the_original_symbol(name: str) -> None:
    """Use a temporary parser alias while retaining the source Var identity.

    :param name: Python keyword used as a valid declared DSL signal.
    :return: None.
    """
    variable: Var = Var(name)
    parser: DgsExpressionParser = DgsExpressionParser(dict(((name, variable),)))
    expression: Expr = parser.parse(f'{name}+1')
    assert expression.eval_uid(dict(((variable.uid, 2.0),))) == pytest.approx(3.0)
    assert variable.name == name
    assert parser.symbol_table[name] is variable


def test_lpf_derivative_accepts_an_input_named_in() -> None:
    """Translate the exact DFIG LPF equation without changing its input name.

    :return: None.
    """
    definition: BlkDef = BlkDef()
    definition.ID = '13'
    definition.loc_name = 'LPF'
    definition.inputs = list(('in',))
    definition.states = list(('x',))
    definition.params = list(('T',))
    definition.equations_raw = list(('inc(x)=in', 'x.=(in-x)/T'))
    source: DgsCircuit = DgsCircuit()
    source.blkdefs.append(definition)
    parsed: ParsedDgsBlockDefinition = parse_dgs_block_definitions_from_circuit(source)['13']
    assert parsed.unsupported_lines == list()
    bindings: dict[int, float] = dict((
        (parsed.symbol_table['in'].uid, 12.0),
        (parsed.symbol_table['x'].uid, 2.0),
        (parsed.symbol_table['T'].uid, 5.0),
    ))
    assert parsed.state_rhs['x'].eval_uid(bindings) == pytest.approx(2.0)
    assert parsed.init_rhs['x'] is parsed.symbol_table['in']
    assert parsed.symbol_table['in'].name == 'in'


def test_keyword_substitution_does_not_corrupt_function_calls_or_longer_names() -> None:
    """Distinguish sin/min calls, homonymous variables and identifiers containing in.

    :return: None.
    """
    names: tuple[str, ...] = ('in', 'sin', 'min', 'input', 'in1', 'minimum')
    symbols: dict[str, Var] = dict((name, Var(name)) for name in names)
    values: dict[str, float] = dict((('in', 0.5), ('sin', 5.0), ('min', 4.0),
                                    ('input', 2.0), ('in1', 3.0), ('minimum', 7.0)))
    parser: DgsExpressionParser = DgsExpressionParser(symbols)
    expression: Expr = parser.parse('sin(in)+min(in,input)+sin+min+in1+minimum')
    bindings: dict[int, float] = dict((variable.uid, values[name]) for name, variable in symbols.items())
    assert expression.eval_uid(bindings) == pytest.approx(math.sin(0.5) + 0.5 + 5.0 + 4.0 + 3.0 + 7.0)


def test_generated_aliases_cannot_collide_or_be_substituted_again() -> None:
    """Reserve both declared identifiers and previously generated parser aliases.

    :return: None.
    """
    names: tuple[str, ...] = ('in', '__dgs_var_0', 'dgs_var_0')
    symbols: dict[str, Var] = dict((name, Var(name)) for name in names)
    parser: DgsExpressionParser = DgsExpressionParser(symbols)
    expression: Expr = parser.parse('in+__dgs_var_0+dgs_var_0')
    bindings: dict[int, float] = dict((symbols[name].uid, float(index + 1)) for index, name in enumerate(names))
    assert expression.eval_uid(bindings) == pytest.approx(6.0)
    assert tuple(variable.name for variable in symbols.values()) == names
    # Late registrations invalidate the scanner without changing existing aliases.
    late_name: str = parser.preprocess('in')
    late_variable: Var = Var(late_name)
    parser.register_symbol(late_name, late_variable)
    expression = parser.parse(f'in+{late_name}')
    assert expression.eval_uid(dict(((symbols['in'].uid, 2.0), (late_variable.uid, 4.0)))) == pytest.approx(6.0)


def test_dsl_boolean_operators_and_quoted_text_are_preserved() -> None:
    """Translate operators without confusing them with reserved variable names.

    :return: None.
    """
    incoming: Var = Var('in')
    conjunction: Var = Var('and')
    parser: DgsExpressionParser = DgsExpressionParser(dict((('in', incoming), ('and', conjunction))))
    expression: Expr = parser.parse('(in>0) .and. (and>0)')
    assert expression.eval_uid(dict(((incoming.uid, 1.0), (conjunction.uid, -1.0)))) == pytest.approx(0.0)
    assert expression.eval_uid(dict(((incoming.uid, 1.0), (conjunction.uid, 1.0)))) == pytest.approx(1.0)
    assert "'in=.and.^class'" in parser.preprocess("output(in>0, 'in=.and.^class')")
