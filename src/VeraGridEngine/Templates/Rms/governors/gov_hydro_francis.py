# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES GovHydroFrancis governor and turbine."""

import math
from enum import Enum

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class GovHydroFrancisControlKind(Enum):
    """Standalone equation selector corresponding to the canonical RDF enum."""

    mechanicHydrolicTachoAccelerator = 'mechanicHydrolicTachoAccelerator'
    mechanicHydraulicTransientFeedback = 'mechanicHydraulicTransientFeedback'
    electromechanicalElectrohydraulic = 'electromechanicalElectrohydraulic'


class GovHydroFrancisParameters:
    """CGMES Francis governor and hydraulic plant coefficients."""

    __slots__ = (
        'am', 'av0', 'av1', 'bp', 'db1', 'etamax', 'governor_control',
        'h1', 'h2', 'hn', 'kc', 'kg', 'kt', 'qc0', 'qn', 'ta', 'td',
        'ts', 'twnc', 'twng', 'tx', 'va', 'valvmax', 'valvmin', 'vc',
        'waterway_enabled', 'zsfc', 'nominal_frequency',
    )

    def __init__(
            self,
            am: float = 0.7,
            av0: float = 30.0,
            av1: float = 700.0,
            bp: float = 0.05,
            db1: float = 0.0,
            etamax: float = 1.05,
            governor_control: GovHydroFrancisControlKind = GovHydroFrancisControlKind.mechanicHydrolicTachoAccelerator,
            h1: float = 4.0,
            h2: float = 40.0,
            hn: float = 250.0,
            kc: float = 0.025,
            kg: float = 0.025,
            kt: float = 0.25,
            qc0: float = 0.1,
            qn: float = 250.0,
            ta: float = 3.0,
            td: float = 6.0,
            ts: float = 0.5,
            twnc: float = 1.0,
            twng: float = 3.0,
            tx: float = 1.0,
            va: float = 0.06,
            valvmax: float = 1.1,
            valvmin: float = 0.0,
            vc: float = -0.06,
            waterway_enabled: bool = False,
            zsfc: float = 25.0,
            nominal_frequency: float = 50.0,
    ) -> None:
        """Store coefficients in SI units except dimensionless pu values.

        :param am: Gate opening at maximum efficiency, pu.
        :param av0: Surge-tank area, m2.
        :param av1: Compensation-chamber area, m2.
        :param bp: Permanent droop, pu.
        :param db1: Speed deadband, Hz.
        :param etamax: Maximum turbine efficiency, pu.
        :param governor_control: Canonical three-way governor selector.
        :param h1: Compensation-chamber level, m.
        :param h2: Surge-tank level, m.
        :param hn: Rated hydraulic head, m.
        :param kc: Penstock friction loss coefficient, pu.
        :param kg: Tunnel friction loss coefficient, pu.
        :param kt: Transient governor feedback gain, pu.
        :param qc0: No-load turbine flow, pu.
        :param qn: Rated flow, m3/s.
        :param ta: Speed acceleration gain, seconds.
        :param td: Transient feedback time, seconds.
        :param ts: Gate servo time, seconds.
        :param twnc: Penstock water inertia time, seconds.
        :param twng: Tunnel water inertia time, seconds.
        :param tx: Gate derivative feedback time, seconds.
        :param va: Maximum gate opening rate, pu/s.
        :param valvmax: Maximum gate travel, pu.
        :param valvmin: Minimum gate travel, pu.
        :param vc: Minimum gate closing rate, pu/s; normally negative.
        :param waterway_enabled: Select detailed tunnel and surge model.
        :param zsfc: Upper reservoir head above penstock, m.
        :param nominal_frequency: System frequency for Hz to pu conversion.
        """
        self.am: float = am
        self.av0: float = av0
        self.av1: float = av1
        self.bp: float = bp
        self.db1: float = db1
        self.etamax: float = etamax
        self.governor_control: GovHydroFrancisControlKind = governor_control
        self.h1: float = h1
        self.h2: float = h2
        self.hn: float = hn
        self.kc: float = kc
        self.kg: float = kg
        self.kt: float = kt
        self.qc0: float = qc0
        self.qn: float = qn
        self.ta: float = ta
        self.td: float = td
        self.ts: float = ts
        self.twnc: float = twnc
        self.twng: float = twng
        self.tx: float = tx
        self.va: float = va
        self.valvmax: float = valvmax
        self.valvmin: float = valvmin
        self.vc: float = vc
        self.waterway_enabled: bool = waterway_enabled
        self.zsfc: float = zsfc
        self.nominal_frequency: float = nominal_frequency


def build_gov_hydro_francis_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: GovHydroFrancisParameters | None = None,
) -> RmsModelTemplate:
    """Build the Francis governor, turbine, and optional detailed waterway.

    The three control branches follow the local NEPLAN diagram and IEC
    parameter definitions. Waterway head and efficiency use the IEC nonlinear
    characteristics. The output ``PmPu`` is on turbine capability base.

    :param vfactory: Factory owning symbolic model variables.
    :param name: Optional unique template instance name.
    :param parameters: RDF-converted CGMES coefficients.
    :return: Executable standalone CGMES governor/turbine template.
    :raises ValueError: Invalid control selector, bases, times, or limits.
    """
    settings: GovHydroFrancisParameters = (
        GovHydroFrancisParameters() if parameters is None else parameters
    )
    parameter_values: tuple[float, ...] = (
        settings.am, settings.av0, settings.av1, settings.bp, settings.db1,
        settings.etamax, settings.h1, settings.h2, settings.hn, settings.kc,
        settings.kg, settings.kt, settings.qc0, settings.qn, settings.ta,
        settings.td, settings.ts, settings.twnc, settings.twng, settings.tx,
        settings.va, settings.valvmax, settings.valvmin, settings.vc,
        settings.zsfc, settings.nominal_frequency,
    )
    if not all(math.isfinite(value) for value in parameter_values):
        raise ValueError('GovHydroFrancis parameters must be finite')
    elif not isinstance(settings.governor_control, GovHydroFrancisControlKind):
        raise ValueError('GovHydroFrancis requires a declared control selector')
    elif settings.hn <= 0.0 or settings.qn <= 0.0 or settings.nominal_frequency <= 0.0:
        raise ValueError('GovHydroFrancis requires positive hydraulic and frequency bases')
    elif min(settings.ta, settings.td, settings.ts, settings.twnc, settings.twng, settings.tx) < 0.0:
        raise ValueError('GovHydroFrancis time constants must be nonnegative')
    elif settings.bp < 0.0 or settings.db1 < 0.0 or settings.etamax < 0.0:
        raise ValueError('GovHydroFrancis droop, deadband, and efficiency must be nonnegative')
    elif settings.valvmin >= settings.valvmax or settings.va < 0.0 or settings.vc > 0.0:
        raise ValueError('GovHydroFrancis gate limits and rates are invalid')
    elif settings.am <= 0.0:
        raise ValueError('GovHydroFrancis AM must be positive for the efficiency curve')
    elif settings.waterway_enabled and min(settings.av0, settings.av1) <= 0.0:
        raise ValueError('The detailed Francis waterway requires positive chamber areas')
    elif settings.waterway_enabled and not 0.0 <= settings.h1 <= settings.h2:
        raise ValueError('The detailed Francis waterway requires 0 <= H1 <= H2')
    elif settings.waterway_enabled and min(settings.kc, settings.kg) < 0.0:
        raise ValueError('The detailed Francis waterway requires nonnegative losses')
    else:
        pass

    template_name: str = 'GovHydroFrancis' if name is None else name
    control: ControlRealization = ControlRealization(vfactory, template_name)
    bp: Var = control.parameter('GovHydroFrancis.bp', settings.bp)
    db1: Var = control.parameter('GovHydroFrancis.db1', settings.db1)
    am: Var = control.parameter('GovHydroFrancis.am', settings.am)
    etamax: Var = control.parameter('GovHydroFrancis.etamax', settings.etamax)
    kc: Var = control.parameter('GovHydroFrancis.kc', settings.kc)
    kg: Var = control.parameter('GovHydroFrancis.kg', settings.kg)
    kt: Var = control.parameter('GovHydroFrancis.kt', settings.kt)
    qc0: Var = control.parameter('GovHydroFrancis.qc0', settings.qc0)
    ta: Var = control.parameter('GovHydroFrancis.ta', settings.ta)
    td: Var = control.parameter('GovHydroFrancis.td', settings.td)
    ts: Var = control.parameter('GovHydroFrancis.ts', settings.ts)
    twnc: Var = control.parameter('GovHydroFrancis.twnc', settings.twnc)
    twng: Var = control.parameter('GovHydroFrancis.twng', settings.twng)
    tx: Var = control.parameter('GovHydroFrancis.tx', settings.tx)
    va: Var = control.parameter('GovHydroFrancis.va', settings.va)
    vc: Var = control.parameter('GovHydroFrancis.vc', settings.vc)
    valvmax: Var = control.parameter('GovHydroFrancis.valvmax', settings.valvmax)
    valvmin: Var = control.parameter('GovHydroFrancis.valvmin', settings.valvmin)
    h1_pu: float = settings.h1 / settings.hn
    h2_pu: float = settings.h2 / settings.hn
    zsfc_pu: float = settings.zsfc / settings.hn
    av0_pu: float = settings.av0 * settings.hn / settings.qn
    av1_pu: float = settings.av1 * settings.hn / settings.qn
    h1: Var = control.parameter('GovHydroFrancis.h1Pu', h1_pu)
    h2: Var = control.parameter('GovHydroFrancis.h2Pu', h2_pu)
    zsfc: Var = control.parameter('GovHydroFrancis.zsfcPu', zsfc_pu)
    av0: Var = control.parameter('GovHydroFrancis.av0Pu', av0_pu)
    av1: Var = control.parameter('GovHydroFrancis.av1Pu', av1_pu)

    # The source DB1 signal is the positive under-frequency deviation.
    speed: Var = control.input('OmegaPu', Const(1.0))
    speed_derivative: Var = control.input('OmegaDerivativePu', Const(0.0))
    power_reference: Var = control.input('PRefPu', Const(0.5))
    speed_deficit: Expr = Const(1.0) - speed
    deadband_pu: Expr = db1 / Const(settings.nominal_frequency)
    deadbanded_speed: Expr = (
        sym.max(speed_deficit - deadband_pu, Const(0.0))
        + sym.min(speed_deficit + deadband_pu, Const(0.0))
    )
    initial_gate: float = min(max(0.5, settings.valvmin), settings.valvmax)
    gate: Var = vfactory.add_var(f'GateOpeningPu_{template_name}')
    speed_regulation: Expr = bp * (power_reference + deadbanded_speed - gate)
    governor_command: Expr = speed_regulation

    if settings.governor_control == GovHydroFrancisControlKind.mechanicHydrolicTachoAccelerator:
        governor_command: Expr = speed_regulation - ta * speed_derivative
    elif settings.governor_control == GovHydroFrancisControlKind.mechanicHydraulicTransientFeedback:
        if settings.td > 0.0:
            transient_feedback: Var = control.washout(
                'TransientGateFeedbackPu', gate, td, settings.td, kt, Const(initial_gate),
            )
            governor_command = speed_regulation - transient_feedback
        else:
            pass
    else:
        pass
    if settings.governor_control == GovHydroFrancisControlKind.electromechanicalElectrohydraulic:
        governor_command = speed_regulation - ta * speed_derivative
        gate_rate_signal: Var = vfactory.add_var(f'GateCommandRatePu_{template_name}')
        gate_derivative_feedback: Expr = sym.hard_sat(
            tx * gate_rate_signal, vc * ts, va * ts,
        )
        governor_command = governor_command - gate_derivative_feedback
    else:
        pass

    # The 1/TS amplifier and the VA/VC limits precede the position integrator.
    if settings.ts > 0.0:
        gate_rate: Var = control.algebraic(
            'GateRatePuPerSecond',
            sym.hard_sat(governor_command / ts, vc, va),
            Const(0.0),
        )
    else:
        # A zero servo time leaves only the diagram's directional rate limits.
        gate_rate = control.algebraic(
            'GateRatePuPerSecond',
            sym.heaviside(governor_command) * va
            + sym.heaviside(-governor_command) * vc,
            Const(0.0),
        )
    if settings.governor_control == GovHydroFrancisControlKind.electromechanicalElectrohydraulic:
        control.block.algebraic_vars.append(gate_rate_signal)
        control.block.algebraic_eqs.append(gate_rate_signal - gate_rate)
        control.block.init_eqs[gate_rate_signal] = Const(0.0)
    else:
        pass
    control.differential(gate, gate_rate, Const(initial_gate), valvmin, valvmax)

    # The waterway uses the IEC area, level, and rated-flow/head bases.
    turbine_flow: Var = vfactory.add_var(f'TurbineFlowPu_{template_name}')
    turbine_head: Var = control.algebraic(
        'TurbineHeadPu', sym.safe_divide(turbine_flow, gate, Const(1.0)) ** Const(2.0),
        Const(1.0),
    )
    if settings.waterway_enabled:
        tunnel_flow: Var = vfactory.add_var(f'TunnelFlowPu_{template_name}')
        stored_water: Var = vfactory.add_var(f'SurgeWaterVolumePu_{template_name}')
        chamber_head: Var = control.algebraic(
            'SurgeChamberHeadPu',
            build_gov_hydro_francis_level(stored_water, h1, h2, av0, av1,
                                          h1_pu, h2_pu, av0_pu, av1_pu),
            Const(h2_pu),
        )
        tunnel_loss: Expr = kg * tunnel_flow * sym.abs(tunnel_flow)
        penstock_loss: Expr = kc * turbine_flow * sym.abs(turbine_flow)
        tunnel_head_error: Expr = zsfc - chamber_head - tunnel_loss
        penstock_head_error: Expr = chamber_head - turbine_head - penstock_loss
        if settings.twng == 0.0:
            control.block.algebraic_vars.append(tunnel_flow)
            control.block.algebraic_eqs.append(tunnel_head_error)
            control.block.init_eqs[tunnel_flow] = Const(0.5)
        else:
            control.differential(
                tunnel_flow, tunnel_head_error / twng, Const(0.5),
            )
        if settings.twnc == 0.0:
            control.block.algebraic_vars.append(turbine_flow)
            control.block.algebraic_eqs.append(penstock_head_error)
            control.block.init_eqs[turbine_flow] = Const(0.5)
        else:
            control.differential(
                turbine_flow, penstock_head_error / twnc, Const(0.5),
            )
        control.differential(
            stored_water, tunnel_flow - turbine_flow,
            Const(
                h1_pu * av1_pu + (h2_pu - h1_pu) * av0_pu
            ),
        )
        efficiency_input: Expr = gate
    else:
        pass
    if not settings.waterway_enabled:
        penstock_head_error = Const(1.0) - turbine_head - kc * turbine_flow * sym.abs(turbine_flow)
        if settings.twnc == 0.0:
            control.block.algebraic_vars.append(turbine_flow)
            control.block.algebraic_eqs.append(penstock_head_error)
            control.block.init_eqs[turbine_flow] = Const(0.5)
        else:
            control.differential(
                turbine_flow, penstock_head_error / twnc, Const(0.5),
            )
        efficiency_input = gate
    else:
        pass

    # IEC Figure 72 efficiency characteristic, clipped to its real domain.
    efficiency_radicand: Expr = Const(4.0) - (efficiency_input / am - Const(1.0)) ** Const(2.0)
    efficiency: Var = control.algebraic(
        'TurbineEfficiencyPu',
        sym.max(Const(0.0), etamax * (sym.sqrt(sym.max(efficiency_radicand, Const(0.0))) - Const(1.0))),
        Const(settings.etamax * (math.sqrt(max(0.0, 4.0 - (initial_gate / settings.am - 1.0) ** 2)) - 1.0)),
    )
    hydraulic_power: Expr = efficiency * (turbine_flow - qc0) * turbine_head
    mechanical_power: Var = control.algebraic(
        'PmPu', hydraulic_power, Const(0.5),
    )
    runtime: RmsModelTemplate = control.finish(
        (mechanical_power,), 'CGMES GovHydroFrancis governor and nonlinear hydraulic turbine.',
    )

    # Keep every canonical RDF scalar visible as a standalone parameter event.
    parameter_template: RmsModelTemplate = RmsModelTemplate(name=template_name)
    parameter_template.block.children.append(runtime.block)
    parameter_template.block.name = template_name
    parameter_template.comment = runtime.comment
    for parameter_name in (
            'enabled', 'am', 'av0', 'av1', 'bp', 'db1', 'etamax',
            'governorControl', 'h1', 'h2', 'hn', 'kc', 'kg', 'kt', 'qc0',
            'qn', 'ta', 'td', 'ts', 'twnc', 'twng', 'tx', 'va', 'valvmax',
            'valvmin', 'vc', 'waterTunnelSurgeChamberSimulation', 'zsfc',
    ):
        parameter_variable: Var = vfactory.add_var(
            f'GovHydroFrancis.{parameter_name}_{template_name}'
        )
        parameter_template.block.event_dict[parameter_variable] = vfactory.add_const(
            value=None, name=parameter_variable.name,
        )
    return parameter_template


def build_gov_hydro_francis_level(
        stored_water: Expr,
        h1: Var,
        h2: Var,
        av0: Var,
        av1: Var,
        h1_value: float,
        h2_value: float,
        av0_value: float,
        av1_value: float,
) -> Expr:
    """Build the IEC two-area nonlinear surge-chamber level characteristic.

    :param stored_water: Integrated water-volume signal in pu units.
    :param h1: Compensation-chamber knee, pu head.
    :param h2: Surge-tank upper knee, pu head.
    :param av0: Upper chamber area in the IEC Qn/Hn base.
    :param av1: Lower chamber area in the IEC Qn/Hn base.
    :param h1_value: Numeric H1 construction value.
    :param h2_value: Numeric H2 construction value.
    :param av0_value: Numeric AV0 construction value.
    :param av1_value: Numeric AV1 construction value.
    :return: Continuous piecewise-linear IEC NL1 output.
    """
    w1: Expr = h1 * av1
    w2: Expr = w1 + (h2 - h1) * av0
    lower_branch: Expr = sym.safe_divide(stored_water, av1, Const(1.0))
    middle_branch: Expr = h1 + sym.safe_divide(stored_water - w1, av0, Const(1.0))
    if h1_value * av1_value >= 0.0 and h2_value >= h1_value and av0_value > 0.0:
        lower_weight: Expr = Const(1.0) - sym.heaviside(stored_water - w1)
        middle_weight: Expr = sym.heaviside(stored_water - w1) - sym.heaviside(stored_water - w2)
        upper_weight: Expr = sym.heaviside(stored_water - w2)
        return lower_weight * lower_branch + middle_weight * middle_branch + upper_weight * h2
    else:
        return Const(h2_value)


def get_gov_hydro_francis_steady_state(
        settings: GovHydroFrancisParameters,
        target_power: float,
) -> tuple[float, float, float, float, float, float, float, float] | None:
    """Invert the Francis turbine law at a requested pu power.

    :param settings: Converted Francis parameter set.
    :param target_power: Generator mechanical power on turbine capability base.
    :return: Gate, turbine flow/head/efficiency/power, tunnel flow, chamber
        storage, and chamber head; ``None`` if no feasible gate reproduces power.
    """
    lower_gate: float = settings.valvmin
    upper_gate: float = settings.valvmax
    best_gate: float = lower_gate
    best_error: float = math.inf
    bracket_lower: float | None = None
    bracket_upper: float | None = None
    previous_gate: float | None = None
    previous_error: float | None = None
    for sample_index in range(1001):
        gate_value: float = lower_gate + (upper_gate - lower_gate) * sample_index / 1000.0
        operating_point: tuple[float, float, float, float, float, float, float] | None = (
            get_gov_hydro_francis_point_at_gate(settings, gate_value)
        )
        if operating_point is not None:
            power_value: float = operating_point[3]
            error_value: float = power_value - target_power
            if abs(error_value) < best_error:
                best_gate = gate_value
                best_error = abs(error_value)
            else:
                pass
            if (
                    previous_gate is not None
                    and previous_error is not None
                    and previous_error * error_value <= 0.0
            ):
                bracket_lower = previous_gate
                bracket_upper = gate_value
                break
            else:
                pass
            previous_gate = gate_value
            previous_error = error_value
        else:
            pass

    if bracket_lower is not None and bracket_upper is not None:
        first_gate: float = bracket_lower
        last_gate: float = bracket_upper
        for _ in range(64):
            middle_gate: float = (first_gate + last_gate) / 2.0
            middle_point: tuple[float, float, float, float, float, float, float] | None = (
                get_gov_hydro_francis_point_at_gate(settings, middle_gate)
            )
            first_point: tuple[float, float, float, float, float, float, float] | None = (
                get_gov_hydro_francis_point_at_gate(settings, first_gate)
            )
            if middle_point is not None and first_point is not None and (
                    middle_point[3] - target_power
            ) * (first_point[3] - target_power) <= 0.0:
                last_gate = middle_gate
            else:
                first_gate = middle_gate
        else:
            pass
        final_gate: float = (first_gate + last_gate) / 2.0
        final_point: tuple[float, float, float, float, float, float, float] | None = (
            get_gov_hydro_francis_point_at_gate(settings, final_gate)
        )
        if final_point is not None:
            return (final_gate,) + final_point
        else:
            return None
    elif best_error <= 1.0e-8:
        best_point: tuple[float, float, float, float, float, float, float] | None = (
            get_gov_hydro_francis_point_at_gate(settings, best_gate)
        )
        if best_point is not None:
            return (best_gate,) + best_point
        else:
            return None
    else:
        return None


def get_gov_hydro_francis_point_at_gate(
        settings: GovHydroFrancisParameters,
        gate_value: float,
) -> tuple[float, float, float, float, float, float, float] | None:
    """Calculate a zero-derivative turbine and waterway point for one gate.

    :param settings: Converted Francis parameter set.
    :param gate_value: Gate opening in pu.
    :return: Turbine flow/head/efficiency/power, tunnel flow, chamber storage,
        and chamber head; ``None`` if the specified reservoir cannot support it.
    """
    if gate_value <= 0.0:
        return None
    else:
        if settings.waterway_enabled:
            head_denominator: float = (
                1.0 / (gate_value * gate_value) + settings.kc + settings.kg
            )
            zsfc_pu: float = settings.zsfc / settings.hn
            if zsfc_pu <= 0.0 or head_denominator <= 0.0:
                return None
            else:
                flow_value: float = math.sqrt(zsfc_pu / head_denominator)
                head_value: float = (flow_value / gate_value) ** 2
                chamber_head: float = head_value + settings.kc * flow_value ** 2
                h1_pu: float = settings.h1 / settings.hn
                h2_pu: float = settings.h2 / settings.hn
                av0_pu: float = settings.av0 * settings.hn / settings.qn
                av1_pu: float = settings.av1 * settings.hn / settings.qn
                chamber_head_pu: float = chamber_head
                if chamber_head_pu < 0.0 or chamber_head_pu > h2_pu:
                    return None
                elif chamber_head_pu <= h1_pu:
                    stored_water: float = chamber_head_pu * av1_pu
                else:
                    stored_water = h1_pu * av1_pu + (chamber_head_pu - h1_pu) * av0_pu
                efficiency_input: float = gate_value
                tunnel_flow: float = flow_value
        else:
            flow_value = gate_value / math.sqrt(
                1.0 + settings.kc * gate_value * gate_value,
            )
            head_value = (flow_value / gate_value) ** 2
            efficiency_input = gate_value
            tunnel_flow = 0.0
            stored_water = 0.0
            chamber_head_pu = 1.0
        efficiency_radicand: float = max(
            0.0, 4.0 - (efficiency_input / settings.am - 1.0) ** 2,
        )
        efficiency_value: float = max(
            0.0, settings.etamax * (math.sqrt(efficiency_radicand) - 1.0),
        )
        power_value: float = efficiency_value * (flow_value - settings.qc0) * head_value
        return (
            flow_value, head_value, efficiency_value, power_value,
            tunnel_flow, stored_water, chamber_head_pu,
        )
