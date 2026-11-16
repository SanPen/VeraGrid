# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Four-phase dual-input damping with limited measurements and explicitly ordered ramp tracking."""
from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.power_system_stabilizers.ramp_tracking_stabilizer import RampStabilizerKind, RampStabilizerParameters, StabilizerInterface, build_ramp_tracking_stabilizer
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.procedural_logic import PickupDropoffLogic
from VeraGridEngine.Utils.Symbolic.symbolic import Comparison, CmpOp, Const, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


def build_pss2c_template(vf: VarFactory, name: str | None = None,
                          parameters: RampStabilizerParameters | None = None,
                          interface: StabilizerInterface = StabilizerInterface.SHAFT_SPEED_POWER,
                          pss_on: float = -1.0, pss_off: float = 0.0) -> RmsModelTemplate:
    """Build four-phase dual-input damping with continuously enabled output.

    Independently limited measurements pass through paired washouts and optional
    transducers. With conditioned paths A and B, including the second-path gain,
    ramp tracking produces ``R*(A+KS3*B)-B``, where
    ``R=[(1+s*T8)/(1+s*T9)**M]**N``. Four independent lead/lag compensators shape
    the gained signal before supplementary-voltage clipping. Ramp order selects
    exactly M*N memories; zero M or N bypasses that filter. Zero second washouts,
    transducer times and proper zero-time phase pairs are exact bypasses.

    This continuous construction requires positive first-washout times on both
    paths, yielding zero supplementary output at any constant operating point.
    Optional PSSON/PSSOFF settings add the documented electrical-power output
    hysteresis. Compensated frequency still requires a separate measurement
    realization. Output clipping does not freeze any filter memory.

    Default ports preserve absolute shaft speed, its reference and electrical
    power; the selected-measurement interface exposes two host-scaled signals.
    Output is per-unit supplementary excitation voltage. All times use seconds;
    the host owns measurement selection and electrical power bases.

    :param vf: Shared native symbolic variable factory.
    :param name: Optional unique instance label.
    :param parameters: Washout, ramp, four-phase and limiter coefficients.
    :param interface: Selected measurements or shaft/reference/power input ports.
    :param pss_on: Positive machine-base electrical-power threshold enabling the output logic; negative disables it.
    :param pss_off: Lower machine-base electrical-power threshold disabling the output logic.
    :return: Native dual-input damping controller, optionally power gated.
    :raises ValueError: Invalid physical coefficients, limits or improper stages.
    """
    template: RmsModelTemplate = build_ramp_tracking_stabilizer(vf,'PSS2C' if name is None else name,
        RampStabilizerKind.LIMITED_FOUR_PHASE,parameters,interface)
    if not math.isfinite(pss_on) or not math.isfinite(pss_off):
        raise ValueError('PSS2C output thresholds must be finite')
    elif pss_on < 0.0 or (pss_on == 0.0 and pss_off == 0.0):
        return template
    elif pss_on <= 0.0 or pss_off >= pss_on:
        raise ValueError('Enabled PSS2C logic requires PSSON > 0 and PSSOFF < PSSON')
    else:
        pass
    block: Block = template.block
    power: Var = vf.add_var('GeneratorActivePowerPu_' + block.name)
    enabled: Var = vf.add_var('PssOutputEnabled_' + block.name)
    block.in_vars.append(power)
    block.mode_dict[enabled] = Comparison(power, CmpOp.GE, Const(pss_on)).to_expression()
    enable_if_off: sym.Expr = Comparison(power, CmpOp.GE, Const(pss_on)).to_expression()
    remain_on: sym.Expr = Comparison(power, CmpOp.GT, Const(pss_off)).to_expression()
    condition: sym.Expr = (Const(1.0) - enabled) * enable_if_off + enabled * remain_on
    block.init_eqs[enabled] = enable_if_off
    block.procedural_logic.append(PickupDropoffLogic(
        output_var_name=enabled.name, bool_expr=condition,
        pickup_delay_expr=Const(0.0), drop_delay_expr=Const(0.0),
        name='PSS2C electrical-power output hysteresis ' + block.name,
    ))
    source_output: Var = block.out_vars[0]
    gated_output: Var = vf.add_var('VsPuWithPowerLogic_' + block.name)
    block.algebraic_vars.append(gated_output)
    block.algebraic_eqs.append(gated_output - source_output * enabled)
    block.init_eqs[gated_output] = source_output * enable_if_off
    block.out_vars[0] = gated_output
    return template
