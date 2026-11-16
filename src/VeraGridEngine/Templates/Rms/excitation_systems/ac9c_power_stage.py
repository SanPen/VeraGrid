# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""AC9C selected controlled-rectifier power-stage logic."""
from __future__ import annotations

from enum import Enum
import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class Ac9cPowerStageType(Enum):
    """Select the thyristor-bridge or chopper power stage."""

    THYRISTOR_BRIDGE = 1
    CHOPPER = 2


def ac9c_power_stage_type_from_psse(sct: float) -> Ac9cPowerStageType:
    """Translate the PSS/E SCT selector to the native power-stage choice.

    PSS/E 35.2 Model Library §6.14 specifies nonzero SCT for the thyristor
    bridge and zero SCT for the chopper converter.

    :param sct: Source model SCT value.
    :return: Native power-stage selection.
    :raises ValueError: The source selector is not finite.
    """
    if not math.isfinite(sct):
        raise ValueError('AC9C SCT selector must be finite')
    elif sct != 0.0:
        return Ac9cPowerStageType.THYRISTOR_BRIDGE
    else:
        return Ac9cPowerStageType.CHOPPER


def build_ac9c_power_stage_template(
        vf: VarFactory,
        name: str = 'AC9C power stage',
        stage_type: Ac9cPowerStageType = Ac9cPowerStageType.THYRISTOR_BRIDGE,
        vlim1: float = 0.0,
        vlim2: float = -0.1,
) -> RmsModelTemplate:
    """Build the documented AC9C thyristor/chopper selection logic.

    The thyristor bridge passes ``VCT`` as regulator output ``VR``. The
    chopper passes ``VCT`` above ``VLIM1``, blocks output between the limits,
    and applies ``-VFW`` at or below ``VLIM2``. The strict source comparisons
    are preserved at both thresholds.

    :param vf: Symbol factory owning this component's equations.
    :param name: Unique component label.
    :param stage_type: Selected bridge or chopper structure.
    :param vlim1: Upper chopper stage threshold, per unit.
    :param vlim2: Lower chopper stage threshold, per unit.
    :return: Stateless AC9C power-stage logic with output ``VR``.
    :raises ValueError: Thresholds are nonfinite, unordered or selection invalid.
    """
    if not isinstance(stage_type, Ac9cPowerStageType):
        raise ValueError('AC9C power-stage selection is invalid')
    elif not math.isfinite(vlim1) or not math.isfinite(vlim2):
        raise ValueError('AC9C power-stage thresholds must be finite')
    elif vlim1 <= vlim2:
        raise ValueError('AC9C requires VLIM1 greater than VLIM2')
    else:
        pass

    control: ControlRealization = ControlRealization(vf, name)
    upper: Var = control.parameter('VLIM1', vlim1)
    lower: Var = control.parameter('VLIM2', vlim2)
    converter_voltage: Var = control.input('VCTPu', Const(0.0))
    freewheel_voltage: Var = control.input('VFWPu', Const(0.0))
    regulator_output: Var = control.input('VAVRPu', Const(0.0))
    if stage_type is Ac9cPowerStageType.THYRISTOR_BRIDGE:
        output_expression: Expr = converter_voltage
    else:
        above_upper: Expr = sym.heaviside(regulator_output - upper)
        above_lower: Expr = sym.heaviside(regulator_output - lower)
        output_expression = (above_upper * converter_voltage
                             - (Const(1.0) - above_lower) * freewheel_voltage)
    output: Var = control.algebraic('VRPu', output_expression, Const(0.0))
    template: RmsModelTemplate = control.finish((output,), 'AC9C bridge/chopper power-stage logic')
    return template
