# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""AC9C rotating-exciter field state and rectifier regulation."""
from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Templates.Rms.synchronous_machines.genrou_exc_gov_rms_template import _esst3a_fex
from VeraGridEngine.Templates.Rms.excitation_systems.ieeex1_ieeest_rms_template import _quadratic_saturation_coefficients
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class Ac9cRotatingExciterSettings:
    """Store AC9C field, saturation and rectifier coefficients."""

    __slots__ = ('kc', 'kd', 'ke', 'te', 'vfemax', 'vemin', 'e1', 'se1',
                 'e2', 'se2', 'efe0', 'ifd0', 've0')

    def __init__(self, kc: float = .1, kd: float = .1, ke: float = 1.0,
                 te: float = .5, vfemax: float = 5.0, vemin: float = 0.0,
                 e1: float = 0.0, se1: float = 0.0, e2: float = 0.0,
                 se2: float = 0.0, efe0: float | None = None, ifd0: float = 0.0,
                 ve0: float = 1.0) -> None:
        """Store source parameters and the solved equilibrium point.

        :param kc: Diode-bridge loading factor.
        :param kd: Exciter demagnetizing coefficient.
        :param ke: Exciter field-resistance coefficient.
        :param te: Exciter field time constant in seconds.
        :param vfemax: Maximum field-current-equivalent capability.
        :param vemin: Minimum exciter field voltage.
        :param e1: First saturation voltage sample.
        :param se1: Saturation factor at E1.
        :param e2: Second saturation voltage sample.
        :param se2: Saturation factor at E2.
        :param efe0: Initial exciter input voltage, or ``None`` to use equilibrium feedback.
        :param ifd0: Initial field current.
        :param ve0: Initial internal exciter voltage.
        """
        self.kc: float = kc
        self.kd: float = kd
        self.ke: float = ke
        self.te: float = te
        self.vfemax: float = vfemax
        self.vemin: float = vemin
        self.e1: float = e1
        self.se1: float = se1
        self.e2: float = e2
        self.se2: float = se2
        self.efe0: float | None = efe0
        self.ifd0: float = ifd0
        self.ve0: float = ve0


def build_ac9c_rotating_exciter_template(
        vf: VarFactory,
        name: str = 'AC9C rotating exciter',
        settings: Ac9cRotatingExciterSettings | None = None,
) -> RmsModelTemplate:
    """Build the AC9C ``VE`` state, field feedback and rectifier function.

    The Model Library state/parameter list and the archived independent AC9C
    diagram give ``dVE/dt=(EFE-VFE)/TE``,
    ``VFE=(KE+SE(VE))*VE+KD*IFD``, the dynamic upper field limit
    ``(VFEMAX-KD*IFD)/(KE+SE(VE))``, and ``EFD=VE*FEX(KC*IFD/VE)``.
    ``EFE`` and ``IFD`` remain explicit host inputs for source gate and machine
    current connections.

    :param vf: Symbol factory owning exciter symbols.
    :param name: Unique component label.
    :param settings: Physical coefficients and solved operating point.
    :return: Native block exposing EFD, VFE and internal VE.
    :raises ValueError: Invalid field domain, saturation samples or equilibrium.
    """
    selected: Ac9cRotatingExciterSettings = (
        Ac9cRotatingExciterSettings() if settings is None else settings
    )
    values: tuple[float, ...] = (
        selected.kc, selected.kd, selected.ke, selected.te, selected.vfemax,
        selected.vemin, selected.e1, selected.se1, selected.e2, selected.se2,
        selected.ifd0, selected.ve0,
    )
    if (not all(math.isfinite(value) for value in values)
            or (selected.efe0 is not None and not math.isfinite(selected.efe0))):
        raise ValueError('AC9C rotating-exciter settings must be finite')
    elif min(selected.kc, selected.kd) < 0.0 or min(selected.ke, selected.te) <= 0.0:
        raise ValueError('AC9C rotating-exciter gains and time are invalid')
    elif (selected.vfemax <= 0.0 or selected.vemin < 0.0
          or selected.ve0 <= 0.0 or selected.ve0 < selected.vemin):
        raise ValueError('AC9C rotating-exciter field limits are invalid')
    elif (selected.se1 == 0.0) != (selected.se2 == 0.0):
        raise ValueError('AC9C saturation requires two samples or two zeros')
    elif selected.se1 < 0.0 or selected.se2 < 0.0:
        raise ValueError('AC9C saturation factors must be nonnegative')
    elif selected.se1 > 0.0 and (
            selected.e1 <= 0.0 or selected.e2 <= 0.0 or selected.e1 == selected.e2):
        raise ValueError('AC9C saturation voltage samples are invalid')
    else:
        pass

    control: ControlRealization = ControlRealization(vf, name)
    loading: Var = control.parameter('KC', selected.kc)
    demagnetizing: Var = control.parameter('KD', selected.kd)
    field_resistance: Var = control.parameter('KE', selected.ke)
    field_time: Var = control.parameter('TE', selected.te)
    field_maximum: Var = control.parameter('VFEMAX', selected.vfemax)
    field_minimum: Var = control.parameter('VEMIN', selected.vemin)
    initial_efe_guess: float = 0.0 if selected.efe0 is None else selected.efe0
    field_voltage_input: Var = control.input('EFEPu', Const(initial_efe_guess))
    field_current: Var = control.input('IFDPu', Const(selected.ifd0))
    field_voltage: Var = vf.add_var('ExciterFieldVoltagePu_' + name)

    saturation_start: Expr
    saturation_gain: Expr
    saturation_initial: float
    if selected.se1 > 0.0:
        first_voltage: Var = control.parameter('E1', selected.e1)
        first_saturation: Var = control.parameter('SE1', selected.se1)
        second_voltage: Var = control.parameter('E2', selected.e2)
        second_saturation: Var = control.parameter('SE2', selected.se2)
        saturation_coefficients: tuple[Expr, Expr] = _quadratic_saturation_coefficients(
            first_voltage, first_saturation, second_voltage, second_saturation,
        )
        saturation_start = saturation_coefficients[0]
        saturation_gain = saturation_coefficients[1]
        saturation_ratio: float = math.sqrt(
            selected.se1 * selected.e1 / (selected.se2 * selected.e2)
        )
        if saturation_ratio == 1.0:
            raise ValueError('AC9C saturation samples do not define a finite curve')
        else:
            pass
        saturation_start_value: float = selected.e2 - (
            selected.e1 - selected.e2
        ) / (saturation_ratio - 1.0)
        saturation_gain_value: float = (
            selected.se2 * selected.e2 * (saturation_ratio - 1.0) ** 2
            / (selected.e1 - selected.e2) ** 2
        )
        saturation_value: Expr = (
            sym.heaviside(field_voltage - saturation_start) * saturation_gain
            * (field_voltage - saturation_start) ** 2 / field_voltage
        )
        saturation_initial = (
            max(selected.ve0 - saturation_start_value, 0.0) ** 2
            * saturation_gain_value / selected.ve0
        )
    else:
        saturation_start = Const(0.0)
        saturation_gain = Const(0.0)
        saturation_value = Const(0.0)
        saturation_initial = 0.0

    saturation: Var = control.algebraic(
        'FieldSaturationPu', saturation_value, Const(saturation_initial),
    )
    feedback_expression: Expr = (
        (field_resistance + saturation) * field_voltage + demagnetizing * field_current
    )
    feedback_initial: float = (
        (selected.ke + saturation_initial) * selected.ve0 + selected.kd * selected.ifd0
    )
    if (selected.efe0 is not None
            and not math.isclose(selected.efe0, feedback_initial, rel_tol=1e-9, abs_tol=1e-9)):
        raise ValueError('AC9C initial EFE must balance field feedback')
    else:
        pass
    initial_efe: float = feedback_initial if selected.efe0 is None else selected.efe0
    control.block.init_eqs[field_voltage_input] = Const(initial_efe)
    feedback: Var = control.algebraic(
        'VFEpu', feedback_expression, Const(feedback_initial),
    )
    upper_field_voltage: Expr = (
        field_maximum - demagnetizing * field_current
    ) / (field_resistance + saturation)
    upper_initial: float = (
        selected.vfemax - selected.kd * selected.ifd0
    ) / (selected.ke + saturation_initial)
    if upper_initial < selected.vemin or selected.ve0 > upper_initial:
        raise ValueError('AC9C initial exciter voltage exceeds its dynamic field limit')
    else:
        pass
    control.differential(
        field_voltage, (field_voltage_input - feedback) / field_time,
        Const(selected.ve0), field_minimum, upper_field_voltage,
    )

    normalized_current: Expr = sym.safe_divide(
        loading * field_current, field_voltage, Const(1.0),
    )
    rectifier_factor: Expr = _esst3a_fex(normalized_current)
    field_output_initial: Expr = Const(selected.ve0) * _esst3a_fex(
        Const(selected.kc * selected.ifd0 / selected.ve0),
    )
    field_output: Var = control.algebraic(
        'EFDPu', field_voltage * rectifier_factor, field_output_initial,
    )
    return control.finish(
        (field_output, feedback, field_voltage),
        'AC9C rotating exciter with saturation, demagnetizing feedback and rectifier regulation',
    )
