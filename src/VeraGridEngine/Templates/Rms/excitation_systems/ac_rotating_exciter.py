# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Colib AC rotating-exciter submodel with exponential saturation."""

from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Templates.Rms.synchronous_machines.genrou_exc_gov_rms_template import _esst3a_fex
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class AcRotatingExciterSettings:
    """Store Colib AC rotating-exciter coefficients and equilibrium values."""

    __slots__ = ('aex', 'bex', 'kc', 'kd', 'ke', 'te', 'tol_li', 'vemin',
                 'vfemax', 'efe0', 'ir0', 've0')

    def __init__(
            self,
            aex: float = 0.0,
            bex: float = 1.0,
            kc: float = 0.1,
            kd: float = 0.1,
            ke: float = 1.0,
            te: float = 0.5,
            tol_li: float = 0.0,
            vemin: float = 0.0,
            vfemax: float = 5.0,
            efe0: float | None = None,
            ir0: float = 0.0,
            ve0: float = 1.0,
    ) -> None:
        """Store one AC rotating-exciter operating point.

        :param aex: Exponential saturation gain.
        :param bex: Exponential saturation exponent.
        :param kc: Rectifier loading factor.
        :param kd: Demagnetizing factor.
        :param ke: Exciter field-resistance constant.
        :param te: Exciter field time constant in seconds.
        :param tol_li: Limited-integrator crossing tolerance.
        :param vemin: Minimum exciter voltage.
        :param vfemax: Maximum exciter field-current signal.
        :param efe0: Initial regulator output, or ``None`` for equilibrium.
        :param ir0: Initial rotor current.
        :param ve0: Initial exciter voltage.
        :return: ``None``.
        """
        self.aex: float = aex
        self.bex: float = bex
        self.kc: float = kc
        self.kd: float = kd
        self.ke: float = ke
        self.te: float = te
        self.tol_li: float = tol_li
        self.vemin: float = vemin
        self.vfemax: float = vfemax
        self.efe0: float | None = efe0
        self.ir0: float = ir0
        self.ve0: float = ve0


def build_ac_rotating_exciter_template(
        vf: VarFactory,
        name: str = 'AcRotatingExciter',
        settings: AcRotatingExciterSettings | None = None,
) -> RmsModelTemplate:
    """Build the Colib AC rotating-exciter state, feedback and rectifier.

    :param vf: Variable factory used to allocate symbolic variables.
    :param name: Unique submodel instance name.
    :param settings: Physical parameters and solved operating point.
    :return: RMS rotating-exciter template exposing ``Efd`` and ``Vfe``.
    :raises ValueError: If the supplied operating point is physically invalid.
    """
    selected: AcRotatingExciterSettings = (
        AcRotatingExciterSettings() if settings is None else settings
    )
    finite_values: tuple[float, ...] = (
        selected.aex, selected.bex, selected.kc, selected.kd, selected.ke,
        selected.te, selected.tol_li, selected.vemin, selected.vfemax,
        selected.ir0, selected.ve0,
    )
    if not all(math.isfinite(value) for value in finite_values):
        raise ValueError('AC rotating-exciter settings must be finite')
    elif selected.efe0 is not None and not math.isfinite(selected.efe0):
        raise ValueError('AC rotating-exciter initial input must be finite')
    elif (selected.aex < 0.0 or selected.kc < 0.0 or selected.kd < 0.0
          or selected.ke <= 0.0 or selected.te <= 0.0):
        raise ValueError('AC rotating-exciter gains and time are invalid')
    elif selected.vemin < 0.0 or selected.vfemax <= 0.0 or selected.ve0 <= 0.0:
        raise ValueError('AC rotating-exciter voltage limits are invalid')
    else:
        pass

    control: ControlRealization = ControlRealization(vf, name)
    saturation_gain: Var = control.parameter('AEx', selected.aex)
    saturation_exponent: Var = control.parameter('BEx', selected.bex)
    rectifier_loading: Var = control.parameter('Kc', selected.kc)
    demagnetizing: Var = control.parameter('Kd', selected.kd)
    field_resistance: Var = control.parameter('Ke', selected.ke)
    field_time: Var = control.parameter('tE', selected.te)
    control.parameter('TolLi', selected.tol_li)
    field_minimum: Var = control.parameter('VeMinPu', selected.vemin)
    field_maximum: Var = control.parameter('VfeMaxPu', selected.vfemax)
    initial_input: float = 0.0 if selected.efe0 is None else selected.efe0
    regulator_output: Var = control.input('EfePu', Const(initial_input))
    rotor_current: Var = control.input('IrPu', Const(selected.ir0))
    exciter_voltage: Var = vf.add_var('VePu_' + name)

    # The Colib saturation law is exponential rather than AC9C sample based.
    saturation_expression: Expr = saturation_gain * sym.exp(
        saturation_exponent * exciter_voltage
    )
    saturation_initial: float = selected.aex * math.exp(selected.bex * selected.ve0)
    saturation: Var = control.algebraic(
        'SePu', saturation_expression, Const(saturation_initial)
    )
    field_feedback_expression: Expr = (
        (field_resistance + saturation) * exciter_voltage
        + demagnetizing * rotor_current
    )
    field_feedback_initial: float = (
        (selected.ke + saturation_initial) * selected.ve0 + selected.kd * selected.ir0
    )
    if selected.efe0 is not None and not math.isclose(
            selected.efe0, field_feedback_initial, rel_tol=1e-9, abs_tol=1e-9):
        raise ValueError('AC rotating-exciter initial Efe must balance feedback')
    else:
        pass
    control.block.init_eqs[regulator_output] = Const(field_feedback_initial)
    field_feedback: Var = control.algebraic(
        'VfePu', field_feedback_expression, Const(field_feedback_initial)
    )
    upper_voltage: Expr = (
        field_maximum - demagnetizing * rotor_current
    ) / (field_resistance + saturation)
    upper_initial: float = (
        selected.vfemax - selected.kd * selected.ir0
    ) / (selected.ke + saturation_initial)
    if selected.ve0 < selected.vemin or selected.ve0 > upper_initial:
        raise ValueError('AC rotating-exciter initial voltage exceeds dynamic limit')
    else:
        pass
    control.differential(
        exciter_voltage,
        (regulator_output - field_feedback) / field_time,
        Const(selected.ve0),
        field_minimum,
        upper_voltage,
    )

    normalized_current: Expr = sym.safe_divide(
        rectifier_loading * rotor_current, exciter_voltage, Const(1.0)
    )
    excitation_voltage: Var = control.algebraic(
        'EfdPu',
        exciter_voltage * _esst3a_fex(normalized_current),
        Const(selected.ve0) * _esst3a_fex(Const(selected.kc * selected.ir0 / selected.ve0)),
    )
    return control.finish(
        (excitation_voltage, field_feedback),
        'Colib AC rotating exciter with exponential saturation and rectifier',
    )
