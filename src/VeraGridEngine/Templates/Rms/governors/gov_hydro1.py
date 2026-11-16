# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES GovHydro1 mechanical-hydraulic governor."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class GovHydro1Parameters:
    """CGMES GovHydro1 governor, actuator, and water-column settings."""

    __slots__ = (
        'mwbase', 'rperm', 'rtemp', 'tr', 'tf', 'tg', 'velm', 'gmax', 'gmin',
        'tw', 'at', 'dturb', 'qnl', 'hdam',
    )

    def __init__(
            self,
            mwbase: float = 100.0,
            rperm: float = 0.05,
            rtemp: float = 0.3,
            tr: float = 5.0,
            tf: float = 0.05,
            tg: float = 0.5,
            velm: float = 0.2,
            gmax: float = 1.0,
            gmin: float = 0.0,
            tw: float = 1.0,
            at: float = 1.0,
            dturb: float = 0.0,
            qnl: float = 0.08,
            hdam: float = 1.0,
    ) -> None:
        """Store the imported coefficients in their CGMES units.

        :param mwbase: Governor power base in MW.
        :param rperm: Permanent speed droop in per unit.
        :param rtemp: Temporary speed droop in per unit.
        :param tr: Transient-droop reset time in seconds.
        :param tf: Governor measurement-filter time in seconds.
        :param tg: Gate-servo time in seconds.
        :param velm: Symmetric gate rate limit in per unit per second.
        :param gmax: Maximum gate opening in per unit.
        :param gmin: Minimum gate opening in per unit.
        :param tw: Water-column time in seconds.
        :param at: Turbine gain in per unit.
        :param dturb: Turbine speed damping normalized to ``mwbase`` in per unit.
        :param qnl: No-load flow in per unit.
        :param hdam: Dam head in per unit.
        """
        self.mwbase: float = mwbase
        self.rperm: float = rperm
        self.rtemp: float = rtemp
        self.tr: float = tr
        self.tf: float = tf
        self.tg: float = tg
        self.velm: float = velm
        self.gmax: float = gmax
        self.gmin: float = gmin
        self.tw: float = tw
        self.at: float = at
        self.dturb: float = dturb
        self.qnl: float = qnl
        self.hdam: float = hdam


def build_gov_hydro1_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: GovHydro1Parameters | None = None,
) -> RmsModelTemplate:
    """Build the HYGOV-style controller and nonlinear water-column equations.

    The filtered speed error passes through the CGMES temporary-droop PI path,
    rate-limited gate demand, gate servo, and inelastic water-column relation.
    The hydraulic equilibrium uses ``head=hdam`` and ``flow=gate*sqrt(hdam)``.
    Zero ``T_G`` and ``T_W`` reduce the associated stages algebraically.

    :param vfactory: Factory owning this template's symbolic variables.
    :param name: Optional unique runtime name.
    :param parameters: Parsed CGMES values selecting coefficients and bases.
    :return: Executable CGMES GovHydro1 template with speed and reference inputs.
    :raises ValueError: Invalid or nonphysical parameters.
    """
    settings: GovHydro1Parameters = (
        GovHydro1Parameters() if parameters is None else parameters
    )
    numeric_values: tuple[float, ...] = (
        settings.mwbase, settings.rperm, settings.rtemp, settings.tr,
        settings.tf, settings.tg, settings.velm, settings.gmax, settings.gmin,
        settings.tw, settings.at, settings.dturb, settings.qnl, settings.hdam,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('GovHydro1 parameters must be finite')
    elif settings.mwbase <= 0.0 or settings.rtemp <= 0.0 or settings.tr <= 0.0:
        raise ValueError('GovHydro1 requires positive MWBASE, RTEMP, and TR')
    elif settings.tf <= 0.0 or settings.velm <= 0.0 or settings.at <= 0.0:
        raise ValueError('GovHydro1 requires positive TF, VELM, and AT')
    elif settings.tg < 0.0 or settings.tw < 0.0:
        raise ValueError('GovHydro1 TG and TW must be nonnegative')
    elif settings.rperm < 0.0 or settings.dturb < 0.0 or settings.qnl < 0.0:
        raise ValueError('GovHydro1 droop, damping, and no-load flow must be nonnegative')
    elif settings.gmin < 0.0 or settings.gmax <= settings.gmin or settings.hdam <= 0.0:
        raise ValueError('GovHydro1 requires ordered nonnegative gates and positive HDAM')
    else:
        pass

    template_name: str = 'GovHydro1' if name is None else name
    control: ControlRealization = ControlRealization(vfactory, template_name)

    # Keep runtime coefficients editable and dimensioned in the RDF units.
    rperm: Var = control.parameter('GovHydro1.rperm', settings.rperm)
    rtemp: Var = control.parameter('GovHydro1.rtemp', settings.rtemp)
    tr: Var = control.parameter('GovHydro1.tr', settings.tr)
    tf: Var = control.parameter('GovHydro1.tf', settings.tf)
    tg: Var = control.parameter('GovHydro1.tg', settings.tg)
    velm: Var = control.parameter('GovHydro1.velm', settings.velm)
    gmax: Var = control.parameter('GovHydro1.gmax', settings.gmax)
    gmin: Var = control.parameter('GovHydro1.gmin', settings.gmin)
    tw: Var = control.parameter('GovHydro1.tw', settings.tw)
    at: Var = control.parameter('GovHydro1.at', settings.at)
    dturb: Var = control.parameter('DTurbGovernorBasePu', settings.dturb)
    qnl: Var = control.parameter('GovHydro1.qnl', settings.qnl)
    hdam: Var = control.parameter('GovHydro1.hdam', settings.hdam)
    control.parameter('GovHydro1.mwbase', settings.mwbase)

    # The host supplies absolute machine speed and the speed-domain setpoint.
    speed: Var = control.input('OmegaPu', Const(1.0))
    initial_gate: float = (
        settings.qnl + 0.5 / (settings.at * math.sqrt(settings.hdam))
    ) / math.sqrt(settings.hdam)
    initial_gate = min(max(initial_gate, settings.gmin), settings.gmax)
    reference: Var = control.input(
        'PRefPu', Const(settings.rperm * initial_gate),
    )
    speed_deviation: Var = control.algebraic(
        'SpeedDeviationPu', speed - Const(1.0), Const(0.0),
    )

    # Filter the governor error before applying the reset PI characteristic.
    gate: Var = vfactory.add_var(f'GateOpeningPu_{template_name}')
    error: Var = control.lag(
        'FilteredSpeedErrorPu',
        reference - speed_deviation - rperm * gate,
        tf,
        settings.tf,
        Const(0.0),
    )
    error_derivative: Expr = (
        reference - speed_deviation - rperm * gate - error
    ) / tf
    gate_velocity_command: Expr = (
        error_derivative + error / tr
    ) / rtemp
    desired_gate: Var = control.differential(
        vfactory.add_var(f'DesiredGateOpeningPu_{template_name}'),
        sym.hard_sat(gate_velocity_command, -velm, velm),
        Const(initial_gate),
        gmin,
        gmax,
    )
    if settings.tg > 0.0:
        control.differential(
            gate,
            (desired_gate - gate) / tg,
            Const(initial_gate),
            gmin,
            gmax,
        )
    else:
        control.block.algebraic_vars.append(gate)
        control.block.algebraic_eqs.append(
            gate - sym.hard_sat(desired_gate, gmin, gmax)
        )
        control.block.init_eqs[gate] = Const(initial_gate)

    # The flow/head states preserve the nonlinear inverse response; at TW=0,
    # steady dam head gives the exact static flow relation.
    flow: Var = vfactory.add_var(f'TurbineFlowPu_{template_name}')
    head: Var = control.algebraic(
        'TurbineHeadPu',
        sym.safe_divide(flow, gate, hdam ** Const(0.5)) ** Const(2.0),
        Const(settings.hdam),
    )
    if settings.tw > 0.0:
        control.differential(
            flow,
            (hdam - head) / tw,
            Const(initial_gate * math.sqrt(settings.hdam)),
        )
    else:
        control.block.algebraic_vars.append(flow)
        control.block.algebraic_eqs.append(
            flow - gate * (hdam ** Const(0.5))
        )
        control.block.init_eqs[flow] = Const(initial_gate * math.sqrt(settings.hdam))

    mechanical_power: Var = control.algebraic(
        'PmPu',
        at * (flow - qnl) * head - dturb * (speed - Const(1.0)),
        Const(0.5),
    )
    runtime: RmsModelTemplate = control.finish(
        (mechanical_power,),
        'CGMES GovHydro1 speed governor and nonlinear hydro turbine',
    )

    # Retain each canonical RDF field as a named event for importer edits.
    template: RmsModelTemplate = RmsModelTemplate(name=template_name)
    template.block.children.append(runtime.block)
    template.block.name = template_name
    template.comment = 'CGMES GovHydro1 equations with nonlinear dam-head dynamics.'
    for parameter_name in (
            'enabled', 'mwbase', 'rperm', 'rtemp', 'tr', 'tf', 'tg', 'velm',
            'gmax', 'gmin', 'tw', 'at', 'dturb', 'qnl', 'hdam',
    ):
        parameter_variable: Var = vfactory.add_var(
            f'GovHydro1.{parameter_name}_{template_name}'
        )
        template.block.event_dict[parameter_variable] = vfactory.add_const(
            value=None, name=parameter_variable.name,
        )
    return template
