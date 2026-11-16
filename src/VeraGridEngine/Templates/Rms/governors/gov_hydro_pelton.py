# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES GovHydroPelton governor and hydraulic turbine."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Templates.Rms.governors.gov_hydro_francis import (
    build_gov_hydro_francis_level,
)
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class GovHydroPeltonParameters:
    """CGMES Pelton governor, servo, and hydraulic-system coefficients."""

    __slots__ = (
        'av0', 'av1', 'bp', 'db1', 'db2', 'h1', 'h2', 'hn', 'kc', 'kg',
        'qc0', 'qn', 'simplified_pelton', 'static_compensating', 'ta', 'ts',
        'tv', 'twnc', 'twng', 'tx', 'va', 'valvmax', 'valvmin', 'vav',
        'vc', 'vcv', 'waterway_enabled', 'zsfc', 'nominal_frequency',
    )

    def __init__(
            self,
            av0: float = 30.0,
            av1: float = 700.0,
            bp: float = 0.05,
            db1: float = 0.0,
            db2: float = 0.01,
            h1: float = 4.0,
            h2: float = 40.0,
            hn: float = 250.0,
            kc: float = 0.025,
            kg: float = 0.025,
            qc0: float = 0.05,
            qn: float = 250.0,
            simplified_pelton: bool = True,
            static_compensating: bool = False,
            ta: float = 3.0,
            ts: float = 0.15,
            tv: float = 0.3,
            twnc: float = 1.0,
            twng: float = 3.0,
            tx: float = 0.5,
            va: float = 0.06,
            valvmax: float = 1.1,
            valvmin: float = 0.0,
            vav: float = 0.1,
            vc: float = -0.06,
            vcv: float = -0.1,
            waterway_enabled: bool = False,
            zsfc: float = 25.0,
            nominal_frequency: float = 50.0,
    ) -> None:
        """Store the RDF coefficients in their physical units.

        :param av0: Surge-tank area in square metres.
        :param av1: Compensation-tank area in square metres.
        :param bp: Governor permanent droop in pu.
        :param db1: Main gate-command deadband in hertz.
        :param db2: Needle-command deadband in hertz.
        :param h1: Compensation-chamber level in metres.
        :param h2: Surge-tank level in metres.
        :param hn: Rated hydraulic head in metres.
        :param kc: Penstock friction coefficient in pu.
        :param kg: Tunnel friction coefficient in pu.
        :param qc0: No-load turbine flow in pu.
        :param qn: Rated turbine flow in cubic metres per second.
        :param simplified_pelton: Select direct gate opening rather than NL3.
        :param static_compensating: Select the NL4 reference characteristic.
        :param ta: Speed-derivative feedback time in seconds.
        :param ts: Main gate servo time in seconds.
        :param tv: Pelton needle servo time in seconds.
        :param twnc: Penstock water inertia time in seconds.
        :param twng: Tunnel water inertia time in seconds.
        :param tx: Governor integrator time in seconds.
        :param va: Main gate opening rate in pu per second.
        :param valvmax: Maximum gate and needle travel in pu.
        :param valvmin: Minimum gate and needle travel in pu.
        :param vav: Needle opening rate in pu per second.
        :param vc: Main gate closing rate in pu per second.
        :param vcv: Needle closing rate in pu per second.
        :param waterway_enabled: Enable the detailed tunnel and surge tank.
        :param zsfc: Reservoir head above the penstock in metres.
        :param nominal_frequency: System frequency in hertz.
        """
        self.av0: float = av0
        self.av1: float = av1
        self.bp: float = bp
        self.db1: float = db1
        self.db2: float = db2
        self.h1: float = h1
        self.h2: float = h2
        self.hn: float = hn
        self.kc: float = kc
        self.kg: float = kg
        self.qc0: float = qc0
        self.qn: float = qn
        self.simplified_pelton: bool = simplified_pelton
        self.static_compensating: bool = static_compensating
        self.ta: float = ta
        self.ts: float = ts
        self.tv: float = tv
        self.twnc: float = twnc
        self.twng: float = twng
        self.tx: float = tx
        self.va: float = va
        self.valvmax: float = valvmax
        self.valvmin: float = valvmin
        self.vav: float = vav
        self.vc: float = vc
        self.vcv: float = vcv
        self.waterway_enabled: bool = waterway_enabled
        self.zsfc: float = zsfc
        self.nominal_frequency: float = nominal_frequency


def build_gov_hydro_pelton_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: GovHydroPeltonParameters | None = None,
) -> RmsModelTemplate:
    """Build the Pelton governor, needle servo, and waterway equations.

    :param vfactory: Factory owning symbolic model variables.
    :param name: Optional unique template instance name.
    :param parameters: RDF-converted coefficients.
    :return: Executable CGMES Pelton template with open machine signal ports.
    :raises ValueError: Invalid bases, times, rates, limits, or waterway geometry.
    """
    settings: GovHydroPeltonParameters = (
        GovHydroPeltonParameters() if parameters is None else parameters
    )
    numeric_parameters: tuple[float, ...] = (
        settings.av0, settings.av1, settings.bp, settings.db1, settings.db2,
        settings.h1, settings.h2, settings.hn, settings.kc, settings.kg,
        settings.qc0, settings.qn, settings.ta, settings.ts, settings.tv,
        settings.twnc, settings.twng, settings.tx, settings.va, settings.valvmax,
        settings.valvmin, settings.vav, settings.vc, settings.vcv, settings.zsfc,
        settings.nominal_frequency,
    )
    if not all(math.isfinite(value) for value in numeric_parameters):
        raise ValueError('GovHydroPelton parameters must be finite')
    elif min(settings.hn, settings.qn, settings.nominal_frequency) <= 0.0:
        raise ValueError('GovHydroPelton requires positive hydraulic and frequency bases')
    elif min(settings.ta, settings.ts, settings.tv, settings.twnc, settings.twng, settings.tx) < 0.0:
        raise ValueError('GovHydroPelton time constants must be nonnegative')
    elif settings.waterway_enabled and min(settings.av0, settings.av1) <= 0.0:
        raise ValueError('GovHydroPelton waterway areas must be positive')
    elif settings.waterway_enabled and not 0.0 <= settings.h1 <= settings.h2:
        raise ValueError('GovHydroPelton requires 0 <= H1 <= H2')
    elif settings.valvmin >= settings.valvmax:
        raise ValueError('GovHydroPelton valve limits are invalid')
    elif settings.va < 0.0 or settings.vc > 0.0 or settings.vav < 0.0 or settings.vcv > 0.0:
        raise ValueError('GovHydroPelton opening/closing rate signs are invalid')
    elif settings.bp < 0.0 or settings.db1 < 0.0 or settings.db2 < 0.0:
        raise ValueError('GovHydroPelton droop and deadbands must be nonnegative')
    elif settings.waterway_enabled and min(settings.kc, settings.kg) < 0.0:
        raise ValueError('GovHydroPelton waterway losses must be nonnegative')
    else:
        pass

    template_name: str = 'GovHydroPelton' if name is None else name
    control: ControlRealization = ControlRealization(vfactory, template_name)
    bp: Var = control.parameter('GovHydroPelton.bp', settings.bp)
    db1: Var = control.parameter('GovHydroPelton.db1Pu', settings.db1 / settings.nominal_frequency)
    db2: Var = control.parameter('GovHydroPelton.db2Pu', settings.db2 / settings.nominal_frequency)
    kc: Var = control.parameter('GovHydroPelton.kc', settings.kc)
    kg: Var = control.parameter('GovHydroPelton.kg', settings.kg)
    qc0: Var = control.parameter('GovHydroPelton.qc0', settings.qc0)
    ta: Var = control.parameter('GovHydroPelton.ta', settings.ta)
    ts: Var = control.parameter('GovHydroPelton.ts', settings.ts)
    tv: Var = control.parameter('GovHydroPelton.tv', settings.tv)
    twnc: Var = control.parameter('GovHydroPelton.twnc', settings.twnc)
    twng: Var = control.parameter('GovHydroPelton.twng', settings.twng)
    tx: Var = control.parameter('GovHydroPelton.tx', settings.tx)
    va: Var = control.parameter('GovHydroPelton.va', settings.va)
    vc: Var = control.parameter('GovHydroPelton.vc', settings.vc)
    vav: Var = control.parameter('GovHydroPelton.vav', settings.vav)
    vcv: Var = control.parameter('GovHydroPelton.vcv', settings.vcv)
    valvmax: Var = control.parameter('GovHydroPelton.valvmax', settings.valvmax)
    valvmin: Var = control.parameter('GovHydroPelton.valvmin', settings.valvmin)

    # The source diagram integrates speed/acceleration error against droop feedback.
    speed: Var = control.input('OmegaPu', Const(1.0))
    speed_derivative: Var = control.input('OmegaDerivativePu', Const(0.0))
    power_reference: Var = control.input('PRefPu', Const(0.5))
    initial_gate: float = min(max(0.5, settings.valvmin), settings.valvmax)
    controller_state: Var = vfactory.add_var(f'PeltonGovernorIntegralPu_{template_name}')
    controller_error: Expr = (
        speed - Const(1.0) - ta * speed_derivative - bp * controller_state
    )
    if settings.tx > 0.0:
        control.differential(controller_state, controller_error / tx, Const(0.0))
    else:
        control.block.algebraic_vars.append(controller_state)
        control.block.algebraic_eqs.append(controller_error)
        control.block.init_eqs[controller_state] = Const(0.0)

    # CFLAG selects NL4; otherwise the governor reference bypasses static compensation.
    if settings.static_compensating:
        governor_reference: Expr = build_pelton_nl4(power_reference + controller_state)
    else:
        governor_reference = power_reference + controller_state
    gate: Var = vfactory.add_var(f'GateOpeningPu_{template_name}')
    gate_error: Expr = governor_reference - gate
    gate_error_db: Expr = (
        sym.max(gate_error - db1, Const(0.0))
        + sym.min(gate_error + db1, Const(0.0))
    )
    # Prevent inverse-curve roundoff from selecting a full rate at zero command error.
    zero_rate_band: Const = Const(1.0e-12)
    if settings.ts > 0.0:
        gate_rate: Var = control.algebraic(
            'GateRatePuPerSecond', sym.hard_sat(gate_error_db / ts, vc, va), Const(0.0),
        )
    else:
        gate_rate = control.algebraic(
            'GateRatePuPerSecond',
            sym.heaviside(gate_error_db - zero_rate_band) * va
            + sym.heaviside(-gate_error_db - zero_rate_band) * vc,
            Const(0.0),
        )
    control.differential(gate, gate_rate, Const(initial_gate), valvmin, valvmax)

    # NL2 forms the needle demand; DB2 and TV/VAV/VCV realize the needle servo.
    needle: Var = vfactory.add_var(f'PeltonNeedlePositionPu_{template_name}')
    needle_error: Expr = gate ** Const(3.0) - needle
    needle_error_db: Expr = (
        sym.max(needle_error - db2, Const(0.0))
        + sym.min(needle_error + db2, Const(0.0))
    )
    if settings.tv > 0.0:
        needle_rate: Var = control.algebraic(
            'PeltonNeedleRatePuPerSecond',
            sym.hard_sat(needle_error_db / tv, vcv, vav),
            Const(0.0),
        )
    else:
        needle_rate = control.algebraic(
            'PeltonNeedleRatePuPerSecond',
            sym.heaviside(needle_error_db - zero_rate_band) * vav
            + sym.heaviside(-needle_error_db - zero_rate_band) * vcv,
            Const(0.0),
        )
    needle_initial: float = min(max(initial_gate ** 3.0, settings.valvmin), settings.valvmax)
    control.differential(needle, needle_rate, Const(needle_initial), valvmin, valvmax)
    if settings.simplified_pelton:
        hydraulic_opening: Expr = gate
        initial_opening: float = initial_gate
    else:
        hydraulic_opening = build_pelton_nl3(needle)
        initial_opening = get_pelton_nl3_value(needle_initial)

    # The hydraulic system can retain tunnel and surge states or use the single penstock.
    flow: Var = vfactory.add_var(f'TurbineFlowPu_{template_name}')
    head: Var = control.algebraic(
        'TurbineHeadPu',
        sym.safe_divide(flow, hydraulic_opening, Const(1.0)) ** Const(2.0),
        Const(1.0),
    )
    if settings.waterway_enabled:
        tunnel_flow: Var = vfactory.add_var(f'TunnelFlowPu_{template_name}')
        stored_water: Var = vfactory.add_var(f'SurgeWaterVolumePu_{template_name}')
        h1_pu: float = settings.h1 / settings.hn
        h2_pu: float = settings.h2 / settings.hn
        zsfc_pu: float = settings.zsfc / settings.hn
        av0_pu: float = settings.av0 * settings.hn / settings.qn
        av1_pu: float = settings.av1 * settings.hn / settings.qn
        h1: Var = control.parameter('GovHydroPelton.h1Pu', h1_pu)
        h2: Var = control.parameter('GovHydroPelton.h2Pu', h2_pu)
        av0: Var = control.parameter('GovHydroPelton.av0Pu', av0_pu)
        av1: Var = control.parameter('GovHydroPelton.av1Pu', av1_pu)
        zsfc: Var = control.parameter('GovHydroPelton.zsfcPu', zsfc_pu)
        chamber_head: Var = control.algebraic(
            'SurgeChamberHeadPu',
            build_gov_hydro_francis_level(
                stored_water, h1, h2, av0, av1,
                h1_pu, h2_pu, av0_pu, av1_pu,
            ),
            Const(h2_pu),
        )
        tunnel_error: Expr = zsfc - chamber_head - kg * tunnel_flow * sym.abs(tunnel_flow)
        penstock_error: Expr = chamber_head - head - kc * flow * sym.abs(flow)
        if settings.twng == 0.0:
            control.block.algebraic_vars.append(tunnel_flow)
            control.block.algebraic_eqs.append(tunnel_error)
            control.block.init_eqs[tunnel_flow] = Const(0.5)
        else:
            control.differential(tunnel_flow, tunnel_error / twng, Const(0.5))
        if settings.twnc == 0.0:
            control.block.algebraic_vars.append(flow)
            control.block.algebraic_eqs.append(penstock_error)
            control.block.init_eqs[flow] = Const(0.5)
        else:
            control.differential(flow, penstock_error / twnc, Const(0.5))
        control.differential(
            stored_water, tunnel_flow - flow,
            Const(h1_pu * av1_pu + (h2_pu - h1_pu) * av0_pu),
        )
    else:
        pass
    if not settings.waterway_enabled:
        penstock_error = Const(1.0) - head - kc * flow * sym.abs(flow)
        if settings.twnc == 0.0:
            control.block.algebraic_vars.append(flow)
            control.block.algebraic_eqs.append(penstock_error)
            control.block.init_eqs[flow] = Const(0.5)
        else:
            control.differential(flow, penstock_error / twnc, Const(0.5))
    else:
        pass

    # IEC efficiency is evaluated at the selected simplified/full effective opening.
    efficiency: Var = control.algebraic(
        'TurbineEfficiencyPu',
        build_pelton_efficiency(hydraulic_opening),
        Const(get_pelton_efficiency_value(initial_opening)),
    )
    mechanical_power: Var = control.algebraic(
        'PmPu', efficiency * (flow - qc0) * head, Const(0.5),
    )
    runtime: RmsModelTemplate = control.finish(
        (mechanical_power,), 'CGMES GovHydroPelton governor, needle servo, and turbine.',
    )

    # Keep all RDF scalar names in the standalone parameter record.
    parameter_template: RmsModelTemplate = RmsModelTemplate(name=template_name)
    parameter_template.block.children.append(runtime.block)
    parameter_template.block.name = template_name
    parameter_template.comment = runtime.comment
    for parameter_name in (
            'enabled', 'av0', 'av1', 'bp', 'db1', 'db2', 'h1', 'h2', 'hn',
            'kc', 'kg', 'qc0', 'qn', 'simplifiedPelton', 'staticCompensating',
            'ta', 'ts', 'tv', 'twnc', 'twng', 'tx', 'va', 'valvmax', 'valvmin',
            'vav', 'vc', 'vcv', 'waterTunnelSurgeChamberSimulation', 'zsfc',
    ):
        parameter_variable: Var = vfactory.add_var(
            f'GovHydroPelton.{parameter_name}_{template_name}'
        )
        parameter_template.block.event_dict[parameter_variable] = vfactory.add_const(
            value=None, name=parameter_variable.name,
        )
    return parameter_template


def build_pelton_nl4(value: Expr) -> Expr:
    """Build IEC NL4 static compensation for a reference signal.

    :param value: Governor reference before the characteristic.
    :return: Pelton compensated reference.
    """
    root_argument: Expr = sym.max(
        Const(0.0), Const(5.62) - (value + Const(1.1)) ** Const(2.0),
    )
    cube_argument: Expr = sym.max(
        Const(0.0), Const(2.1) - sym.sqrt(root_argument),
    )
    return cube_argument ** Const(1.0 / 3.0)


def build_pelton_nl3(value: Expr) -> Expr:
    """Build IEC NL3 effective-opening characteristic.

    :param value: Pelton needle opening.
    :return: Effective turbine opening.
    """
    radicand: Expr = Const(1.21) + value * (Const(4.2) - value)
    return sym.max(Const(0.0), Const(-1.1) + sym.sqrt(sym.max(Const(0.0), radicand)))


def get_pelton_nl3_value(value: float) -> float:
    """Evaluate IEC NL3 for equilibrium initialization.

    :param value: Pelton needle opening.
    :return: Effective turbine opening.
    """
    return max(0.0, -1.1 + math.sqrt(max(0.0, 1.21 + value * (4.2 - value))))


def get_pelton_nl4_input_value(value: float) -> float | None:
    """Invert IEC NL4 for an attainable compensated gate command.

    :param value: Desired main gate command after static compensation.
    :return: NL4 input required for the command, or None outside its real domain.
    """
    radicand: float = 5.62 - (2.1 - value ** 3.0) ** 2.0
    if radicand < 0.0:
        return None
    else:
        return math.sqrt(radicand) - 1.1


def build_pelton_efficiency(value: Expr) -> Expr:
    """Build IEC's four-segment Pelton efficiency curve.

    :param value: Effective opening or Seff approximation.
    :return: Efficiency in pu.
    """
    first_weight: Expr = sym.heaviside(value - Const(0.07)) - sym.heaviside(value - Const(0.13))
    second_weight: Expr = sym.heaviside(value - Const(0.13)) - sym.heaviside(value - Const(0.3))
    upper_weight: Expr = sym.heaviside(value - Const(0.3))
    return (
        first_weight * Const(13.83) * (value - Const(0.07))
        + second_weight * (Const(0.7) + value)
        + upper_weight
    )


def get_pelton_efficiency_value(value: float) -> float:
    """Evaluate IEC Pelton efficiency for equilibrium initialization.

    :param value: Effective opening or Seff approximation.
    :return: Efficiency in pu.
    """
    if value >= 0.3:
        return 1.0
    elif value >= 0.13:
        return 0.7 + value
    elif value >= 0.07:
        return 13.83 * (value - 0.07)
    else:
        return 0.0


def get_gov_hydro_pelton_operating_point(
        settings: GovHydroPeltonParameters,
        target_power: float,
) -> tuple[float, float, float, float, float, float, float, float, float, float] | None:
    """Find a gate and hydraulic equilibrium reproducing generator power.

    :param settings: Converted Pelton coefficients.
    :param target_power: Generator mechanical power on capability base.
    :return: Gate, needle, effective opening, flow, head, efficiency, power,
        tunnel flow, chamber storage, and chamber head; None when infeasible.
    """
    lower_gate: float = settings.valvmin
    upper_gate: float = settings.valvmax
    best_gate: float = lower_gate
    best_error: float = math.inf
    previous_gate: float | None = None
    previous_error: float | None = None
    bracket: tuple[float, float] | None = None
    for sample_index in range(1001):
        gate_value: float = lower_gate + (upper_gate - lower_gate) * sample_index / 1000.0
        point: tuple[float, float, float, float, float, float, float, float, float] | None = (
            get_gov_hydro_pelton_point_at_gate(settings, gate_value)
        )
        if point is not None:
            error_value: float = point[5] - target_power
            if abs(error_value) < best_error:
                best_gate = gate_value
                best_error = abs(error_value)
            else:
                pass
            if previous_gate is not None and previous_error is not None and previous_error * error_value <= 0.0:
                bracket = (previous_gate, gate_value)
                break
            else:
                pass
            previous_gate = gate_value
            previous_error = error_value
        else:
            pass
    if bracket is not None:
        left: float = bracket[0]
        right: float = bracket[1]
        for _ in range(64):
            middle: float = (left + right) / 2.0
            middle_point: tuple[float, float, float, float, float, float, float, float, float] | None = (
                get_gov_hydro_pelton_point_at_gate(settings, middle)
            )
            left_point: tuple[float, float, float, float, float, float, float, float, float] | None = (
                get_gov_hydro_pelton_point_at_gate(settings, left)
            )
            if middle_point is not None and left_point is not None and (
                    middle_point[5] - target_power
            ) * (left_point[5] - target_power) <= 0.0:
                right = middle
            else:
                left = middle
        else:
            pass
        final_gate: float = (left + right) / 2.0
        final_point: tuple[float, float, float, float, float, float, float, float, float] | None = (
            get_gov_hydro_pelton_point_at_gate(settings, final_gate)
        )
        if final_point is not None:
            return (final_gate,) + final_point
        else:
            return None
    elif best_error <= 1.0e-8:
        best_point: tuple[float, float, float, float, float, float, float, float, float] | None = (
            get_gov_hydro_pelton_point_at_gate(settings, best_gate)
        )
        if best_point is not None:
            return (best_gate,) + best_point
        else:
            return None
    else:
        return None


def get_gov_hydro_pelton_point_at_gate(
        settings: GovHydroPeltonParameters,
        gate_value: float,
) -> tuple[float, float, float, float, float, float, float, float, float] | None:
    """Evaluate a zero-derivative Pelton turbine point at one gate position.

    :param settings: Converted Pelton coefficients.
    :param gate_value: Main gate opening in pu.
    :return: Needle, effective opening, flow, head, efficiency, power, tunnel
        flow, chamber storage, and chamber head; None when infeasible.
    """
    if gate_value <= 0.0:
        return None
    else:
        needle_value: float = min(max(gate_value ** 3.0, settings.valvmin), settings.valvmax)
        if settings.simplified_pelton:
            opening_value: float = gate_value
        else:
            opening_value = get_pelton_nl3_value(needle_value)
        if opening_value <= 0.0:
            return None
        else:
            if settings.waterway_enabled:
                denominator: float = (
                    1.0 / (opening_value * opening_value) + settings.kc + settings.kg
                )
                reservoir_head_pu: float = settings.zsfc / settings.hn
                if denominator <= 0.0 or reservoir_head_pu <= 0.0:
                    return None
                else:
                    flow_value: float = math.sqrt(reservoir_head_pu / denominator)
                    head_value: float = (flow_value / opening_value) ** 2
                    chamber_head: float = head_value + settings.kc * flow_value ** 2
                    h1_pu: float = settings.h1 / settings.hn
                    h2_pu: float = settings.h2 / settings.hn
                    av0_pu: float = settings.av0 * settings.hn / settings.qn
                    av1_pu: float = settings.av1 * settings.hn / settings.qn
                    if chamber_head < 0.0 or chamber_head > h2_pu:
                        return None
                    elif chamber_head <= h1_pu:
                        stored_water: float = chamber_head * av1_pu
                    else:
                        stored_water = h1_pu * av1_pu + (
                            chamber_head - h1_pu
                        ) * av0_pu
                    tunnel_flow: float = flow_value
                    chamber_head_initial: float = chamber_head
            else:
                flow_value = opening_value / math.sqrt(
                    1.0 + settings.kc * opening_value * opening_value,
                )
                head_value = (flow_value / opening_value) ** 2
                tunnel_flow = 0.0
                stored_water = 0.0
                chamber_head_initial = 1.0
            efficiency_value: float = get_pelton_efficiency_value(opening_value)
            power_value: float = efficiency_value * (
                flow_value - settings.qc0
            ) * head_value
            return (
                needle_value, opening_value, flow_value, head_value,
                efficiency_value, power_value, tunnel_flow, stored_water,
                chamber_head_initial,
            )
