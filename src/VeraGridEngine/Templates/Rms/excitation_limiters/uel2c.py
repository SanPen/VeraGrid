# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Maintainable international-standard module for 'Uel2c'.

This is the runtime implementation shipped by VeraGrid.
It exposes the imported public interface, explicit symbolic equations, and
"""

from __future__ import annotations

import math
from enum import Enum

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Utils.Symbolic.block import Block
import VeraGridEngine.Utils.Symbolic.symbolic as sym
from VeraGridEngine.enumerations import DeviceType
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.Utils.Symbolic.symbolic import Expr
from VeraGridEngine.Utils.Symbolic.symbolic import Const


class Uel2cThirdQuadrantMode(Enum):
    """Select how UEL2C reflects or extends the P-Q characteristic."""

    MIRROR = 0
    LINEAR_EXTRAPOLATION = 1


class Uel2cGainReductionMode(Enum):
    """Select fixed KFIX or filtered KADJ gain reduction."""

    FIXED = 1
    ADJUSTABLE = 0


class Uel2cParameters:
    """Store the PSS/E UEL2C continuous parameters and voltage exponents."""

    __slots__ = (
        'k1', 'k2', 'tuv', 'tup', 'tuq', 'kui', 'kul', 'vuimax', 'vuimin',
        'kuf', 'kfb', 'tul', 'tu1', 'tu2', 'tu3', 'tu4', 'vulmax', 'vulmin',
        'vbias', 'kfix', 'tadj', 'tqref', 'vuelmax2', 'vuelmin2', 'vuelmax1',
        'vuelmin1', 'xq',
    )

    def __init__(
            self,
            k1: int = 1,
            k2: int = 1,
            tuv: float = .02,
            tup: float = .02,
            tuq: float = .02,
            kui: float = 1.,
            kul: float = 1.,
            vuimax: float = 1.,
            vuimin: float = -1.,
            kuf: float = 0.,
            kfb: float = 0.,
            tul: float = 1.,
            tu1: float = 1.,
            tu2: float = 1.,
            tu3: float = 1.,
            tu4: float = 1.,
            vulmax: float = 1.,
            vulmin: float = -1.,
            vbias: float = 0.,
            kfix: float = 1.,
            tadj: float = 1.,
            tqref: float = 1.,
            vuelmax2: float = 1.,
            vuelmin2: float = -1.,
            vuelmax1: float = 1.,
            vuelmin1: float = -1.,
            xq: float = 1.,
    ) -> None:
        """Store sourced UEL2C constants on their documented per-unit bases.

        :param k1: Active-power voltage-normalization exponent.
        :param k2: Reactive-power voltage-scaling exponent.
        :param tuv: Terminal-voltage filter time, seconds.
        :param tup: Active-power filter time, seconds.
        :param tuq: Reactive-power filter time, seconds.
        :param kui: UEL integrator gain.
        :param kul: UEL proportional gain.
        :param vuimax: Integrator upper bound.
        :param vuimin: Integrator lower bound.
        :param kuf: Exciter stabilizer feedback gain.
        :param kfb: VFB feedback gain.
        :param tul: VFB lag time, seconds.
        :param tu1: First lead time, seconds.
        :param tu2: First lag time, seconds.
        :param tu3: Second lead time, seconds.
        :param tu4: Second lag time, seconds.
        :param vulmax: Final UEL output upper bound.
        :param vulmin: Final UEL output lower bound.
        :param vbias: Voltage-bias threshold.
        :param kfix: Fixed gain-reduction factor.
        :param tadj: Adjustable gain-reduction filter time, seconds.
        :param tqref: Reactive-power reference filter time, seconds.
        :param vuelmax2: First lead-lag upper bound.
        :param vuelmin2: First lead-lag lower bound.
        :param vuelmax1: Second lead-lag upper bound.
        :param vuelmin1: Second lead-lag lower bound.
        :param xq: Synchronous-generator q-axis reactance, per unit.
        :return: None.
        """
        self.k1: int = k1
        self.k2: int = k2
        self.tuv: float = tuv
        self.tup: float = tup
        self.tuq: float = tuq
        self.kui: float = kui
        self.kul: float = kul
        self.vuimax: float = vuimax
        self.vuimin: float = vuimin
        self.kuf: float = kuf
        self.kfb: float = kfb
        self.tul: float = tul
        self.tu1: float = tu1
        self.tu2: float = tu2
        self.tu3: float = tu3
        self.tu4: float = tu4
        self.vulmax: float = vulmax
        self.vulmin: float = vulmin
        self.vbias: float = vbias
        self.kfix: float = kfix
        self.tadj: float = tadj
        self.tqref: float = tqref
        self.vuelmax2: float = vuelmax2
        self.vuelmin2: float = vuelmin2
        self.vuelmax1: float = vuelmax1
        self.vuelmin1: float = vuelmin1
        self.xq: float = xq


def _build_source_curve_expression(
        vf: VarFactory,
        input_power: Expr,
        points: tuple[tuple[float, float], ...],
        third_quadrant_mode: Uel2cThirdQuadrantMode,
) -> Expr:
    """Build the source-defined piecewise-linear P-Q limiter characteristic.

    The selected third-quadrant behavior either reflects the table about the
    reactive-power axis or linearly extrapolates its first segment. The final
    segment extrapolates linearly, matching the source table configuration.
    Interior slope changes occur at each supplied active-power point.

    :param vf: Factory that owns the symbolic constants.
    :param input_power: Filtered voltage-normalized active power.
    :param points: Two to eleven ordered ``(P, Q)`` characteristic points.
    :param third_quadrant_mode: Source ICON selection for negative active power.
    :return: Symbolic reactive-power limit for the supplied P value.
    :raises ValueError: The source curve is short, nonfinite, or unordered.
    """
    if len(points) < 2 or len(points) > 11:
        raise ValueError('UEL2C curve requires two to eleven active points')
    elif not isinstance(third_quadrant_mode, Uel2cThirdQuadrantMode):
        raise ValueError('UEL2C third-quadrant mode is invalid')
    else:
        pass
    for point in points:
        if not math.isfinite(point[0]) or not math.isfinite(point[1]):
            raise ValueError('UEL2C curve points must be finite')
        else:
            pass
    for index in range(1, len(points)):
        if points[index][0] <= points[index - 1][0]:
            raise ValueError('UEL2C active-power curve points must increase')
        else:
            pass
    table_power: Expr
    if third_quadrant_mode is Uel2cThirdQuadrantMode.MIRROR:
        table_power = sym.abs(input_power)
    else:
        table_power = input_power
    first_slope: float = (points[1][1] - points[0][1]) / (points[1][0] - points[0][0])
    expression: Expr = (
        vf.add_const(value=points[0][1])
        + vf.add_const(value=first_slope)
        * (table_power - vf.add_const(value=points[0][0]))
    )
    previous_slope: float = first_slope
    for index in range(1, len(points) - 1):
        next_slope: float = (
            (points[index + 1][1] - points[index][1])
            / (points[index + 1][0] - points[index][0])
        )
        expression = expression + vf.add_const(value=next_slope - previous_slope) * sym.max(
            table_power - vf.add_const(value=points[index][0]),
            vf.add_const(value=0.0),
        )
        previous_slope = next_slope
    return expression


def build_uel2c_template(
        vf: VarFactory,
        name: str | None = None,
        curve_points: tuple[tuple[float, float], ...] | None = None,
        third_quadrant_mode: Uel2cThirdQuadrantMode = Uel2cThirdQuadrantMode.LINEAR_EXTRAPOLATION,
        gain_reduction_mode: Uel2cGainReductionMode = Uel2cGainReductionMode.ADJUSTABLE,
        parameters: Uel2cParameters | None = None,
        output_limits: tuple[float, float] | None = None,
) -> RmsModelTemplate:
    """
    Return the canonical template rewritten in explicit Block(...) form.

    This helper exists for human auditability and follows the same broad
    construction style used by the handwritten EMT/RMS templates: variables
    are declared through the VarFactory first, then the explicit Block(...)
    is assembled from state, algebraic, initialization, and event sections.

    :param vf: Variable factory used to allocate the symbolic variables.
    :type vf: VarFactory
    :param name: Optional runtime template name.
    :param curve_points: Optional PSS/E P-Q characteristic points. When
        supplied, the source curve replaces the catalogue example curve.
    :param third_quadrant_mode: PSS/E ICON selection for negative active power.
    :param gain_reduction_mode: PSS/E ICON selection between KFIX and KADJ.
    :param parameters: Optional PSS/E UEL2C parameter values.
    :param output_limits: Optional override for the ordered VULMIN/VULMAX bounds.
    :type name: str | None
    :return: Materialized result produced by this builder.
    :rtype: RmsModelTemplate
"""
    template_name: str
    if name is None:
        template_name: str = 'Uel2c'
    else:
        template_name: str = name

    templ: RmsModelTemplate = RmsModelTemplate()
    templ.tpe = DeviceType.GeneratorDevice
    templ.name = template_name
    if not isinstance(third_quadrant_mode, Uel2cThirdQuadrantMode):
        raise ValueError('UEL2C third-quadrant mode is invalid')
    elif not isinstance(gain_reduction_mode, Uel2cGainReductionMode):
        raise ValueError('UEL2C gain-reduction mode is invalid')
    else:
        pass
    selected_output_limits: tuple[float, float]
    if output_limits is not None:
        selected_output_limits = output_limits
    elif parameters is not None:
        selected_output_limits = (parameters.vulmin, parameters.vulmax)
    else:
        selected_output_limits = (-1.0, 1.0)

    # ______________________________________________________________________________________
    #                                    variables
    # ______________________________________________________________________________________

    # State variables
    uel_firstOrder_y_Uel2c: Var = vf.add_var(name='uel.firstOrder.y_Uel2c')
    uel_firstOrder3_y_Uel2c: Var = vf.add_var(name='uel.firstOrder3.y_Uel2c')
    uel_limitedFirstOrder_I_y_Uel2c: Var = vf.add_var(name='uel.limitedFirstOrder.I.y_Uel2c')
    uel_limitedLeadLag_firstOrder_y_Uel2c: Var = vf.add_var(name='uel.limitedLeadLag.firstOrder.y_Uel2c')
    uel_limitedLeadLag1_firstOrder_y_Uel2c: Var = vf.add_var(name='uel.limitedLeadLag1.firstOrder.y_Uel2c')
    uel_limitedPI_integrator_y_Uel2c: Var = vf.add_var(name='uel.limitedPI.integrator.y_Uel2c')
    uel_firstOrder4_y_Uel2c: Var = vf.add_var(name='uel.firstOrder4.y_Uel2c')
    uel_firstOrder1_y_Uel2c: Var = vf.add_var(name='uel.firstOrder1.y_Uel2c')
    uel_firstOrder2_y_Uel2c: Var = vf.add_var(name='uel.firstOrder2.y_Uel2c')

    # Algebraic variables
    uel_limitedFirstOrder_Gk_y_Uel2c: Var = vf.add_var(name='uel.limitedFirstOrder.Gk.y_Uel2c')
    uel_multiSwitch1_expr_2_Uel2c: Var = vf.add_var(name='uel.multiSwitch1.expr[2]_Uel2c')
    uel_multiSwitch1_u_1_Uel2c: Var = vf.add_var(name='uel.multiSwitch1.u[1]_Uel2c')
    uel_multiSwitch1_u_2_Uel2c: Var = vf.add_var(name='uel.multiSwitch1.u[2]_Uel2c')
    uel_multiSwitch1_firstActiveIndex_Uel2c: Var = vf.add_var(name='uel.multiSwitch1.firstActiveIndex_Uel2c')
    uel_add3_y_Uel2c: Var = vf.add_var(name='uel.add3.y_Uel2c')
    uel_limitedFirstOrder_y_Uel2c: Var = vf.add_var(name='uel.limitedFirstOrder.y_Uel2c')
    uel_limitedFirstOrder_feedback_y_Uel2c: Var = vf.add_var(name='uel.limitedFirstOrder.feedback.y_Uel2c')
    uel_limitedFirstOrder_G_y_Uel2c: Var = vf.add_var(name='uel.limitedFirstOrder.G.y_Uel2c')
    uel_limitedFirstOrder_I_u_Uel2c: Var = vf.add_var(name='uel.limitedFirstOrder.I.u_Uel2c')
    uel_switch_y_Uel2c: Var = vf.add_var(name='uel.switch.y_Uel2c')
    uel_product2_y_Uel2c: Var = vf.add_var(name='uel.product2.y_Uel2c')
    uel_limitedPI_add_y_Uel2c: Var = vf.add_var(name='uel.limitedPI.add.y_Uel2c')
    uel_limitedPI_y_Uel2c: Var = vf.add_var(name='uel.limitedPI.y_Uel2c')
    uel_add_y_Uel2c: Var = vf.add_var(name='uel.add.y_Uel2c')
    uel_limitedLeadLag_feedback_y_Uel2c: Var = vf.add_var(name='uel.limitedLeadLag.feedback.y_Uel2c')
    uel_limitedLeadLag_gain_y_Uel2c: Var = vf.add_var(name='uel.limitedLeadLag.gain.y_Uel2c')
    uel_limitedLeadLag_y_Uel2c: Var = vf.add_var(name='uel.limitedLeadLag.y_Uel2c')
    uel_limitedLeadLag1_feedback_y_Uel2c: Var = vf.add_var(name='uel.limitedLeadLag1.feedback.y_Uel2c')
    uel_limitedLeadLag1_gain_y_Uel2c: Var = vf.add_var(name='uel.limitedLeadLag1.gain.y_Uel2c')
    uel_UUelPu_Uel2c: Var = vf.add_var(name='uel.UUelPu_Uel2c')
    uel_limitedPI_hysteresisMax_y_Uel2c: Var = vf.add_var(name='uel.limitedPI.hysteresisMax.y_Uel2c')
    uel_limitedPI_hysteresisMin_y_Uel2c: Var = vf.add_var(name='uel.limitedPI.hysteresisMin.y_Uel2c')
    uel_limitedPI_switch1_u2_Uel2c: Var = vf.add_var(name='uel.limitedPI.switch1.u2_Uel2c')
    uel_limitedPI_switch1_y_Uel2c: Var = vf.add_var(name='uel.limitedPI.switch1.y_Uel2c')
    uel_multiSwitch1_expr_1_Uel2c: Var = vf.add_var(name='uel.multiSwitch1.expr[1]_Uel2c')
    uel_multiSwitch1_y_Uel2c: Var = vf.add_var(name='uel.multiSwitch1.y_Uel2c')
    uel_power_y_Uel2c: Var = vf.add_var(name='uel.power.y_Uel2c')
    uel_power1_y_Uel2c: Var = vf.add_var(name='uel.power1.y_Uel2c')
    uel_division_y_Uel2c: Var = vf.add_var(name='uel.division.y_Uel2c')
    uel_combiTable1Ds_y_1_Uel2c: Var = vf.add_var(name='uel.combiTable1Ds.y[1]_Uel2c')
    uel_product1_y_Uel2c: Var = vf.add_var(name='uel.product1.y_Uel2c')
    uel_kAdj_Uel2c: Var = vf.add_var(name='uel.kAdj_Uel2c')
    uel_multiSwitch1_expr_Uel2c: Var = vf.add_var(name='uel.multiSwitch1.expr_Uel2c')
    uel_PGenPu_Uel2c: Var = vf.add_var(name='uel.PGenPu_Uel2c')
    uel_QGenPu_Uel2c: Var = vf.add_var(name='uel.QGenPu_Uel2c')
    uel_VFbPu_Uel2c: Var = vf.add_var(name='uel.VFbPu_Uel2c')
    uel_VfPu_Uel2c: Var = vf.add_var(name='uel.VfPu_Uel2c')
    uel_utPu_im_Uel2c: Var = vf.add_var(name='uel.utPu.im_Uel2c')
    uel_utPu_re_Uel2c: Var = vf.add_var(name='uel.utPu.re_Uel2c')
    uel_limitedFirstOrder_lim_simplifiedExpr_Uel2c: Var = vf.add_var(name='uel.limitedFirstOrder.lim.simplifiedExpr_Uel2c')
    uel_limitedFirstOrder_I_local_reset_Uel2c: Var = vf.add_var(name='uel.limitedFirstOrder.I.local_reset_Uel2c')
    uel_limitedFirstOrder_I_local_set_Uel2c: Var = vf.add_var(name='uel.limitedFirstOrder.I.local_set_Uel2c')
    uel_limitedPI_limiter1_simplifiedExpr_Uel2c: Var = vf.add_var(name='uel.limitedPI.limiter1.simplifiedExpr_Uel2c')
    uel_limitedPI_integrator_local_reset_Uel2c: Var = vf.add_var(name='uel.limitedPI.integrator.local_reset_Uel2c')
    uel_limitedPI_integrator_local_set_Uel2c: Var = vf.add_var(name='uel.limitedPI.integrator.local_set_Uel2c')
    uel_limitedLeadLag_limiter_simplifiedExpr_Uel2c: Var = vf.add_var(name='uel.limitedLeadLag.limiter.simplifiedExpr_Uel2c')
    uel_limitedLeadLag1_limiter_simplifiedExpr_Uel2c: Var = vf.add_var(name='uel.limitedLeadLag1.limiter.simplifiedExpr_Uel2c')
    START_uel_firstOrder_y_Uel2c: Var = vf.add_var(name='$START.uel.firstOrder.y_Uel2c')
    START_uel_firstOrder1_y_Uel2c: Var = vf.add_var(name='$START.uel.firstOrder1.y_Uel2c')
    START_uel_firstOrder2_y_Uel2c: Var = vf.add_var(name='$START.uel.firstOrder2.y_Uel2c')
    START_uel_firstOrder3_y_Uel2c: Var = vf.add_var(name='$START.uel.firstOrder3.y_Uel2c')
    START_uel_limitedLeadLag_firstOrder_y_Uel2c: Var = vf.add_var(name='$START.uel.limitedLeadLag.firstOrder.y_Uel2c')
    START_uel_limitedLeadLag1_firstOrder_y_Uel2c: Var = vf.add_var(name='$START.uel.limitedLeadLag1.firstOrder.y_Uel2c')
    START_uel_firstOrder4_y_Uel2c: Var = vf.add_var(name='$START.uel.firstOrder4.y_Uel2c')
    PRE_uel_limitedPI_hysteresisMin_y_Uel2c: Var = vf.add_var(name='$PRE.uel.limitedPI.hysteresisMin.y_Uel2c')
    PRE_uel_limitedPI_hysteresisMax_y_Uel2c: Var = vf.add_var(name='$PRE.uel.limitedPI.hysteresisMax.y_Uel2c')
    uel_gain_y_Uel2c: Var = vf.add_var(name='uel.gain.y_Uel2c')
    uel_complexToPolar_phi_Uel2c: Var = vf.add_var(name='uel.complexToPolar.phi_Uel2c')
    uel_UPu_Uel2c: Var = vf.add_var(name='uel.UPu_Uel2c')
    PRE_uel_multiSwitch1_u_2_Uel2c: Var = vf.add_var(name='$PRE.uel.multiSwitch1.u[2]_Uel2c')
    PRE_uel_multiSwitch1_u_1_Uel2c: Var = vf.add_var(name='$PRE.uel.multiSwitch1.u[1]_Uel2c')

    # Differential variables
    d_uel_firstOrder_y_Uel2c: Var = vf.add_diff_var(name='d_uel.firstOrder.y_Uel2c', base_var=uel_firstOrder_y_Uel2c)
    d_uel_firstOrder3_y_Uel2c: Var = vf.add_diff_var(name='d_uel.firstOrder3.y_Uel2c', base_var=uel_firstOrder3_y_Uel2c)
    d_uel_limitedFirstOrder_I_y_Uel2c: Var = vf.add_diff_var(name='d_uel.limitedFirstOrder.I.y_Uel2c', base_var=uel_limitedFirstOrder_I_y_Uel2c)
    d_uel_limitedLeadLag_firstOrder_y_Uel2c: Var = vf.add_diff_var(name='d_uel.limitedLeadLag.firstOrder.y_Uel2c', base_var=uel_limitedLeadLag_firstOrder_y_Uel2c)
    d_uel_limitedLeadLag1_firstOrder_y_Uel2c: Var = vf.add_diff_var(name='d_uel.limitedLeadLag1.firstOrder.y_Uel2c', base_var=uel_limitedLeadLag1_firstOrder_y_Uel2c)
    d_uel_limitedPI_integrator_y_Uel2c: Var = vf.add_diff_var(name='d_uel.limitedPI.integrator.y_Uel2c', base_var=uel_limitedPI_integrator_y_Uel2c)
    d_uel_firstOrder4_y_Uel2c: Var = vf.add_diff_var(name='d_uel.firstOrder4.y_Uel2c', base_var=uel_firstOrder4_y_Uel2c)
    d_uel_firstOrder1_y_Uel2c: Var = vf.add_diff_var(name='d_uel.firstOrder1.y_Uel2c', base_var=uel_firstOrder1_y_Uel2c)
    d_uel_firstOrder2_y_Uel2c: Var = vf.add_diff_var(name='d_uel.firstOrder2.y_Uel2c', base_var=uel_firstOrder2_y_Uel2c)

    # ______________________________________________________________________________________
    #                                    parameters
    # ______________________________________________________________________________________

    # Runtime parameters and event variables
    uel_firstOrder_T_Uel2c: Var = vf.add_var(name='uel.firstOrder.T_Uel2c')
    uel_firstOrder_k_Uel2c: Var = vf.add_var(name='uel.firstOrder.k_Uel2c')
    uel_firstOrder3_T_Uel2c: Var = vf.add_var(name='uel.firstOrder3.T_Uel2c')
    uel_limitedFirstOrder_I_k_Uel2c: Var = vf.add_var(name='uel.limitedFirstOrder.I.k_Uel2c')
    uel_limitedLeadLag_firstOrder_k_Uel2c: Var = vf.add_var(name='uel.limitedLeadLag.firstOrder.k_Uel2c')
    uel_limitedLeadLag_firstOrder_T_Uel2c: Var = vf.add_var(name='uel.limitedLeadLag.firstOrder.T_Uel2c')
    uel_limitedLeadLag1_firstOrder_k_Uel2c: Var = vf.add_var(name='uel.limitedLeadLag1.firstOrder.k_Uel2c')
    uel_limitedLeadLag1_firstOrder_T_Uel2c: Var = vf.add_var(name='uel.limitedLeadLag1.firstOrder.T_Uel2c')
    uel_limitedPI_integrator_k_Uel2c: Var = vf.add_var(name='uel.limitedPI.integrator.k_Uel2c')
    uel_firstOrder4_T_Uel2c: Var = vf.add_var(name='uel.firstOrder4.T_Uel2c')
    uel_firstOrder4_k_Uel2c: Var = vf.add_var(name='uel.firstOrder4.k_Uel2c')
    uel_firstOrder1_k_Uel2c: Var = vf.add_var(name='uel.firstOrder1.k_Uel2c')
    uel_firstOrder1_T_Uel2c: Var = vf.add_var(name='uel.firstOrder1.T_Uel2c')
    uel_firstOrder2_T_Uel2c: Var = vf.add_var(name='uel.firstOrder2.T_Uel2c')
    uel_firstOrder2_k_Uel2c: Var = vf.add_var(name='uel.firstOrder2.k_Uel2c')
    uel_QRef0Pu_Uel2c: Var = vf.add_var(name='uel.QRef0Pu_Uel2c')
    uel_limitedFirstOrder_Gk_k_Uel2c: Var = vf.add_var(name='uel.limitedFirstOrder.Gk.k_Uel2c')
    uel_VBiasPu_Uel2c: Var = vf.add_var(name='uel.VBiasPu_Uel2c')
    uel_greaterThreshold_threshold_Uel2c: Var = vf.add_var(name='uel.greaterThreshold.threshold_Uel2c')
    uel_lessEqualThreshold_threshold_Uel2c: Var = vf.add_var(name='uel.lessEqualThreshold.threshold_Uel2c')
    uel_add3_k1_Uel2c: Var = vf.add_var(name='uel.add3.k1_Uel2c')
    uel_add3_k3_Uel2c: Var = vf.add_var(name='uel.add3.k3_Uel2c')
    uel_limitedFirstOrder_lim_uMax_Uel2c: Var = vf.add_var(name='uel.limitedFirstOrder.lim.uMax_Uel2c')
    uel_limitedFirstOrder_lim_uMin_Uel2c: Var = vf.add_var(name='uel.limitedFirstOrder.lim.uMin_Uel2c')
    uel_limitedFirstOrder_G_k_Uel2c: Var = vf.add_var(name='uel.limitedFirstOrder.G.k_Uel2c')
    uel_const_k_Uel2c: Var = vf.add_var(name='uel.const.k_Uel2c')
    uel_booleanConstant_k_Uel2c: Var = vf.add_var(name='uel.booleanConstant.k_Uel2c')
    uel_limitedPI_add_k2_Uel2c: Var = vf.add_var(name='uel.limitedPI.add.k2_Uel2c')
    uel_limitedPI_add_k1_Uel2c: Var = vf.add_var(name='uel.limitedPI.add.k1_Uel2c')
    uel_limitedPI_limiter1_uMin_Uel2c: Var = vf.add_var(name='uel.limitedPI.limiter1.uMin_Uel2c')
    uel_limitedPI_limiter1_uMax_Uel2c: Var = vf.add_var(name='uel.limitedPI.limiter1.uMax_Uel2c')
    uel_add_k2_Uel2c: Var = vf.add_var(name='uel.add.k2_Uel2c')
    uel_add_k1_Uel2c: Var = vf.add_var(name='uel.add.k1_Uel2c')
    uel_limitedLeadLag_gain_k_Uel2c: Var = vf.add_var(name='uel.limitedLeadLag.gain.k_Uel2c')
    uel_limitedLeadLag_limiter_uMax_Uel2c: Var = vf.add_var(name='uel.limitedLeadLag.limiter.uMax_Uel2c')
    uel_limitedLeadLag_limiter_uMin_Uel2c: Var = vf.add_var(name='uel.limitedLeadLag.limiter.uMin_Uel2c')
    uel_limitedLeadLag1_gain_k_Uel2c: Var = vf.add_var(name='uel.limitedLeadLag1.gain.k_Uel2c')
    uel_limitedLeadLag1_limiter_uMax_Uel2c: Var = vf.add_var(name='uel.limitedLeadLag1.limiter.uMax_Uel2c')
    uel_limitedLeadLag1_limiter_uMin_Uel2c: Var = vf.add_var(name='uel.limitedLeadLag1.limiter.uMin_Uel2c')
    uel_limitedPI_hysteresisMax_uHigh_Uel2c: Var = vf.add_var(name='uel.limitedPI.hysteresisMax.uHigh_Uel2c')
    uel_limitedPI_hysteresisMax_uLow_Uel2c: Var = vf.add_var(name='uel.limitedPI.hysteresisMax.uLow_Uel2c')
    uel_limitedPI_hysteresisMin_uHigh_Uel2c: Var = vf.add_var(name='uel.limitedPI.hysteresisMin.uHigh_Uel2c')
    uel_limitedPI_hysteresisMin_uLow_Uel2c: Var = vf.add_var(name='uel.limitedPI.hysteresisMin.uLow_Uel2c')
    uel_limitedPI_const_k_Uel2c: Var = vf.add_var(name='uel.limitedPI.const.k_Uel2c')
    uel_multiSwitch1_y_default_Uel2c: Var = vf.add_var(name='uel.multiSwitch1.y_default_Uel2c')
    uel_power_N_Uel2c: Var = vf.add_var(name='uel.power.N_Uel2c')
    uel_power1_N_Uel2c: Var = vf.add_var(name='uel.power1.N_Uel2c')
    uel_limitedFirstOrder_I_y_start_Uel2c: Var = vf.add_var(name='uel.limitedFirstOrder.I.y_start_Uel2c')
    uel_limitedPI_integrator_y_start_Uel2c: Var = vf.add_var(name='uel.limitedPI.integrator.y_start_Uel2c')
    uel_limitedLeadLag1_Y0_Uel2c: Var = vf.add_var(name='uel.limitedLeadLag1.Y0_Uel2c')
    uel_limitedFirstOrder_Y0_Uel2c: Var = vf.add_var(name='uel.limitedFirstOrder.Y0_Uel2c')
    uel_limitedLeadLag_Y0_Uel2c: Var = vf.add_var(name='uel.limitedLeadLag.Y0_Uel2c')
    uel_limitedPI_Y0_Uel2c: Var = vf.add_var(name='uel.limitedPI.Y0_Uel2c')
    uel_limitedPI_hysteresisMin_pre_y_start_Uel2c: Var = vf.add_var(name='uel.limitedPI.hysteresisMin.pre_y_start_Uel2c')
    uel_limitedPI_hysteresisMax_pre_y_start_Uel2c: Var = vf.add_var(name='uel.limitedPI.hysteresisMax.pre_y_start_Uel2c')
    uel_K1_Uel2c: Var = vf.add_var(name='uel.K1_Uel2c')
    uel_K2_Uel2c: Var = vf.add_var(name='uel.K2_Uel2c')
    uel_KAdj0_Uel2c: Var = vf.add_var(name='uel.KAdj0_Uel2c')
    uel_U0Pu_Uel2c: Var = vf.add_var(name='uel.U0Pu_Uel2c')
    uel_PGen0Pu_Uel2c: Var = vf.add_var(name='uel.PGen0Pu_Uel2c')
    uel_XqPu_Uel2c: Var = vf.add_var(name='uel.XqPu_Uel2c')
    uel_QGen0Pu_Uel2c: Var = vf.add_var(name='uel.QGen0Pu_Uel2c')
    uel_KFb_Uel2c: Var = vf.add_var(name='uel.KFb_Uel2c')
    uel_KFix_Uel2c: Var = vf.add_var(name='uel.KFix_Uel2c')
    uel_Kuf_Uel2c: Var = vf.add_var(name='uel.Kuf_Uel2c')
    uel_Kui_Uel2c: Var = vf.add_var(name='uel.Kui_Uel2c')
    uel_Kul_Uel2c: Var = vf.add_var(name='uel.Kul_Uel2c')
    uel_UsRef0Pu_Uel2c: Var = vf.add_var(name='uel.UsRef0Pu_Uel2c')
    uel_VBias0Pu_Uel2c: Var = vf.add_var(name='uel.VBias0Pu_Uel2c')
    uel_VUel1MaxPu_Uel2c: Var = vf.add_var(name='uel.VUel1MaxPu_Uel2c')
    uel_VUel1MinPu_Uel2c: Var = vf.add_var(name='uel.VUel1MinPu_Uel2c')
    uel_VUel2MaxPu_Uel2c: Var = vf.add_var(name='uel.VUel2MaxPu_Uel2c')
    uel_VUel2MinPu_Uel2c: Var = vf.add_var(name='uel.VUel2MinPu_Uel2c')
    uel_VUiMaxPu_Uel2c: Var = vf.add_var(name='uel.VUiMaxPu_Uel2c')
    uel_VUiMinPu_Uel2c: Var = vf.add_var(name='uel.VUiMinPu_Uel2c')
    uel_VULMaxPu_Uel2c: Var = vf.add_var(name='uel.VULMaxPu_Uel2c')
    uel_VULMinPu_Uel2c: Var = vf.add_var(name='uel.VULMinPu_Uel2c')
    uel_add3_k2_Uel2c: Var = vf.add_var(name='uel.add3.k2_Uel2c')
    uel_combiTable1Ds_u_max_Uel2c: Var = vf.add_var(name='uel.combiTable1Ds.u_max_Uel2c')
    uel_combiTable1Ds_u_min_Uel2c: Var = vf.add_var(name='uel.combiTable1Ds.u_min_Uel2c')
    uel_tUV_Uel2c: Var = vf.add_var(name='uel.tUV_Uel2c')
    uel_firstOrder_y_start_Uel2c: Var = vf.add_var(name='uel.firstOrder.y_start_Uel2c')
    uel_tUP_Uel2c: Var = vf.add_var(name='uel.tUP_Uel2c')
    uel_firstOrder1_y_start_Uel2c: Var = vf.add_var(name='uel.firstOrder1.y_start_Uel2c')
    uel_tQRef_Uel2c: Var = vf.add_var(name='uel.tQRef_Uel2c')
    uel_firstOrder2_y_start_Uel2c: Var = vf.add_var(name='uel.firstOrder2.y_start_Uel2c')
    uel_tUQ_Uel2c: Var = vf.add_var(name='uel.tUQ_Uel2c')
    uel_firstOrder3_k_Uel2c: Var = vf.add_var(name='uel.firstOrder3.k_Uel2c')
    uel_firstOrder3_y_start_Uel2c: Var = vf.add_var(name='uel.firstOrder3.y_start_Uel2c')
    uel_tUl_Uel2c: Var = vf.add_var(name='uel.tUl_Uel2c')
    uel_firstOrder4_y_start_Uel2c: Var = vf.add_var(name='uel.firstOrder4.y_start_Uel2c')
    uel_gain_k_Uel2c: Var = vf.add_var(name='uel.gain.k_Uel2c')
    uel_limitedFirstOrder_tFilter_Uel2c: Var = vf.add_var(name='uel.limitedFirstOrder.tFilter_Uel2c')
    uel_limitedFirstOrder_K_Uel2c: Var = vf.add_var(name='uel.limitedFirstOrder.K_Uel2c')
    uel_limitedFirstOrder_YMax_Uel2c: Var = vf.add_var(name='uel.limitedFirstOrder.YMax_Uel2c')
    uel_limitedFirstOrder_YMin_Uel2c: Var = vf.add_var(name='uel.limitedFirstOrder.YMin_Uel2c')
    uel_tAdj_Uel2c: Var = vf.add_var(name='uel.tAdj_Uel2c')
    uel_limitedLeadLag_K_Uel2c: Var = vf.add_var(name='uel.limitedLeadLag.K_Uel2c')
    uel_limitedLeadLag_YMax_Uel2c: Var = vf.add_var(name='uel.limitedLeadLag.YMax_Uel2c')
    uel_limitedLeadLag_YMin_Uel2c: Var = vf.add_var(name='uel.limitedLeadLag.YMin_Uel2c')
    uel_limitedLeadLag_t1_Uel2c: Var = vf.add_var(name='uel.limitedLeadLag.t1_Uel2c')
    uel_limitedLeadLag_t2_Uel2c: Var = vf.add_var(name='uel.limitedLeadLag.t2_Uel2c')
    uel_limitedLeadLag_firstOrder_y_start_Uel2c: Var = vf.add_var(name='uel.limitedLeadLag.firstOrder.y_start_Uel2c')
    uel_tU1_Uel2c: Var = vf.add_var(name='uel.tU1_Uel2c')
    uel_tU2_Uel2c: Var = vf.add_var(name='uel.tU2_Uel2c')
    uel_limitedLeadLag1_K_Uel2c: Var = vf.add_var(name='uel.limitedLeadLag1.K_Uel2c')
    uel_limitedLeadLag1_YMax_Uel2c: Var = vf.add_var(name='uel.limitedLeadLag1.YMax_Uel2c')
    uel_limitedLeadLag1_YMin_Uel2c: Var = vf.add_var(name='uel.limitedLeadLag1.YMin_Uel2c')
    uel_limitedLeadLag1_t1_Uel2c: Var = vf.add_var(name='uel.limitedLeadLag1.t1_Uel2c')
    uel_limitedLeadLag1_t2_Uel2c: Var = vf.add_var(name='uel.limitedLeadLag1.t2_Uel2c')
    uel_limitedLeadLag1_firstOrder_y_start_Uel2c: Var = vf.add_var(name='uel.limitedLeadLag1.firstOrder.y_start_Uel2c')
    uel_tU3_Uel2c: Var = vf.add_var(name='uel.tU3_Uel2c')
    uel_tU4_Uel2c: Var = vf.add_var(name='uel.tU4_Uel2c')
    uel_limitedPI_Ki_Uel2c: Var = vf.add_var(name='uel.limitedPI.Ki_Uel2c')
    uel_limitedPI_Kp_Uel2c: Var = vf.add_var(name='uel.limitedPI.Kp_Uel2c')
    uel_limitedPI_Tol_Uel2c: Var = vf.add_var(name='uel.limitedPI.Tol_Uel2c')
    uel_limitedPI_YMax_Uel2c: Var = vf.add_var(name='uel.limitedPI.YMax_Uel2c')
    uel_limitedPI_YMin_Uel2c: Var = vf.add_var(name='uel.limitedPI.YMin_Uel2c')
    uel_ut0Pu_im_Uel2c: Var = vf.add_var(name='uel.ut0Pu.im_Uel2c')
    uel_ut0Pu_re_Uel2c: Var = vf.add_var(name='uel.ut0Pu.re_Uel2c')
    uel_combiTable1Ds_columns_1_Uel2c: Var = vf.add_var(name='uel.combiTable1Ds.columns[1]_Uel2c')
    uel_combiTable1Ds_extrapolation_Uel2c: Var = vf.add_var(name='uel.combiTable1Ds.extrapolation_Uel2c')
    uel_combiTable1Ds_nout_Uel2c: Var = vf.add_var(name='uel.combiTable1Ds.nout_Uel2c')
    uel_combiTable1Ds_smoothness_Uel2c: Var = vf.add_var(name='uel.combiTable1Ds.smoothness_Uel2c')
    uel_firstOrder_initType_Uel2c: Var = vf.add_var(name='uel.firstOrder.initType_Uel2c')
    uel_firstOrder1_initType_Uel2c: Var = vf.add_var(name='uel.firstOrder1.initType_Uel2c')
    uel_firstOrder2_initType_Uel2c: Var = vf.add_var(name='uel.firstOrder2.initType_Uel2c')
    uel_firstOrder3_initType_Uel2c: Var = vf.add_var(name='uel.firstOrder3.initType_Uel2c')
    uel_firstOrder4_initType_Uel2c: Var = vf.add_var(name='uel.firstOrder4.initType_Uel2c')
    uel_limitedFirstOrder_I_initType_Uel2c: Var = vf.add_var(name='uel.limitedFirstOrder.I.initType_Uel2c')
    uel_limitedFirstOrder_lim_homotopyType_Uel2c: Var = vf.add_var(name='uel.limitedFirstOrder.lim.homotopyType_Uel2c')
    uel_limitedLeadLag_firstOrder_initType_Uel2c: Var = vf.add_var(name='uel.limitedLeadLag.firstOrder.initType_Uel2c')
    uel_limitedLeadLag_limiter_homotopyType_Uel2c: Var = vf.add_var(name='uel.limitedLeadLag.limiter.homotopyType_Uel2c')
    uel_limitedLeadLag1_firstOrder_initType_Uel2c: Var = vf.add_var(name='uel.limitedLeadLag1.firstOrder.initType_Uel2c')
    uel_limitedLeadLag1_limiter_homotopyType_Uel2c: Var = vf.add_var(name='uel.limitedLeadLag1.limiter.homotopyType_Uel2c')
    uel_limitedPI_integrator_initType_Uel2c: Var = vf.add_var(name='uel.limitedPI.integrator.initType_Uel2c')
    uel_limitedPI_limiter1_homotopyType_Uel2c: Var = vf.add_var(name='uel.limitedPI.limiter1.homotopyType_Uel2c')
    uel_multiSwitch1_nu_Uel2c: Var = vf.add_var(name='uel.multiSwitch1.nu_Uel2c')
    uel_multiSwitch1_precision_Uel2c: Var = vf.add_var(name='uel.multiSwitch1.precision_Uel2c')
    uel_Sw1_Uel2c: Var = vf.add_var(name='uel.Sw1_Uel2c')
    uel_combiTable1Ds_tableOnFile_Uel2c: Var = vf.add_var(name='uel.combiTable1Ds.tableOnFile_Uel2c')
    uel_combiTable1Ds_verboseExtrapolation_Uel2c: Var = vf.add_var(name='uel.combiTable1Ds.verboseExtrapolation_Uel2c')
    uel_combiTable1Ds_verboseRead_Uel2c: Var = vf.add_var(name='uel.combiTable1Ds.verboseRead_Uel2c')
    uel_limitedFirstOrder_I_use_reset_Uel2c: Var = vf.add_var(name='uel.limitedFirstOrder.I.use_reset_Uel2c')
    uel_limitedFirstOrder_I_use_set_Uel2c: Var = vf.add_var(name='uel.limitedFirstOrder.I.use_set_Uel2c')
    uel_limitedFirstOrder_lim_limitsAtInit_Uel2c: Var = vf.add_var(name='uel.limitedFirstOrder.lim.limitsAtInit_Uel2c')
    uel_limitedFirstOrder_lim_strict_Uel2c: Var = vf.add_var(name='uel.limitedFirstOrder.lim.strict_Uel2c')
    uel_limitedLeadLag_limiter_limitsAtInit_Uel2c: Var = vf.add_var(name='uel.limitedLeadLag.limiter.limitsAtInit_Uel2c')
    uel_limitedLeadLag_limiter_strict_Uel2c: Var = vf.add_var(name='uel.limitedLeadLag.limiter.strict_Uel2c')
    uel_limitedLeadLag1_limiter_limitsAtInit_Uel2c: Var = vf.add_var(name='uel.limitedLeadLag1.limiter.limitsAtInit_Uel2c')
    uel_limitedLeadLag1_limiter_strict_Uel2c: Var = vf.add_var(name='uel.limitedLeadLag1.limiter.strict_Uel2c')
    uel_limitedPI_integrator_use_reset_Uel2c: Var = vf.add_var(name='uel.limitedPI.integrator.use_reset_Uel2c')
    uel_limitedPI_integrator_use_set_Uel2c: Var = vf.add_var(name='uel.limitedPI.integrator.use_set_Uel2c')
    uel_limitedPI_limiter1_limitsAtInit_Uel2c: Var = vf.add_var(name='uel.limitedPI.limiter1.limitsAtInit_Uel2c')
    uel_limitedPI_limiter1_strict_Uel2c: Var = vf.add_var(name='uel.limitedPI.limiter1.strict_Uel2c')
    uel_power_NInteger_Uel2c: Var = vf.add_var(name='uel.power.NInteger_Uel2c')
    uel_power1_NInteger_Uel2c: Var = vf.add_var(name='uel.power1.NInteger_Uel2c')
    uel_FPQTableName_Uel2c: Var = vf.add_var(name='uel.FPQTableName_Uel2c')
    uel_TablesFile_Uel2c: Var = vf.add_var(name='uel.TablesFile_Uel2c')
    uel_combiTable1Ds_fileName_Uel2c: Var = vf.add_var(name='uel.combiTable1Ds.fileName_Uel2c')
    uel_combiTable1Ds_tableName_Uel2c: Var = vf.add_var(name='uel.combiTable1Ds.tableName_Uel2c')
    uel_combiTable1Ds_tableID_Uel2c: Var = vf.add_var(name='uel.combiTable1Ds.tableID_Uel2c')

    event_dict: dict[Var, Expr | Const] = dict({
        uel_K1_Uel2c: vf.add_const(value=1.0),
        uel_K2_Uel2c: vf.add_const(value=1.0),
        uel_KAdj0_Uel2c: ((((uel_U0Pu_Uel2c ** vf.add_const(value=2.0)) / uel_XqPu_Uel2c) + uel_QGen0Pu_Uel2c) / sym.sqrt((((((uel_U0Pu_Uel2c ** vf.add_const(value=2.0)) / uel_XqPu_Uel2c) + uel_QGen0Pu_Uel2c) ** vf.add_const(value=2.0)) + (uel_PGen0Pu_Uel2c ** vf.add_const(value=2.0))))),
        uel_KFb_Uel2c: vf.add_const(value=0.0),
        uel_KFix_Uel2c: vf.add_const(value=1.0),
        uel_Kuf_Uel2c: vf.add_const(value=0.0),
        uel_Kui_Uel2c: vf.add_const(value=1.0),
        uel_Kul_Uel2c: vf.add_const(value=1.0),
        uel_PGen0Pu_Uel2c: vf.add_const(value=0.8),
        uel_QGen0Pu_Uel2c: vf.add_const(value=0.0),
        uel_QRef0Pu_Uel2c: vf.add_const(value=0.0),
        uel_U0Pu_Uel2c: vf.add_const(value=1.0),
        uel_UsRef0Pu_Uel2c: vf.add_const(value=1.0),
        uel_VBias0Pu_Uel2c: vf.add_const(value=0.0),
        uel_VBiasPu_Uel2c: vf.add_const(value=0.0),
        START_uel_firstOrder_y_Uel2c: uel_firstOrder_y_start_Uel2c,
        START_uel_firstOrder1_y_Uel2c: uel_firstOrder1_y_start_Uel2c,
        START_uel_firstOrder2_y_Uel2c: uel_firstOrder2_y_start_Uel2c,
        START_uel_firstOrder3_y_Uel2c: uel_firstOrder3_y_start_Uel2c,
        START_uel_firstOrder4_y_Uel2c: uel_firstOrder4_y_start_Uel2c,
        START_uel_limitedLeadLag_firstOrder_y_Uel2c: uel_limitedLeadLag_firstOrder_y_start_Uel2c,
        START_uel_limitedLeadLag1_firstOrder_y_Uel2c: uel_limitedLeadLag1_firstOrder_y_start_Uel2c,
        uel_VUel1MaxPu_Uel2c: vf.add_const(value=1.0),
        uel_VUel1MinPu_Uel2c: vf.add_const(value=-1.0),
        uel_VUel2MaxPu_Uel2c: vf.add_const(value=1.0),
        uel_VUel2MinPu_Uel2c: vf.add_const(value=-1.0),
        uel_VUiMaxPu_Uel2c: vf.add_const(value=1.0),
        uel_VUiMinPu_Uel2c: vf.add_const(value=-1.0),
        uel_VULMaxPu_Uel2c: vf.add_const(value=1.0),
        uel_VULMinPu_Uel2c: vf.add_const(value=-1.0),
        uel_XqPu_Uel2c: vf.add_const(value=1.0),
        uel_add_k1_Uel2c: vf.add_const(value=1.0),
        uel_add_k2_Uel2c: vf.add_const(value=1.0),
        uel_add3_k1_Uel2c: vf.add_const(value=-1.0),
        uel_add3_k2_Uel2c: vf.add_const(value=-1.0),
        uel_add3_k3_Uel2c: vf.add_const(value=1.0),
        uel_combiTable1Ds_u_max_Uel2c: vf.add_const(value=1.02),
        uel_combiTable1Ds_u_min_Uel2c: vf.add_const(value=0.0),
        uel_const_k_Uel2c: uel_KFix_Uel2c,
        uel_firstOrder_T_Uel2c: uel_tUV_Uel2c,
        uel_firstOrder_k_Uel2c: vf.add_const(value=1.0),
        uel_firstOrder_y_start_Uel2c: uel_U0Pu_Uel2c,
        uel_firstOrder1_T_Uel2c: uel_tUP_Uel2c,
        uel_firstOrder1_k_Uel2c: vf.add_const(value=1.0),
        uel_firstOrder1_y_start_Uel2c: (uel_PGen0Pu_Uel2c / (uel_VBias0Pu_Uel2c ** uel_K1_Uel2c)),
        uel_firstOrder2_T_Uel2c: uel_tQRef_Uel2c,
        uel_firstOrder2_k_Uel2c: vf.add_const(value=1.0),
        uel_firstOrder2_y_start_Uel2c: uel_QRef0Pu_Uel2c,
        uel_firstOrder3_T_Uel2c: uel_tUQ_Uel2c,
        uel_firstOrder3_k_Uel2c: vf.add_const(value=1.0),
        uel_firstOrder3_y_start_Uel2c: uel_QGen0Pu_Uel2c,
        uel_firstOrder4_T_Uel2c: uel_tUl_Uel2c,
        uel_firstOrder4_k_Uel2c: uel_KFb_Uel2c,
        uel_firstOrder4_y_start_Uel2c: (uel_KFb_Uel2c * uel_UsRef0Pu_Uel2c),
        uel_gain_k_Uel2c: uel_Kuf_Uel2c,
        uel_greaterThreshold_threshold_Uel2c: vf.add_const(value=1.0),
        uel_lessEqualThreshold_threshold_Uel2c: vf.add_const(value=1.0),
        uel_limitedFirstOrder_G_k_Uel2c: (vf.add_const(value=1.0) / uel_limitedFirstOrder_tFilter_Uel2c),
        uel_limitedFirstOrder_Gk_k_Uel2c: uel_limitedFirstOrder_K_Uel2c,
        uel_limitedFirstOrder_I_k_Uel2c: vf.add_const(value=1.0),
        uel_limitedFirstOrder_I_y_start_Uel2c: uel_limitedFirstOrder_Y0_Uel2c,
        uel_limitedFirstOrder_K_Uel2c: vf.add_const(value=1.0),
        uel_limitedFirstOrder_Y0_Uel2c: uel_KAdj0_Uel2c,
        uel_limitedFirstOrder_YMax_Uel2c: vf.add_const(value=1.0),
        uel_limitedFirstOrder_YMin_Uel2c: vf.add_const(value=0.1),
        uel_limitedFirstOrder_lim_uMax_Uel2c: uel_limitedFirstOrder_YMax_Uel2c,
        uel_limitedFirstOrder_lim_uMin_Uel2c: uel_limitedFirstOrder_YMin_Uel2c,
        uel_limitedFirstOrder_tFilter_Uel2c: uel_tAdj_Uel2c,
        uel_limitedLeadLag_K_Uel2c: vf.add_const(value=1.0),
        uel_limitedLeadLag_Y0_Uel2c: vf.add_const(value=0.0),
        uel_limitedLeadLag_YMax_Uel2c: uel_VUel2MaxPu_Uel2c,
        uel_limitedLeadLag_YMin_Uel2c: uel_VUel2MinPu_Uel2c,
        uel_limitedLeadLag_firstOrder_T_Uel2c: uel_limitedLeadLag_t1_Uel2c,
        uel_limitedLeadLag_firstOrder_k_Uel2c: ((uel_limitedLeadLag_t1_Uel2c - uel_limitedLeadLag_t2_Uel2c) / (uel_limitedLeadLag_t1_Uel2c * uel_limitedLeadLag_K_Uel2c)),
        uel_limitedLeadLag_firstOrder_y_start_Uel2c: (uel_limitedLeadLag_Y0_Uel2c * ((uel_limitedLeadLag_t1_Uel2c - uel_limitedLeadLag_t2_Uel2c) / (uel_limitedLeadLag_t1_Uel2c * uel_limitedLeadLag_K_Uel2c))),
        uel_limitedLeadLag_gain_k_Uel2c: (uel_limitedLeadLag_K_Uel2c * (uel_limitedLeadLag_t1_Uel2c / uel_limitedLeadLag_t2_Uel2c)),
        uel_limitedLeadLag_limiter_uMax_Uel2c: uel_limitedLeadLag_YMax_Uel2c,
        uel_limitedLeadLag_limiter_uMin_Uel2c: uel_limitedLeadLag_YMin_Uel2c,
        uel_limitedLeadLag_t1_Uel2c: uel_tU1_Uel2c,
        uel_limitedLeadLag_t2_Uel2c: uel_tU2_Uel2c,
        uel_limitedLeadLag1_K_Uel2c: vf.add_const(value=1.0),
        uel_limitedLeadLag1_Y0_Uel2c: vf.add_const(value=0.0),
        uel_limitedLeadLag1_YMax_Uel2c: uel_VUel1MaxPu_Uel2c,
        uel_limitedLeadLag1_YMin_Uel2c: uel_VUel1MinPu_Uel2c,
        uel_limitedLeadLag1_firstOrder_T_Uel2c: uel_limitedLeadLag1_t1_Uel2c,
        uel_limitedLeadLag1_firstOrder_k_Uel2c: ((uel_limitedLeadLag1_t1_Uel2c - uel_limitedLeadLag1_t2_Uel2c) / (uel_limitedLeadLag1_t1_Uel2c * uel_limitedLeadLag1_K_Uel2c)),
        uel_limitedLeadLag1_firstOrder_y_start_Uel2c: (uel_limitedLeadLag1_Y0_Uel2c * ((uel_limitedLeadLag1_t1_Uel2c - uel_limitedLeadLag1_t2_Uel2c) / (uel_limitedLeadLag1_t1_Uel2c * uel_limitedLeadLag1_K_Uel2c))),
        uel_limitedLeadLag1_gain_k_Uel2c: (uel_limitedLeadLag1_K_Uel2c * (uel_limitedLeadLag1_t1_Uel2c / uel_limitedLeadLag1_t2_Uel2c)),
        uel_limitedLeadLag1_limiter_uMax_Uel2c: uel_limitedLeadLag1_YMax_Uel2c,
        uel_limitedLeadLag1_limiter_uMin_Uel2c: uel_limitedLeadLag1_YMin_Uel2c,
        uel_limitedLeadLag1_t1_Uel2c: uel_tU3_Uel2c,
        uel_limitedLeadLag1_t2_Uel2c: uel_tU4_Uel2c,
        uel_limitedPI_Ki_Uel2c: uel_Kui_Uel2c,
        uel_limitedPI_Kp_Uel2c: uel_Kul_Uel2c,
        uel_limitedPI_Tol_Uel2c: vf.add_const(value=1e-05),
        uel_limitedPI_Y0_Uel2c: (-(uel_KFb_Uel2c) * uel_UsRef0Pu_Uel2c),
        uel_limitedPI_YMax_Uel2c: uel_VUiMaxPu_Uel2c,
        uel_limitedPI_YMin_Uel2c: uel_VUiMinPu_Uel2c,
        uel_limitedPI_add_k1_Uel2c: uel_limitedPI_Kp_Uel2c,
        uel_limitedPI_add_k2_Uel2c: vf.add_const(value=1.0),
        uel_limitedPI_const_k_Uel2c: vf.add_const(value=0.0),
        uel_limitedPI_hysteresisMax_uHigh_Uel2c: uel_limitedPI_YMax_Uel2c,
        uel_limitedPI_hysteresisMax_uLow_Uel2c: (uel_limitedPI_YMax_Uel2c + (uel_limitedPI_Tol_Uel2c * (uel_limitedPI_YMin_Uel2c - uel_limitedPI_YMax_Uel2c))),
        uel_limitedPI_hysteresisMin_uHigh_Uel2c: (uel_limitedPI_YMin_Uel2c + (uel_limitedPI_Tol_Uel2c * (uel_limitedPI_YMax_Uel2c - uel_limitedPI_YMin_Uel2c))),
        uel_limitedPI_hysteresisMin_uLow_Uel2c: uel_limitedPI_YMin_Uel2c,
        uel_limitedPI_integrator_k_Uel2c: uel_limitedPI_Ki_Uel2c,
        uel_limitedPI_integrator_y_start_Uel2c: uel_limitedPI_Y0_Uel2c,
        uel_limitedPI_limiter1_uMax_Uel2c: uel_limitedPI_YMax_Uel2c,
        uel_limitedPI_limiter1_uMin_Uel2c: uel_limitedPI_YMin_Uel2c,
        uel_multiSwitch1_y_default_Uel2c: vf.add_const(value=1.0),
        uel_power_N_Uel2c: uel_K2_Uel2c,
        uel_power1_N_Uel2c: uel_K1_Uel2c,
        uel_tAdj_Uel2c: vf.add_const(value=1.0),
        uel_tQRef_Uel2c: vf.add_const(value=1.0),
        uel_tU1_Uel2c: vf.add_const(value=1.0),
        uel_tU2_Uel2c: vf.add_const(value=1.0),
        uel_tU3_Uel2c: vf.add_const(value=1.0),
        uel_tU4_Uel2c: vf.add_const(value=1.0),
        uel_tUP_Uel2c: vf.add_const(value=0.02),
        uel_tUQ_Uel2c: vf.add_const(value=0.02),
        uel_tUV_Uel2c: vf.add_const(value=0.02),
        uel_tUl_Uel2c: vf.add_const(value=1.0),
        uel_ut0Pu_im_Uel2c: vf.add_const(value=0.0),
        uel_ut0Pu_re_Uel2c: vf.add_const(value=1.0),
        uel_combiTable1Ds_columns_1_Uel2c: vf.add_const(value=2.0),
        uel_combiTable1Ds_extrapolation_Uel2c: vf.add_const(value=2.0),
        uel_combiTable1Ds_nout_Uel2c: vf.add_const(value=1.0),
        uel_combiTable1Ds_smoothness_Uel2c: vf.add_const(value=1.0),
        uel_firstOrder_initType_Uel2c: vf.add_const(value=1.0),
        uel_firstOrder1_initType_Uel2c: vf.add_const(value=1.0),
        uel_firstOrder2_initType_Uel2c: vf.add_const(value=1.0),
        uel_firstOrder3_initType_Uel2c: vf.add_const(value=1.0),
        uel_firstOrder4_initType_Uel2c: vf.add_const(value=1.0),
        uel_limitedFirstOrder_I_initType_Uel2c: vf.add_const(value=3.0),
        uel_limitedFirstOrder_lim_homotopyType_Uel2c: vf.add_const(value=1.0),
        uel_limitedLeadLag_firstOrder_initType_Uel2c: vf.add_const(value=1.0),
        uel_limitedLeadLag_limiter_homotopyType_Uel2c: vf.add_const(value=1.0),
        uel_limitedLeadLag1_firstOrder_initType_Uel2c: vf.add_const(value=1.0),
        uel_limitedLeadLag1_limiter_homotopyType_Uel2c: vf.add_const(value=1.0),
        uel_limitedPI_integrator_initType_Uel2c: vf.add_const(value=3.0),
        uel_limitedPI_limiter1_homotopyType_Uel2c: vf.add_const(value=1.0),
        uel_multiSwitch1_nu_Uel2c: vf.add_const(value=2.0),
        uel_multiSwitch1_precision_Uel2c: vf.add_const(value=3.0),
        uel_Sw1_Uel2c: vf.add_const(value=0.0),
        uel_booleanConstant_k_Uel2c: uel_Sw1_Uel2c,
        uel_combiTable1Ds_tableOnFile_Uel2c: vf.add_const(value=1.0),
        uel_combiTable1Ds_verboseExtrapolation_Uel2c: vf.add_const(value=0.0),
        uel_combiTable1Ds_verboseRead_Uel2c: vf.add_const(value=1.0),
        uel_limitedFirstOrder_I_use_reset_Uel2c: vf.add_const(value=0.0),
        uel_limitedFirstOrder_I_use_set_Uel2c: vf.add_const(value=0.0),
        uel_limitedFirstOrder_lim_limitsAtInit_Uel2c: vf.add_const(value=1.0),
        uel_limitedFirstOrder_lim_strict_Uel2c: vf.add_const(value=0.0),
        uel_limitedLeadLag_limiter_limitsAtInit_Uel2c: vf.add_const(value=1.0),
        uel_limitedLeadLag_limiter_strict_Uel2c: vf.add_const(value=0.0),
        uel_limitedLeadLag1_limiter_limitsAtInit_Uel2c: vf.add_const(value=1.0),
        uel_limitedLeadLag1_limiter_strict_Uel2c: vf.add_const(value=0.0),
        uel_limitedPI_hysteresisMax_pre_y_start_Uel2c: vf.add_const(value=0.0),
        uel_limitedPI_hysteresisMin_pre_y_start_Uel2c: vf.add_const(value=1.0),
        uel_limitedPI_integrator_use_reset_Uel2c: vf.add_const(value=0.0),
        uel_limitedPI_integrator_use_set_Uel2c: vf.add_const(value=0.0),
        uel_limitedPI_limiter1_limitsAtInit_Uel2c: vf.add_const(value=1.0),
        uel_limitedPI_limiter1_strict_Uel2c: vf.add_const(value=0.0),
        uel_power_NInteger_Uel2c: vf.add_const(value=1.0),
        uel_power1_NInteger_Uel2c: vf.add_const(value=1.0),
        uel_FPQTableName_Uel2c: vf.add_const(value=0.0),
        uel_TablesFile_Uel2c: vf.add_const(value=0.0),
        uel_combiTable1Ds_fileName_Uel2c: uel_TablesFile_Uel2c,
        uel_combiTable1Ds_tableName_Uel2c: uel_FPQTableName_Uel2c,
        uel_combiTable1Ds_tableID_Uel2c: vf.add_const(value=0.0),
    })

    external_mapping: dict[object, Var] = dict()

    api_obj_mapping: dict[object, Var] = dict()

    templ.block = Block(
        state_eqs=[
            ((uel_firstOrder_k_Uel2c - uel_firstOrder_y_Uel2c) / uel_firstOrder_T_Uel2c),
            ((uel_QGenPu_Uel2c - uel_firstOrder3_y_Uel2c) / uel_firstOrder3_T_Uel2c),
            (uel_limitedFirstOrder_I_k_Uel2c * uel_limitedFirstOrder_I_u_Uel2c),
            (((uel_limitedLeadLag_firstOrder_k_Uel2c * uel_limitedLeadLag_y_Uel2c) - uel_limitedLeadLag_firstOrder_y_Uel2c) / uel_limitedLeadLag_firstOrder_T_Uel2c),
            (((uel_limitedLeadLag1_firstOrder_k_Uel2c * uel_UUelPu_Uel2c) - uel_limitedLeadLag1_firstOrder_y_Uel2c) / uel_limitedLeadLag1_firstOrder_T_Uel2c),
            (uel_limitedPI_integrator_k_Uel2c * uel_limitedPI_switch1_y_Uel2c),
            ((uel_firstOrder4_k_Uel2c - uel_firstOrder4_y_Uel2c) / uel_firstOrder4_T_Uel2c),
            (((uel_firstOrder1_k_Uel2c * uel_division_y_Uel2c) - uel_firstOrder1_y_Uel2c) / uel_firstOrder1_T_Uel2c),
            (((uel_firstOrder2_k_Uel2c * uel_QRef0Pu_Uel2c) - uel_firstOrder2_y_Uel2c) / uel_firstOrder2_T_Uel2c),
        ],
        state_vars=[
            uel_firstOrder_y_Uel2c,
            uel_firstOrder3_y_Uel2c,
            uel_limitedFirstOrder_I_y_Uel2c,
            uel_limitedLeadLag_firstOrder_y_Uel2c,
            uel_limitedLeadLag1_firstOrder_y_Uel2c,
            uel_limitedPI_integrator_y_Uel2c,
            uel_firstOrder4_y_Uel2c,
            uel_firstOrder1_y_Uel2c,
            uel_firstOrder2_y_Uel2c,
        ],
        algebraic_eqs=[
            (uel_limitedFirstOrder_Gk_y_Uel2c - (uel_limitedFirstOrder_Gk_k_Uel2c * uel_kAdj_Uel2c)),
            (uel_kAdj_Uel2c - (((uel_firstOrder_y_Uel2c ** vf.add_const(value=2.0)) / uel_XqPu_Uel2c + uel_QGenPu_Uel2c) / sym.sqrt((((uel_firstOrder_y_Uel2c ** vf.add_const(value=2.0)) / uel_XqPu_Uel2c + uel_QGenPu_Uel2c) ** vf.add_const(value=2.0)) + (uel_PGenPu_Uel2c ** vf.add_const(value=2.0))))),
            (uel_multiSwitch1_expr_2_Uel2c - (uel_firstOrder_y_Uel2c / uel_VBiasPu_Uel2c)),
            (uel_multiSwitch1_u_1_Uel2c - sym.heaviside(((uel_firstOrder_y_Uel2c - uel_greaterThreshold_threshold_Uel2c) - vf.add_const(value=1e-06)))),
            (uel_multiSwitch1_u_2_Uel2c - sym.heaviside(((uel_lessEqualThreshold_threshold_Uel2c - uel_firstOrder_y_Uel2c) + vf.add_const(value=1e-06)))),
            (uel_multiSwitch1_firstActiveIndex_Uel2c - ((vf.add_const(value=0.0) + ((vf.add_const(value=1.0) * uel_multiSwitch1_u_1_Uel2c) * vf.add_const(value=1.0))) + ((vf.add_const(value=2.0) * uel_multiSwitch1_u_2_Uel2c) * (vf.add_const(value=1.0) - uel_multiSwitch1_u_1_Uel2c)))),
            (uel_add3_y_Uel2c - ((uel_add3_k1_Uel2c * uel_firstOrder3_y_Uel2c) + (uel_add3_k3_Uel2c * uel_firstOrder2_y_Uel2c))),
            (uel_limitedFirstOrder_y_Uel2c - ((sym.heaviside(((uel_limitedFirstOrder_I_y_Uel2c - uel_limitedFirstOrder_lim_uMax_Uel2c) - vf.add_const(value=1e-06))) * uel_limitedFirstOrder_lim_uMax_Uel2c) + ((vf.add_const(value=1.0) - sym.heaviside(((uel_limitedFirstOrder_I_y_Uel2c - uel_limitedFirstOrder_lim_uMax_Uel2c) - vf.add_const(value=1e-06)))) * ((sym.heaviside(((uel_limitedFirstOrder_lim_uMin_Uel2c - uel_limitedFirstOrder_I_y_Uel2c) - vf.add_const(value=1e-06))) * uel_limitedFirstOrder_lim_uMin_Uel2c) + ((vf.add_const(value=1.0) - sym.heaviside(((uel_limitedFirstOrder_lim_uMin_Uel2c - uel_limitedFirstOrder_I_y_Uel2c) - vf.add_const(value=1e-06)))) * uel_limitedFirstOrder_I_y_Uel2c))))),
            (uel_limitedFirstOrder_feedback_y_Uel2c - (uel_limitedFirstOrder_Gk_y_Uel2c - uel_limitedFirstOrder_y_Uel2c)),
            (uel_limitedFirstOrder_G_y_Uel2c - (uel_limitedFirstOrder_G_k_Uel2c * uel_limitedFirstOrder_feedback_y_Uel2c)),
            (uel_limitedFirstOrder_I_u_Uel2c - (((vf.add_const(value=1.0) - ((vf.add_const(value=1.0) - ((sym.heaviside(((uel_limitedFirstOrder_G_y_Uel2c - vf.add_const(value=0.0)) + vf.add_const(value=1e-06))) * sym.heaviside(((uel_limitedFirstOrder_G_y_Uel2c - vf.add_const(value=0.0)) + vf.add_const(value=1e-06)))) * sym.heaviside(((uel_limitedFirstOrder_I_y_Uel2c - uel_limitedFirstOrder_lim_uMax_Uel2c) - vf.add_const(value=1e-06))))) * (vf.add_const(value=1.0) - ((((((sym.heaviside(((uel_limitedFirstOrder_G_y_Uel2c - vf.add_const(value=0.0)) + vf.add_const(value=1e-06))) * sym.heaviside(((uel_limitedFirstOrder_I_y_Uel2c - uel_limitedFirstOrder_lim_uMax_Uel2c) - vf.add_const(value=1e-06)))) * sym.heaviside(((vf.add_const(value=0.0) - uel_limitedFirstOrder_G_y_Uel2c) + vf.add_const(value=1e-06)))) * sym.heaviside(((uel_limitedFirstOrder_G_y_Uel2c - vf.add_const(value=0.0)) + vf.add_const(value=1e-06)))) * sym.heaviside(((uel_limitedFirstOrder_I_y_Uel2c - uel_limitedFirstOrder_lim_uMax_Uel2c) - vf.add_const(value=1e-06)))) * sym.heaviside(((vf.add_const(value=0.0) - uel_limitedFirstOrder_G_y_Uel2c) + vf.add_const(value=1e-06)))) * sym.heaviside(((uel_limitedFirstOrder_lim_uMin_Uel2c - uel_limitedFirstOrder_I_y_Uel2c) - vf.add_const(value=1e-06))))))) * vf.add_const(value=0.0)) + ((vf.add_const(value=1.0) - (vf.add_const(value=1.0) - ((vf.add_const(value=1.0) - ((sym.heaviside(((uel_limitedFirstOrder_G_y_Uel2c - vf.add_const(value=0.0)) + vf.add_const(value=1e-06))) * sym.heaviside(((uel_limitedFirstOrder_G_y_Uel2c - vf.add_const(value=0.0)) + vf.add_const(value=1e-06)))) * sym.heaviside(((uel_limitedFirstOrder_I_y_Uel2c - uel_limitedFirstOrder_lim_uMax_Uel2c) - vf.add_const(value=1e-06))))) * (vf.add_const(value=1.0) - ((((((sym.heaviside(((uel_limitedFirstOrder_G_y_Uel2c - vf.add_const(value=0.0)) + vf.add_const(value=1e-06))) * sym.heaviside(((uel_limitedFirstOrder_I_y_Uel2c - uel_limitedFirstOrder_lim_uMax_Uel2c) - vf.add_const(value=1e-06)))) * sym.heaviside(((vf.add_const(value=0.0) - uel_limitedFirstOrder_G_y_Uel2c) + vf.add_const(value=1e-06)))) * sym.heaviside(((uel_limitedFirstOrder_G_y_Uel2c - vf.add_const(value=0.0)) + vf.add_const(value=1e-06)))) * sym.heaviside(((uel_limitedFirstOrder_I_y_Uel2c - uel_limitedFirstOrder_lim_uMax_Uel2c) - vf.add_const(value=1e-06)))) * sym.heaviside(((vf.add_const(value=0.0) - uel_limitedFirstOrder_G_y_Uel2c) + vf.add_const(value=1e-06)))) * sym.heaviside(((uel_limitedFirstOrder_lim_uMin_Uel2c - uel_limitedFirstOrder_I_y_Uel2c) - vf.add_const(value=1e-06)))))))) * uel_limitedFirstOrder_G_y_Uel2c))),
            (uel_switch_y_Uel2c - ((uel_booleanConstant_k_Uel2c * uel_const_k_Uel2c) + ((vf.add_const(value=1.0) - uel_booleanConstant_k_Uel2c) * uel_limitedFirstOrder_y_Uel2c))),
            (uel_product2_y_Uel2c - (uel_add3_y_Uel2c * uel_switch_y_Uel2c)),
            (uel_limitedPI_add_y_Uel2c - ((uel_limitedPI_add_k1_Uel2c * uel_product2_y_Uel2c) + (uel_limitedPI_add_k2_Uel2c * uel_limitedPI_integrator_y_Uel2c))),
            (uel_limitedPI_y_Uel2c - ((sym.heaviside(((uel_limitedPI_add_y_Uel2c - uel_limitedPI_limiter1_uMax_Uel2c) - vf.add_const(value=1e-06))) * uel_limitedPI_limiter1_uMax_Uel2c) + ((vf.add_const(value=1.0) - sym.heaviside(((uel_limitedPI_add_y_Uel2c - uel_limitedPI_limiter1_uMax_Uel2c) - vf.add_const(value=1e-06)))) * ((sym.heaviside(((uel_limitedPI_limiter1_uMin_Uel2c - uel_limitedPI_add_y_Uel2c) - vf.add_const(value=1e-06))) * uel_limitedPI_limiter1_uMin_Uel2c) + ((vf.add_const(value=1.0) - sym.heaviside(((uel_limitedPI_limiter1_uMin_Uel2c - uel_limitedPI_add_y_Uel2c) - vf.add_const(value=1e-06)))) * uel_limitedPI_add_y_Uel2c))))),
            (uel_add_y_Uel2c - ((uel_add_k1_Uel2c * uel_limitedPI_y_Uel2c) + (uel_add_k2_Uel2c * uel_firstOrder4_y_Uel2c))),
            (uel_limitedLeadLag_feedback_y_Uel2c - (uel_add_y_Uel2c - uel_limitedLeadLag_firstOrder_y_Uel2c)),
            (uel_limitedLeadLag_gain_y_Uel2c - (uel_limitedLeadLag_gain_k_Uel2c * uel_limitedLeadLag_feedback_y_Uel2c)),
            (uel_limitedLeadLag_y_Uel2c - ((sym.heaviside(((uel_limitedLeadLag_gain_y_Uel2c - uel_limitedLeadLag_limiter_uMax_Uel2c) - vf.add_const(value=1e-06))) * uel_limitedLeadLag_limiter_uMax_Uel2c) + ((vf.add_const(value=1.0) - sym.heaviside(((uel_limitedLeadLag_gain_y_Uel2c - uel_limitedLeadLag_limiter_uMax_Uel2c) - vf.add_const(value=1e-06)))) * ((sym.heaviside(((uel_limitedLeadLag_limiter_uMin_Uel2c - uel_limitedLeadLag_gain_y_Uel2c) - vf.add_const(value=1e-06))) * uel_limitedLeadLag_limiter_uMin_Uel2c) + ((vf.add_const(value=1.0) - sym.heaviside(((uel_limitedLeadLag_limiter_uMin_Uel2c - uel_limitedLeadLag_gain_y_Uel2c) - vf.add_const(value=1e-06)))) * uel_limitedLeadLag_gain_y_Uel2c))))),
            (uel_limitedLeadLag1_feedback_y_Uel2c - (uel_limitedLeadLag_y_Uel2c - uel_limitedLeadLag1_firstOrder_y_Uel2c)),
            (uel_limitedLeadLag1_gain_y_Uel2c - (uel_limitedLeadLag1_gain_k_Uel2c * uel_limitedLeadLag1_feedback_y_Uel2c)),
            (uel_UUelPu_Uel2c - ((sym.heaviside(((uel_limitedLeadLag1_gain_y_Uel2c - uel_limitedLeadLag1_limiter_uMax_Uel2c) - vf.add_const(value=1e-06))) * uel_limitedLeadLag1_limiter_uMax_Uel2c) + ((vf.add_const(value=1.0) - sym.heaviside(((uel_limitedLeadLag1_gain_y_Uel2c - uel_limitedLeadLag1_limiter_uMax_Uel2c) - vf.add_const(value=1e-06)))) * ((sym.heaviside(((uel_limitedLeadLag1_limiter_uMin_Uel2c - uel_limitedLeadLag1_gain_y_Uel2c) - vf.add_const(value=1e-06))) * uel_limitedLeadLag1_limiter_uMin_Uel2c) + ((vf.add_const(value=1.0) - sym.heaviside(((uel_limitedLeadLag1_limiter_uMin_Uel2c - uel_limitedLeadLag1_gain_y_Uel2c) - vf.add_const(value=1e-06)))) * uel_limitedLeadLag1_gain_y_Uel2c))))),
            ((uel_limitedPI_hysteresisMax_y_Uel2c - sym.heaviside(((uel_limitedPI_add_y_Uel2c - uel_limitedPI_hysteresisMax_uHigh_Uel2c) - vf.add_const(value=1e-06)))) - sym.heaviside(((uel_limitedPI_add_y_Uel2c - uel_limitedPI_hysteresisMax_uLow_Uel2c) + vf.add_const(value=1e-06)))),
            ((uel_limitedPI_hysteresisMin_y_Uel2c - sym.heaviside(((uel_limitedPI_add_y_Uel2c - uel_limitedPI_hysteresisMin_uHigh_Uel2c) - vf.add_const(value=1e-06)))) - sym.heaviside(((uel_limitedPI_add_y_Uel2c - uel_limitedPI_hysteresisMin_uLow_Uel2c) + vf.add_const(value=1e-06)))),
            (uel_limitedPI_switch1_u2_Uel2c - (vf.add_const(value=1.0) - ((vf.add_const(value=1.0) - uel_limitedPI_hysteresisMax_y_Uel2c) * (vf.add_const(value=1.0) - (vf.add_const(value=1.0) - uel_limitedPI_hysteresisMin_y_Uel2c))))),
            (uel_limitedPI_switch1_y_Uel2c - ((uel_limitedPI_switch1_u2_Uel2c * uel_limitedPI_const_k_Uel2c) + ((vf.add_const(value=1.0) - uel_limitedPI_switch1_u2_Uel2c) * uel_product2_y_Uel2c))),
            (uel_multiSwitch1_expr_1_Uel2c - uel_firstOrder_y_Uel2c),
            (uel_multiSwitch1_y_Uel2c - (((sym.heaviside(((uel_multiSwitch1_firstActiveIndex_Uel2c - vf.add_const(value=0.0)) + vf.add_const(value=1e-06))) * sym.heaviside(((vf.add_const(value=0.0) - uel_multiSwitch1_firstActiveIndex_Uel2c) + vf.add_const(value=1e-06)))) * uel_multiSwitch1_y_default_Uel2c) + ((vf.add_const(value=1.0) - (sym.heaviside(((uel_multiSwitch1_firstActiveIndex_Uel2c - vf.add_const(value=0.0)) + vf.add_const(value=1e-06))) * sym.heaviside(((vf.add_const(value=0.0) - uel_multiSwitch1_firstActiveIndex_Uel2c) + vf.add_const(value=1e-06))))) * uel_multiSwitch1_expr_Uel2c))),
            (uel_power_y_Uel2c - (uel_multiSwitch1_y_Uel2c ** uel_power_N_Uel2c)),
            (uel_power1_y_Uel2c - (uel_multiSwitch1_y_Uel2c ** uel_power1_N_Uel2c)),
            (uel_division_y_Uel2c - (uel_PGenPu_Uel2c / uel_power1_y_Uel2c)),
            (uel_combiTable1Ds_y_1_Uel2c - ((((((vf.add_const(value=-0.31) * sym.heaviside(((vf.add_const(value=0.0) - uel_firstOrder1_y_Uel2c) - vf.add_const(value=1e-06)))) + ((((((vf.add_const(value=-0.31) - vf.add_const(value=-0.31)) / (vf.add_const(value=0.3) - vf.add_const(value=0.0))) * uel_firstOrder1_y_Uel2c) + (vf.add_const(value=-0.31) - (((vf.add_const(value=-0.31) - vf.add_const(value=-0.31)) / (vf.add_const(value=0.3) - vf.add_const(value=0.0))) * vf.add_const(value=0.0)))) * sym.heaviside(((uel_firstOrder1_y_Uel2c - vf.add_const(value=0.0)) + vf.add_const(value=1e-06)))) * sym.heaviside(((vf.add_const(value=0.3) - uel_firstOrder1_y_Uel2c) - vf.add_const(value=1e-06))))) + ((((((vf.add_const(value=-0.28) - vf.add_const(value=-0.31)) / (vf.add_const(value=0.6) - vf.add_const(value=0.3))) * uel_firstOrder1_y_Uel2c) + (vf.add_const(value=-0.31) - (((vf.add_const(value=-0.28) - vf.add_const(value=-0.31)) / (vf.add_const(value=0.6) - vf.add_const(value=0.3))) * vf.add_const(value=0.3)))) * sym.heaviside(((uel_firstOrder1_y_Uel2c - vf.add_const(value=0.3)) + vf.add_const(value=1e-06)))) * sym.heaviside(((vf.add_const(value=0.6) - uel_firstOrder1_y_Uel2c) - vf.add_const(value=1e-06))))) + ((((((vf.add_const(value=-0.21) - vf.add_const(value=-0.28)) / (vf.add_const(value=0.9) - vf.add_const(value=0.6))) * uel_firstOrder1_y_Uel2c) + (vf.add_const(value=-0.28) - (((vf.add_const(value=-0.21) - vf.add_const(value=-0.28)) / (vf.add_const(value=0.9) - vf.add_const(value=0.6))) * vf.add_const(value=0.6)))) * sym.heaviside(((uel_firstOrder1_y_Uel2c - vf.add_const(value=0.6)) + vf.add_const(value=1e-06)))) * sym.heaviside(((vf.add_const(value=0.9) - uel_firstOrder1_y_Uel2c) - vf.add_const(value=1e-06))))) + ((((((vf.add_const(value=0.0) - vf.add_const(value=-0.21)) / (vf.add_const(value=1.02) - vf.add_const(value=0.9))) * uel_firstOrder1_y_Uel2c) + (vf.add_const(value=-0.21) - (((vf.add_const(value=0.0) - vf.add_const(value=-0.21)) / (vf.add_const(value=1.02) - vf.add_const(value=0.9))) * vf.add_const(value=0.9)))) * sym.heaviside(((uel_firstOrder1_y_Uel2c - vf.add_const(value=0.9)) + vf.add_const(value=1e-06)))) * sym.heaviside(((vf.add_const(value=1.02) - uel_firstOrder1_y_Uel2c) - vf.add_const(value=1e-06))))) + (vf.add_const(value=0.0) * sym.heaviside(((uel_firstOrder1_y_Uel2c - vf.add_const(value=1.02)) + vf.add_const(value=1e-06)))))),
            (uel_product1_y_Uel2c - (uel_combiTable1Ds_y_1_Uel2c * uel_power_y_Uel2c)),
        ],
        algebraic_vars=[
            uel_limitedFirstOrder_Gk_y_Uel2c,
            uel_multiSwitch1_expr_2_Uel2c,
            uel_multiSwitch1_u_1_Uel2c,
            uel_multiSwitch1_u_2_Uel2c,
            uel_multiSwitch1_firstActiveIndex_Uel2c,
            uel_add3_y_Uel2c,
            uel_limitedFirstOrder_y_Uel2c,
            uel_limitedFirstOrder_feedback_y_Uel2c,
            uel_limitedFirstOrder_G_y_Uel2c,
            uel_limitedFirstOrder_I_u_Uel2c,
            uel_switch_y_Uel2c,
            uel_product2_y_Uel2c,
            uel_limitedPI_add_y_Uel2c,
            uel_limitedPI_y_Uel2c,
            uel_add_y_Uel2c,
            uel_limitedLeadLag_feedback_y_Uel2c,
            uel_limitedLeadLag_gain_y_Uel2c,
            uel_limitedLeadLag_y_Uel2c,
            uel_limitedLeadLag1_feedback_y_Uel2c,
            uel_limitedLeadLag1_gain_y_Uel2c,
            uel_UUelPu_Uel2c,
            uel_limitedPI_hysteresisMax_y_Uel2c,
            uel_limitedPI_hysteresisMin_y_Uel2c,
            uel_limitedPI_switch1_u2_Uel2c,
            uel_limitedPI_switch1_y_Uel2c,
            uel_multiSwitch1_expr_1_Uel2c,
            uel_multiSwitch1_y_Uel2c,
            uel_power_y_Uel2c,
            uel_power1_y_Uel2c,
            uel_division_y_Uel2c,
            uel_combiTable1Ds_y_1_Uel2c,
            uel_product1_y_Uel2c,
            uel_kAdj_Uel2c,
            uel_multiSwitch1_expr_Uel2c,
            uel_PGenPu_Uel2c,
            uel_QGenPu_Uel2c,
            uel_VFbPu_Uel2c,
            uel_VfPu_Uel2c,
            uel_utPu_im_Uel2c,
            uel_utPu_re_Uel2c,
            uel_limitedFirstOrder_lim_simplifiedExpr_Uel2c,
            uel_limitedFirstOrder_I_local_reset_Uel2c,
            uel_limitedFirstOrder_I_local_set_Uel2c,
            uel_limitedPI_limiter1_simplifiedExpr_Uel2c,
            uel_limitedPI_integrator_local_reset_Uel2c,
            uel_limitedPI_integrator_local_set_Uel2c,
            uel_limitedLeadLag_limiter_simplifiedExpr_Uel2c,
            uel_limitedLeadLag1_limiter_simplifiedExpr_Uel2c,
            START_uel_firstOrder_y_Uel2c,
            START_uel_firstOrder1_y_Uel2c,
            START_uel_firstOrder2_y_Uel2c,
            START_uel_firstOrder3_y_Uel2c,
            START_uel_limitedLeadLag_firstOrder_y_Uel2c,
            START_uel_limitedLeadLag1_firstOrder_y_Uel2c,
            START_uel_firstOrder4_y_Uel2c,
            PRE_uel_limitedPI_hysteresisMin_y_Uel2c,
            PRE_uel_limitedPI_hysteresisMax_y_Uel2c,
            uel_gain_y_Uel2c,
            uel_complexToPolar_phi_Uel2c,
            uel_UPu_Uel2c,
            PRE_uel_multiSwitch1_u_2_Uel2c,
            PRE_uel_multiSwitch1_u_1_Uel2c,
        ],
        init_eqs={
            uel_multiSwitch1_y_Uel2c: vf.add_const(value=1.0),
            uel_multiSwitch1_expr_Uel2c: vf.add_const(value=1.0),
            uel_firstOrder_y_Uel2c: START_uel_firstOrder_y_Uel2c,
            uel_firstOrder1_y_Uel2c: START_uel_firstOrder1_y_Uel2c,
            uel_firstOrder2_y_Uel2c: START_uel_firstOrder2_y_Uel2c,
            uel_firstOrder3_y_Uel2c: START_uel_firstOrder3_y_Uel2c,
            uel_firstOrder4_y_Uel2c: START_uel_firstOrder4_y_Uel2c,
            uel_limitedFirstOrder_I_y_Uel2c: uel_limitedFirstOrder_I_y_start_Uel2c,
            uel_limitedLeadLag_firstOrder_y_Uel2c: START_uel_limitedLeadLag_firstOrder_y_Uel2c,
            uel_limitedLeadLag1_firstOrder_y_Uel2c: START_uel_limitedLeadLag1_firstOrder_y_Uel2c,
            uel_limitedPI_integrator_y_Uel2c: uel_limitedPI_integrator_y_start_Uel2c,
            uel_PGenPu_Uel2c: vf.add_const(value=0.8),
            uel_QGenPu_Uel2c: vf.add_const(value=0.0),
            uel_UUelPu_Uel2c: uel_limitedLeadLag1_Y0_Uel2c,
            uel_VFbPu_Uel2c: vf.add_const(value=1.0),
            uel_VfPu_Uel2c: vf.add_const(value=0.0),
            uel_limitedFirstOrder_y_Uel2c: uel_limitedFirstOrder_Y0_Uel2c,
            uel_limitedLeadLag_y_Uel2c: uel_limitedLeadLag_Y0_Uel2c,
            uel_limitedPI_y_Uel2c: uel_limitedPI_Y0_Uel2c,
            uel_utPu_im_Uel2c: vf.add_const(value=0.0),
            uel_utPu_re_Uel2c: vf.add_const(value=1.0),
            uel_limitedPI_hysteresisMin_y_Uel2c: (sym.heaviside(((uel_limitedPI_add_y_Uel2c - uel_limitedPI_hysteresisMin_uHigh_Uel2c) - vf.add_const(value=1e-06))) + sym.heaviside(((uel_limitedPI_add_y_Uel2c - uel_limitedPI_hysteresisMin_uLow_Uel2c) + vf.add_const(value=1e-06)))),
            uel_limitedFirstOrder_lim_simplifiedExpr_Uel2c: vf.add_const(value=0.0),
            uel_limitedFirstOrder_I_local_reset_Uel2c: vf.add_const(value=0.0),
            uel_limitedFirstOrder_I_local_set_Uel2c: vf.add_const(value=0.0),
            uel_limitedPI_limiter1_simplifiedExpr_Uel2c: vf.add_const(value=0.0),
            uel_limitedPI_integrator_local_reset_Uel2c: vf.add_const(value=0.0),
            uel_limitedPI_integrator_local_set_Uel2c: vf.add_const(value=0.0),
            uel_limitedLeadLag_limiter_simplifiedExpr_Uel2c: vf.add_const(value=0.0),
            uel_limitedLeadLag1_limiter_simplifiedExpr_Uel2c: vf.add_const(value=0.0),
            PRE_uel_limitedPI_hysteresisMin_y_Uel2c: uel_limitedPI_hysteresisMin_pre_y_start_Uel2c,
            PRE_uel_limitedPI_hysteresisMax_y_Uel2c: uel_limitedPI_hysteresisMax_pre_y_start_Uel2c,
            uel_limitedPI_hysteresisMax_y_Uel2c: (sym.heaviside(((uel_limitedPI_add_y_Uel2c - uel_limitedPI_hysteresisMax_uHigh_Uel2c) - vf.add_const(value=1e-06))) + sym.heaviside(((uel_limitedPI_add_y_Uel2c - uel_limitedPI_hysteresisMax_uLow_Uel2c) + vf.add_const(value=1e-06)))),
            uel_gain_y_Uel2c: vf.add_const(value=0.0),
            uel_complexToPolar_phi_Uel2c: vf.add_const(value=0.0),
            uel_UPu_Uel2c: vf.add_const(value=1.0),
            PRE_uel_multiSwitch1_u_2_Uel2c: vf.add_const(value=0.0),
            PRE_uel_multiSwitch1_u_1_Uel2c: vf.add_const(value=0.0),
        },
        event_dict=event_dict,
        in_vars=[
            uel_PGenPu_Uel2c,
            uel_QGenPu_Uel2c,
            uel_VFbPu_Uel2c,
            uel_VfPu_Uel2c,
            uel_utPu_im_Uel2c,
            uel_utPu_re_Uel2c,
        ],
        out_vars=[
            uel_UUelPu_Uel2c,
        ],
        external_mapping=external_mapping,
        api_obj_mapping=api_obj_mapping,
        diff_vars=[
            d_uel_firstOrder_y_Uel2c,
            d_uel_firstOrder3_y_Uel2c,
            d_uel_limitedFirstOrder_I_y_Uel2c,
            d_uel_limitedLeadLag_firstOrder_y_Uel2c,
            d_uel_limitedLeadLag1_firstOrder_y_Uel2c,
            d_uel_limitedPI_integrator_y_Uel2c,
            d_uel_firstOrder4_y_Uel2c,
            d_uel_firstOrder1_y_Uel2c,
            d_uel_firstOrder2_y_Uel2c,
        ],
        name=template_name,
    )
    if (not math.isfinite(selected_output_limits[0])
            or not math.isfinite(selected_output_limits[1])
            or selected_output_limits[0] >= selected_output_limits[1]):
        raise ValueError('UEL2C output limits must be finite and ordered')
    else:
        pass
    templ.block.event_dict[uel_VULMinPu_Uel2c] = vf.add_const(value=selected_output_limits[0])
    templ.block.event_dict[uel_VULMaxPu_Uel2c] = vf.add_const(value=selected_output_limits[1])
    voltage_high: Expr = sym.heaviside(uel_firstOrder_y_Uel2c-vf.add_const(value=1.0)-vf.add_const(value=1e-6))
    voltage_above_bias: Expr = sym.heaviside(
        uel_firstOrder_y_Uel2c-uel_VBiasPu_Uel2c-vf.add_const(value=1e-6))
    voltage_bias_signal: Expr = (
        voltage_high*uel_firstOrder_y_Uel2c
        + (vf.add_const(value=1.0)-voltage_high)
        * (voltage_above_bias+(vf.add_const(value=1.0)-voltage_above_bias)
           * (uel_firstOrder_y_Uel2c/uel_VBiasPu_Uel2c))
    )
    voltage_bias_equation_index: int = -1
    for index, equation in enumerate(templ.block.algebraic_eqs):
        if isinstance(equation.left, Var) and equation.left.uid == uel_multiSwitch1_y_Uel2c.uid:
            voltage_bias_equation_index = index
        else:
            pass
    if voltage_bias_equation_index < 0:
        raise ValueError('UEL2C voltage-bias equation is missing')
    else:
        templ.block.algebraic_eqs[voltage_bias_equation_index] = (
            uel_multiSwitch1_y_Uel2c-voltage_bias_signal)
        templ.block.init_eqs[uel_multiSwitch1_y_Uel2c] = voltage_bias_signal
    if gain_reduction_mode is Uel2cGainReductionMode.FIXED:
        templ.block.event_dict[uel_Sw1_Uel2c] = vf.add_const(value=1.0)
    else:
        templ.block.event_dict[uel_Sw1_Uel2c] = vf.add_const(value=0.0)
    output_equation_index: int = -1
    for index, equation in enumerate(templ.block.algebraic_eqs):
        if isinstance(equation.left, Var) and equation.left.uid == uel_UUelPu_Uel2c.uid:
            output_equation_index = index
            output_expression: Expr = equation.right
        else:
            pass
    if output_equation_index < 0:
        raise ValueError('UEL2C output equation is missing')
    else:
        templ.block.algebraic_eqs[output_equation_index] = (
            uel_UUelPu_Uel2c - sym.hard_sat(
                output_expression,
                uel_VULMinPu_Uel2c,
                uel_VULMaxPu_Uel2c,
            )
        )
    if curve_points is not None:
        curve_expression: Expr = _build_source_curve_expression(
            vf,
            uel_firstOrder1_y_Uel2c,
            curve_points,
            third_quadrant_mode,
        )
        curve_equation_index: int = -1
        for index, equation in enumerate(templ.block.algebraic_eqs):
            if isinstance(equation.left, Var) and equation.left.uid == uel_combiTable1Ds_y_1_Uel2c.uid:
                curve_equation_index = index
            else:
                pass
        if curve_equation_index < 0:
            raise ValueError('UEL2C native curve lookup equation is missing')
        else:
            templ.block.algebraic_eqs[curve_equation_index] = (
                uel_combiTable1Ds_y_1_Uel2c - curve_expression
            )
    else:
        pass
    if parameters is not None:
        parameter_values: tuple[float, ...] = (
            parameters.tuv, parameters.tup, parameters.tuq, parameters.kui,
            parameters.kul, parameters.vuimax, parameters.vuimin, parameters.kuf,
            parameters.kfb, parameters.tul, parameters.tu1, parameters.tu2,
            parameters.tu3, parameters.tu4, parameters.vulmax, parameters.vulmin,
            parameters.vbias, parameters.kfix, parameters.tadj, parameters.tqref,
            parameters.vuelmax2, parameters.vuelmin2, parameters.vuelmax1,
            parameters.vuelmin1, parameters.xq,
        )
        if not all(math.isfinite(value) for value in parameter_values):
            raise ValueError('UEL2C parameters must be finite')
        elif parameters.k1 not in (0, 1, 2) or parameters.k2 not in (0, 1, 2):
            raise ValueError('UEL2C exponents must be zero, one, or two')
        elif min(parameters.tuv, parameters.tup, parameters.tuq, parameters.tul,
                 parameters.tu1, parameters.tu2, parameters.tu3, parameters.tu4,
                 parameters.tadj, parameters.tqref) <= 0.0:
            raise ValueError('UEL2C zero filter and lead-lag times are unsupported')
        elif parameters.xq <= 0.0:
            raise ValueError('UEL2C requires positive q-axis reactance')
        elif (parameters.vuimax <= parameters.vuimin
              or parameters.vulmax <= parameters.vulmin
              or parameters.vuelmax2 <= parameters.vuelmin2
              or parameters.vuelmax1 <= parameters.vuelmin1):
            raise ValueError('UEL2C limiter bounds are unordered')
        else:
            pass
        source_parameter_values: tuple[tuple[Var, float], ...] = (
            (uel_K1_Uel2c, float(parameters.k1)),
            (uel_K2_Uel2c, float(parameters.k2)),
            (uel_tUV_Uel2c, parameters.tuv),
            (uel_tUP_Uel2c, parameters.tup),
            (uel_tUQ_Uel2c, parameters.tuq),
            (uel_Kui_Uel2c, parameters.kui),
            (uel_Kul_Uel2c, parameters.kul),
            (uel_VUiMaxPu_Uel2c, parameters.vuimax),
            (uel_VUiMinPu_Uel2c, parameters.vuimin),
            (uel_Kuf_Uel2c, parameters.kuf),
            (uel_KFb_Uel2c, parameters.kfb),
            (uel_tUl_Uel2c, parameters.tul),
            (uel_tU1_Uel2c, parameters.tu1),
            (uel_tU2_Uel2c, parameters.tu2),
            (uel_tU3_Uel2c, parameters.tu3),
            (uel_tU4_Uel2c, parameters.tu4),
            (uel_VBiasPu_Uel2c, parameters.vbias),
            (uel_VBias0Pu_Uel2c, parameters.vbias),
            (uel_KFix_Uel2c, parameters.kfix),
            (uel_tAdj_Uel2c, parameters.tadj),
            (uel_tQRef_Uel2c, parameters.tqref),
            (uel_VUel2MaxPu_Uel2c, parameters.vuelmax2),
            (uel_VUel2MinPu_Uel2c, parameters.vuelmin2),
            (uel_VUel1MaxPu_Uel2c, parameters.vuelmax1),
            (uel_VUel1MinPu_Uel2c, parameters.vuelmin1),
            (uel_XqPu_Uel2c, parameters.xq),
        )
        for parameter, value in source_parameter_values:
            templ.block.event_dict[parameter] = vf.add_const(value=value)
    else:
        pass
    templ.comment = 'Generator under-excitation limiter UEL2C'
    return templ
