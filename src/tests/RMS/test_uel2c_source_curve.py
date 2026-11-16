# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""PSS/E UEL2C source-curve interpolation checks."""
from __future__ import annotations

import pytest

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.excitation_limiters.uel2c import (
    Uel2cGainReductionMode,
    Uel2cParameters,
    Uel2cThirdQuadrantMode,
    build_uel2c_template,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var


def test_uel2c_uses_supplied_piecewise_linear_curve_with_linear_tails() -> None:
    """Evaluate source-table segments and both extrapolation tails.

    :return: None.
    """
    points: tuple[tuple[float, float], ...] = (
        (-0.5, -0.4), (0.0, -0.3), (0.5, -0.1), (1.0, 0.2),
    )
    block: Block = build_uel2c_template(
        VarFactory(),
        curve_points=points,
    ).block
    input_power: Var = next(
        variable for variable in block.state_vars
        if variable.name == 'uel.firstOrder1.y_Uel2c'
    )
    curve_output: Var = next(
        variable for variable in block.algebraic_vars
        if variable.name == 'uel.combiTable1Ds.y[1]_Uel2c'
    )
    curve_equation: Expr = next(
        equation for equation in block.algebraic_eqs
        if equation.left.uid == curve_output.uid
    )
    for active_power, expected_q_limit in (
        (-1.0, -0.5), (-0.25, -0.35), (0.25, -0.2),
        (0.75, 0.05), (1.5, 0.5),
    ):
        assert float(curve_equation.right.eval_uid({input_power.uid: active_power})) == pytest.approx(
            expected_q_limit
        )


def test_uel2c_mirrors_source_curve_in_third_quadrant_when_selected() -> None:
    """Mirror negative active power across the reactive-power axis for ICON=0.

    :return: None.
    """
    points: tuple[tuple[float, float], ...] = (
        (0.0, -0.4), (0.5, -0.2), (1.0, 0.0),
    )
    block: Block = build_uel2c_template(
        VarFactory(),
        curve_points=points,
        third_quadrant_mode=Uel2cThirdQuadrantMode.MIRROR,
    ).block
    input_power: Var = next(
        variable for variable in block.state_vars
        if variable.name == 'uel.firstOrder1.y_Uel2c'
    )
    curve_output: Var = next(
        variable for variable in block.algebraic_vars
        if variable.name == 'uel.combiTable1Ds.y[1]_Uel2c'
    )
    curve_equation: Expr = next(
        equation for equation in block.algebraic_eqs
        if equation.left.uid == curve_output.uid
    )
    assert float(curve_equation.right.eval_uid({input_power.uid: -0.25})) == pytest.approx(-0.3)


def test_uel2c_applies_source_final_output_limits() -> None:
    """Apply VULMIN/VULMAX after the internal lead-lag limits.

    :return: None.
    """
    template: RmsModelTemplate = build_uel2c_template(
        VarFactory(), output_limits=(-0.25, 0.25),
    )
    block: Block = template.block
    output: Var = block.out_vars[0]
    output_equation: Expr = next(
        equation for equation in block.algebraic_eqs
        if equation.left.uid == output.uid
    )
    bindings: dict[int, float] = dict(
        (variable.uid, 0.0)
        for variable in block.state_vars + block.algebraic_vars + block.in_vars
        + list(block.event_dict)
    )
    bindings[next(variable for variable in block.algebraic_vars
                  if variable.name == 'uel.limitedLeadLag1.gain.y_Uel2c').uid] = 2.0
    bindings[next(variable for variable in block.event_dict
                  if variable.name == 'uel.limitedLeadLag1.limiter.uMax_Uel2c').uid] = 99.0
    bindings[next(variable for variable in block.event_dict
                  if variable.name == 'uel.limitedLeadLag1.limiter.uMin_Uel2c').uid] = -99.0
    vulmax: Var = next(parameter for parameter in block.event_dict
                       if parameter.name == 'uel.VULMaxPu_Uel2c')
    vulmin: Var = next(parameter for parameter in block.event_dict
                       if parameter.name == 'uel.VULMinPu_Uel2c')
    bindings[vulmax.uid] = 0.25
    bindings[vulmin.uid] = -0.25
    assert float(output_equation.right.eval_uid(bindings)) == pytest.approx(0.25)
    bindings[next(variable for variable in block.algebraic_vars
                  if variable.name == 'uel.limitedLeadLag1.gain.y_Uel2c').uid] = -2.0
    assert float(output_equation.right.eval_uid(bindings)) == pytest.approx(-0.25)


@pytest.mark.parametrize(
    ('mode', 'switch_value'),
    (
        (Uel2cGainReductionMode.FIXED, 1.0),
        (Uel2cGainReductionMode.ADJUSTABLE, 0.0),
    ),
)
def test_uel2c_maps_gain_reduction_position_to_source_path(
        mode: Uel2cGainReductionMode,
        switch_value: float,
) -> None:
    """Select fixed KFIX or filtered KADJ using the source ICON position.

    :param mode: Native source-equivalent gain-reduction mode.
    :param switch_value: Expected internal graph selector.
    :return: None.
    """
    block: Block = build_uel2c_template(
        VarFactory(), gain_reduction_mode=mode,
    ).block
    switch: Var = next(
        variable for variable in block.event_dict
        if variable.name == 'uel.Sw1_Uel2c'
    )
    switch_value_expr: Expr | Const = block.event_dict[switch]
    assert isinstance(switch_value_expr, Const)
    assert float(switch_value_expr.value) == pytest.approx(switch_value)
    switch_output: Var = next(
        variable for variable in block.algebraic_vars
        if variable.name == 'uel.switch.y_Uel2c'
    )
    switch_equation: Expr = next(
        equation for equation in block.algebraic_eqs
        if equation.left.uid == switch_output.uid
    )
    bindings: dict[int, float] = dict(
        (variable.uid, 0.0)
        for variable in block.state_vars + block.algebraic_vars + block.in_vars
        + list(block.event_dict)
    )
    bindings[next(variable for variable in block.algebraic_vars + list(block.event_dict)
                  if variable.name == 'uel.booleanConstant.k_Uel2c').uid] = switch_value
    bindings[next(variable for variable in block.algebraic_vars + list(block.event_dict)
                  if variable.name == 'uel.const.k_Uel2c').uid] = 0.25
    bindings[next(variable for variable in block.algebraic_vars
                  if variable.name == 'uel.limitedFirstOrder.y_Uel2c').uid] = 0.75
    expected_gain: float = 0.25 if mode is Uel2cGainReductionMode.FIXED else 0.75
    assert float(switch_equation.right.eval_uid(bindings)) == pytest.approx(expected_gain)


def test_uel2c_maps_source_parameters_to_graph_variables() -> None:
    """Replace the generated example constants with all supplied model values.

    :return: None.
    """
    parameters: Uel2cParameters = Uel2cParameters(
        k1=2, k2=0, tuv=.11, tup=.12, tuq=.13, kui=2.4, kul=2.5,
        vuimax=.26, vuimin=-.27, kuf=2.8, kfb=2.9, tul=.3, tu1=.31,
        tu2=.32, tu3=.33, tu4=.34, vulmax=.95, vulmin=-.96, vbias=.97,
        kfix=.98, tadj=.39, tqref=.4, vuelmax2=.91, vuelmin2=-.92,
        vuelmax1=.93, vuelmin1=-.94, xq=1.05,
    )
    block: Block = build_uel2c_template(VarFactory(), parameters=parameters).block
    expected_values: tuple[tuple[str, float], ...] = (
        ('uel.K1_Uel2c', 2.0), ('uel.K2_Uel2c', 0.0),
        ('uel.tUV_Uel2c', .11), ('uel.tUP_Uel2c', .12),
        ('uel.tUQ_Uel2c', .13), ('uel.Kui_Uel2c', 2.4),
        ('uel.Kul_Uel2c', 2.5), ('uel.VUiMaxPu_Uel2c', .26),
        ('uel.VUiMinPu_Uel2c', -.27), ('uel.Kuf_Uel2c', 2.8),
        ('uel.KFb_Uel2c', 2.9), ('uel.tUl_Uel2c', .3),
        ('uel.tU1_Uel2c', .31), ('uel.tU2_Uel2c', .32),
        ('uel.tU3_Uel2c', .33), ('uel.tU4_Uel2c', .34),
        ('uel.VULMaxPu_Uel2c', .95), ('uel.VULMinPu_Uel2c', -.96),
        ('uel.VBiasPu_Uel2c', .97), ('uel.VBias0Pu_Uel2c', .97),
        ('uel.KFix_Uel2c', .98), ('uel.tAdj_Uel2c', .39),
        ('uel.tQRef_Uel2c', .4), ('uel.VUel2MaxPu_Uel2c', .91),
        ('uel.VUel2MinPu_Uel2c', -.92), ('uel.VUel1MaxPu_Uel2c', .93),
        ('uel.VUel1MinPu_Uel2c', -.94), ('uel.XqPu_Uel2c', 1.05),
    )
    for parameter_name, expected_value in expected_values:
        parameter: Var = next(
            variable for variable in block.event_dict
            if variable.name == parameter_name
        )
        actual_value: Expr | Const = block.event_dict[parameter]
        assert isinstance(actual_value, Const)
        assert float(actual_value.value) == pytest.approx(expected_value)


@pytest.mark.parametrize(
    'points',
    (
        (),
        ((0.0, 0.0),),
        ((0.0, 0.0), (0.0, 1.0)),
        ((0.0, 0.0), (float('nan'), 1.0)),
    ),
)
def test_uel2c_rejects_malformed_source_curves(
        points: tuple[tuple[float, float], ...],
) -> None:
    """Reject invalid curve sizes, repeated P values and nonfinite data.

    :param points: Malformed P-Q table data.
    :return: None.
    """
    with pytest.raises(ValueError):
        build_uel2c_template(VarFactory(), curve_points=points)
