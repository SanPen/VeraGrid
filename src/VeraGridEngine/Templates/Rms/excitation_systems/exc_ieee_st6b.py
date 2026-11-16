# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed template for the CGMES ExcIEEEST6B exciter."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.IO.cim.cgmes.dynamics.schema import ExcST6BOELselectorKind
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


def build_exc_i_e_e_e_s_t6_b_template(
        vfactory: VarFactory,
        name: str | None = None,
        ilr: float = 4.164,
        kci: float = 1.0577,
        kff: float = 1.0,
        kg: float = 1.0,
        kia: float = 45.094,
        klr: float = 17.33,
        km: float = 1.0,
        kpa: float = 18.038,
        oelin: ExcST6BOELselectorKind = ExcST6BOELselectorKind.noOELinput,
        tg: float = 0.02,
        vamax: float = 4.81,
        vamin: float = -3.85,
        vrmax: float = 4.81,
        vrmin: float = -3.85,
) -> RmsModelTemplate:
    """Build the IEEE 421.5-2005 ST6B PI and inner field-regulator graph.

    :param vfactory: Symbol factory for this instance.
    :param name: Optional unique instance name.
    :param ilr: Exciter output current limiter reference.
    :param kci: Exciter output current limit adjustment gain.
    :param kff: Inner-loop pre-control gain.
    :param kg: Inner-loop field-voltage feedback gain.
    :param kia: Voltage regulator integral gain.
    :param klr: Exciter output current limiter gain.
    :param km: Inner-loop forward gain.
    :param kpa: Voltage regulator proportional gain.
    :param oelin: OEL insertion point relative to the UEL gate.
    :param tg: Inner-loop feedback time constant.
    :param vamax: PI regulator upper limit.
    :param vamin: PI regulator lower limit.
    :param vrmax: Exciter regulator upper limit.
    :param vrmin: Exciter regulator lower limit.
    :return: Equation graph retaining the canonical ExcIEEEST6B RDF properties.
    """
    if all((
            math.isfinite(ilr), math.isfinite(kci), math.isfinite(kff),
            math.isfinite(kg), math.isfinite(kia), math.isfinite(klr),
            math.isfinite(km), math.isfinite(kpa), math.isfinite(tg),
            math.isfinite(vamax), math.isfinite(vamin), math.isfinite(vrmax),
            math.isfinite(vrmin),
    )) is False:
        raise ValueError('ExcIEEEST6B parameters must be finite')
    elif min(ilr, kci, kff, kg, kia, klr, km, kpa, tg) < 0.0:
        raise ValueError('ExcIEEEST6B gains and time constants must be nonnegative')
    elif vamax <= vamin or vrmax <= vrmin:
        raise ValueError('ExcIEEEST6B limiter bounds must be ordered')
    else:
        pass
    template_name: str = 'ExcIEEEST6B' if name is None else name
    builder: ControlRealization = ControlRealization(vfactory, template_name)
    # Keep the exact RDF names on the coefficient events for round-trip inspection.
    ilr_event: Var = builder.parameter('ExcIEEEST6B.ilr', ilr)
    kci_event: Var = builder.parameter('ExcIEEEST6B.kci', kci)
    kff_event: Var = builder.parameter('ExcIEEEST6B.kff', kff)
    kg_event: Var = builder.parameter('ExcIEEEST6B.kg', kg)
    kia_event: Var = builder.parameter('ExcIEEEST6B.kia', kia)
    klr_event: Var = builder.parameter('ExcIEEEST6B.klr', klr)
    km_event: Var = builder.parameter('ExcIEEEST6B.km', km)
    kpa_event: Var = builder.parameter('ExcIEEEST6B.kpa', kpa)
    tg_event: Var = builder.parameter('ExcIEEEST6B.tg', tg)
    vamax_event: Var = builder.parameter('ExcIEEEST6B.vamax', vamax)
    vamin_event: Var = builder.parameter('ExcIEEEST6B.vamin', vamin)
    vrmax_event: Var = builder.parameter('ExcIEEEST6B.vrmax', vrmax)
    vrmin_event: Var = builder.parameter('ExcIEEEST6B.vrmin', vrmin)
    if oelin == ExcST6BOELselectorKind.noOELinput:
        oelin_code: float = 0.0
    elif oelin == ExcST6BOELselectorKind.beforeUEL:
        oelin_code = 1.0
    else:
        oelin_code = 2.0
    oelin_event: Var = builder.parameter('ExcIEEEST6B.oelin', oelin_code)
    # Inputs remain open for association to the machine and limiter/PSS records.
    terminal_voltage: Var = builder.input('UsPu', Const(1.0))
    reference: Var = builder.input('UsRefPu', Const(1.0))
    stabilizer: Var = builder.input('VsPu', Const(0.0))
    oel: Var = builder.input('OelPu', Const(0.0))
    uel: Var = builder.input('UelPu', Const(0.0))
    field_current: Var = builder.input('IfdPu', Const(1.0))
    available_supply: Var = builder.input('VbPu', Const(1.0))
    # Apply the two excitation-limit gates in the order selected by the RDF enum.
    raw_error: Expr = reference + stabilizer - terminal_voltage
    if oelin == ExcST6BOELselectorKind.beforeUEL:
        oel_limited_error: Expr = sym.min(raw_error, oel)
        voltage_error: Expr = sym.max(oel_limited_error, uel)
    elif oelin == ExcST6BOELselectorKind.afterUEL:
        uel_limited_error: Expr = sym.max(raw_error, uel)
        voltage_error = sym.min(uel_limited_error, oel)
    else:
        voltage_error = sym.max(raw_error, uel)
    integral: Var = vfactory.add_var(f'VoltageIntegralPu_{template_name}')
    regulator_integral: Var = builder.differential(
        integral,
        kia_event * voltage_error,
        Const(0.0),
        vamin_event - kpa_event * voltage_error,
        vamax_event - kpa_event * voltage_error,
    )
    regulator_output: Var = builder.algebraic(
        'PIDOutputPu',
        sym.hard_sat(kpa_event * voltage_error + regulator_integral, vamin_event, vamax_event),
        Const(0.0),
    )
    # The inner loop pre-control and feedback produce the bounded exciter demand.
    field_output: Var = vfactory.add_var(f'EfdPu_{template_name}')
    feedback: Var = vfactory.add_var(f'FieldFeedbackPu_{template_name}')
    feedback_output: Var = builder.lag(
        'FeedbackPu', kg_event * field_output, tg_event, tg, Const(0.0), output=feedback,
    )
    inner_demand: Expr = (regulator_output - feedback_output) * km_event + regulator_output * kff_event
    voltage_limited: Expr = sym.hard_sat(inner_demand, vrmin_event, vrmax_event)
    current_limited: Expr = sym.max(
        (ilr_event * kci_event - field_current) * klr_event,
        vrmin_event,
    )
    exciter_regulator: Var = builder.algebraic(
        'RegulatorPu', sym.min(voltage_limited, current_limited), Const(0.0),
    )
    # VB is an explicit available-supply port in the IEEE ST6B diagram.
    field_demand: Expr = exciter_regulator * available_supply
    builder.block.algebraic_vars.append(field_output)
    builder.block.algebraic_eqs.append(field_output - field_demand)
    builder.block.init_eqs[field_output] = Const(1.0)
    field: Var = field_output
    template: RmsModelTemplate = builder.finish(
        (field, exciter_regulator),
        'CGMES ExcIEEEST6B PI regulator with inner feedback, pre-control, and current limiting',
    )
    return template
