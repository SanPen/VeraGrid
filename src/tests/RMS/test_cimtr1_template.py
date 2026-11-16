# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""PSS/E CIMTR1 unsaturated two-cage template checks."""

import pytest

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.induction_machines.cimtr1 import (
    Cimtr1Parameters,
    build_cimtr1_template,
)
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var


def test_cimtr1_maps_source_machine_constants_to_flux_kernel() -> None:
    """Use the source reactances, times and inertia in the native equations."""
    settings: Cimtr1Parameters = Cimtr1Parameters(
        t_prime=0.7,
        t_double_prime=0.08,
        inertia=1.2,
        x=2.4,
        x_prime=0.55,
        x_double_prime=0.22,
        x_leakage=0.12,
        ra=0.03,
    )
    template: RmsModelTemplate = build_cimtr1_template(
        VarFactory(), 'CIMTR1_MAP', settings,
    )
    parameters: dict[str, float] = dict()
    variable: Var
    for variable in template.block.event_dict:
        expression: Expr | Const = template.block.event_dict[variable]
        if isinstance(expression, Const):
            parameters[variable.name] = expression.value
        else:
            pass

    assert parameters['RaPu_CIMTR1_MAP'] == settings.ra
    assert parameters['XsPu_CIMTR1_MAP'] == settings.x
    assert parameters['XpPu_CIMTR1_MAP'] == settings.x_prime
    assert parameters['XppPu_CIMTR1_MAP'] == settings.x_double_prime
    assert parameters['Tp0_CIMTR1_MAP'] == settings.t_prime
    assert parameters['Tpp0_CIMTR1_MAP'] == settings.t_double_prime
    assert parameters['H_CIMTR1_MAP'] == settings.inertia


def test_cimtr1_double_cage_slip_terms_match_source_state_equations() -> None:
    """Evaluate both subtransient states against the published d/q equations."""
    template: RmsModelTemplate = build_cimtr1_template(VarFactory(), 'CIMTR1_SLIP')
    d_axis: Expr = template.block.state_eqs[2]
    q_axis: Expr = template.block.state_eqs[3]
    d_values: dict[str, float] = dict(
        (variable.name, 0.0) for variable in d_axis.get_vars()
    )
    q_values: dict[str, float] = dict(
        (variable.name, 0.0) for variable in q_axis.get_vars()
    )
    operating_values: dict[str, float] = dict(
        FNomHz_CIMTR1_SLIP=50.0, OmegaPu_CIMTR1_SLIP=0.98,
        EprPu_CIMTR1_SLIP=0.3, EpiPu_CIMTR1_SLIP=0.4,
        EpprPu_CIMTR1_SLIP=0.2, EppiPu_CIMTR1_SLIP=0.1,
        IrPu_CIMTR1_SLIP=0.05, IiPu_CIMTR1_SLIP=-0.03,
        XsPu_CIMTR1_SLIP=2.4, XpPu_CIMTR1_SLIP=0.55,
        XppPu_CIMTR1_SLIP=0.22, Tp0_CIMTR1_SLIP=0.7,
        Tpp0_CIMTR1_SLIP=0.08,
    )
    d_values.update(operating_values)
    q_values.update(operating_values)
    omega_base: float = 2.0 * 3.141592653589793 * 50.0
    slip: float = 0.02
    e_d_prime_derivative: float = (
        omega_base * slip * operating_values['EpiPu_CIMTR1_SLIP']
        - (operating_values['EprPu_CIMTR1_SLIP']
           + (operating_values['XsPu_CIMTR1_SLIP'] - operating_values['XpPu_CIMTR1_SLIP'])
           * operating_values['IiPu_CIMTR1_SLIP']) / operating_values['Tp0_CIMTR1_SLIP']
    )
    e_q_prime_derivative: float = (
        -omega_base * slip * operating_values['EprPu_CIMTR1_SLIP']
        - (operating_values['EpiPu_CIMTR1_SLIP']
           - (operating_values['XsPu_CIMTR1_SLIP'] - operating_values['XpPu_CIMTR1_SLIP'])
           * operating_values['IrPu_CIMTR1_SLIP']) / operating_values['Tp0_CIMTR1_SLIP']
    )
    expected_d_axis: float = (
        e_d_prime_derivative
        - omega_base * slip * (operating_values['EpiPu_CIMTR1_SLIP']
                               - operating_values['EppiPu_CIMTR1_SLIP'])
        - ((operating_values['EpprPu_CIMTR1_SLIP'] - operating_values['EprPu_CIMTR1_SLIP'])
           + (operating_values['XpPu_CIMTR1_SLIP'] - operating_values['XppPu_CIMTR1_SLIP'])
           * operating_values['IiPu_CIMTR1_SLIP']) / operating_values['Tpp0_CIMTR1_SLIP']
    )
    expected_q_axis: float = (
        e_q_prime_derivative
        + omega_base * slip * (operating_values['EprPu_CIMTR1_SLIP']
                               - operating_values['EpprPu_CIMTR1_SLIP'])
        - ((operating_values['EppiPu_CIMTR1_SLIP'] - operating_values['EpiPu_CIMTR1_SLIP'])
           - (operating_values['XpPu_CIMTR1_SLIP'] - operating_values['XppPu_CIMTR1_SLIP'])
           * operating_values['IrPu_CIMTR1_SLIP']) / operating_values['Tpp0_CIMTR1_SLIP']
    )

    assert d_axis.eval(**d_values) == pytest.approx(expected_d_axis)
    assert q_axis.eval(**q_values) == pytest.approx(expected_q_axis)


def test_cimtr1_rejects_unrepresented_model_reductions() -> None:
    """Do not hide saturation or single-cage requests behind the generic core."""
    try:
        build_cimtr1_template(
            VarFactory(), 'CIMTR1_SAT', Cimtr1Parameters(se1=0.1, se2=0.2),
        )
    except ValueError:
        pass
    else:
        raise AssertionError('CIMTR1 saturation must remain outside this reduction')

    try:
        build_cimtr1_template(
            VarFactory(), 'CIMTR1_SINGLE', Cimtr1Parameters(t_double_prime=0.0),
        )
    except ValueError:
        pass
    else:
        raise AssertionError('CIMTR1 single-cage reduction must remain outside this kernel')
