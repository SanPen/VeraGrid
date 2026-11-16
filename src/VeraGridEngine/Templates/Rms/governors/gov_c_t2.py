# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""CGMES GovCT2 GGOV2 gas-turbine governor and frequency fuel ceiling."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.IO.cim.cgmes.dynamics.schema import DroopSignalFeedbackKind
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Templates.Rms.governors.ggov1 import (
    FuelFlowCharacteristic,
    GovernorDroopFeedback,
    TrackedGovernorParameters,
)
from VeraGridEngine.Utils.procedural_logic import delay
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class GovCT2Parameters:
    """Canonical GovCT2 settings plus the equation's nominal grid frequency."""

    __slots__ = (
        'mwbase', 'r', 'rselect', 'tpelec', 'maxerr', 'minerr', 'kpgov',
        'kigov', 'kdgov', 'tdgov', 'vmax', 'vmin', 'tact', 'kturb', 'wfnl',
        'tb', 'tc', 'wfspd', 'teng', 'tfload', 'kpload', 'kiload', 'ldref',
        'dm', 'ropen', 'rclose', 'kimw', 'aset', 'ka', 'ta', 'db', 'tsa',
        'tsb', 'rup', 'rdown', 'prate', 'flim_points', 'plim_points',
        'nominal_frequency',
    )

    def __init__(
            self,
            mwbase: float = 100.0,
            r: float = 0.05,
            rselect: DroopSignalFeedbackKind = DroopSignalFeedbackKind.electricalPower,
            tpelec: float = 0.1,
            maxerr: float = 0.05,
            minerr: float = -0.05,
            kpgov: float = 10.0,
            kigov: float = 2.0,
            kdgov: float = 0.0,
            tdgov: float = 1.0,
            vmax: float = 1.0,
            vmin: float = 0.0,
            tact: float = 0.5,
            kturb: float = 1.5,
            wfnl: float = 0.2,
            tb: float = 0.5,
            tc: float = 0.0,
            wfspd: bool = False,
            teng: float = 0.0,
            tfload: float = 3.0,
            kpload: float = 2.0,
            kiload: float = 0.67,
            ldref: float = 1.0,
            dm: float = 0.0,
            ropen: float = 0.1,
            rclose: float = -0.1,
            kimw: float = 0.01,
            aset: float = 10.0,
            ka: float = 0.0,
            ta: float = 0.1,
            db: float = 0.0,
            tsa: float = 4.0,
            tsb: float = 5.0,
            rup: float = 99.0,
            rdown: float = -99.0,
            prate: float = 0.017,
            flim_points: tuple[float, ...] = (59.0,) + (0.0,) * 9,
            plim_points: tuple[float, ...] = (0.8325,) + (0.0,) * 9,
            nominal_frequency: float = 60.0,
    ) -> None:
        """Store all canonical fields and the frequency base for FLIM values.

        :param mwbase: Governor power base in MW.
        :param r: Permanent speed droop.
        :param rselect: RDF droop feedback enumeration.
        :param tpelec: Electrical-power measurement time in seconds.
        :param maxerr: Maximum speed error.
        :param minerr: Minimum speed error.
        :param kpgov: Governor proportional gain.
        :param kigov: Governor integral gain.
        :param kdgov: Governor derivative gain.
        :param tdgov: Derivative filter time in seconds.
        :param vmax: Maximum commanded fuel stroke.
        :param vmin: Minimum commanded fuel stroke.
        :param tact: Actuator time in seconds.
        :param kturb: Turbine gain.
        :param wfnl: No-load fuel flow.
        :param tb: Turbine lag time in seconds.
        :param tc: Turbine lead time in seconds.
        :param wfspd: Select fuel flow proportional to speed.
        :param teng: Fuel transport delay in seconds.
        :param tfload: Load measurement time in seconds.
        :param kpload: Load controller proportional gain.
        :param kiload: Load controller integral gain.
        :param ldref: Temperature/load limit reference.
        :param dm: Turbine speed sensitivity coefficient.
        :param ropen: Maximum valve opening rate.
        :param rclose: Maximum valve closing rate.
        :param kimw: Electrical-power reset gain.
        :param aset: Acceleration override setpoint.
        :param ka: Acceleration override gain.
        :param ta: Acceleration detector time in seconds.
        :param db: Symmetric governor deadband.
        :param tsa: Temperature lead time in seconds.
        :param tsb: Temperature lag time in seconds.
        :param rup: Load command upper slew limit.
        :param rdown: Load command lower slew limit.
        :param prate: Frequency-ceiling slew rate in per unit per second.
        :param flim_points: Ten descending frequency thresholds in Hz.
        :param plim_points: Ten associated descending power ceilings in pu.
        :param nominal_frequency: Grid nominal frequency in Hz.
        """
        self.mwbase: float = mwbase
        self.r: float = r
        self.rselect: DroopSignalFeedbackKind = rselect
        self.tpelec: float = tpelec
        self.maxerr: float = maxerr
        self.minerr: float = minerr
        self.kpgov: float = kpgov
        self.kigov: float = kigov
        self.kdgov: float = kdgov
        self.tdgov: float = tdgov
        self.vmax: float = vmax
        self.vmin: float = vmin
        self.tact: float = tact
        self.kturb: float = kturb
        self.wfnl: float = wfnl
        self.tb: float = tb
        self.tc: float = tc
        self.wfspd: bool = wfspd
        self.teng: float = teng
        self.tfload: float = tfload
        self.kpload: float = kpload
        self.kiload: float = kiload
        self.ldref: float = ldref
        self.dm: float = dm
        self.ropen: float = ropen
        self.rclose: float = rclose
        self.kimw: float = kimw
        self.aset: float = aset
        self.ka: float = ka
        self.ta: float = ta
        self.db: float = db
        self.tsa: float = tsa
        self.tsb: float = tsb
        self.rup: float = rup
        self.rdown: float = rdown
        self.prate: float = prate
        self.flim_points: tuple[float, ...] = flim_points
        self.plim_points: tuple[float, ...] = plim_points
        self.nominal_frequency: float = nominal_frequency


def get_gov_ct2_frequency_power_limit(
        frequency: float,
        flim_points: tuple[float, ...],
        plim_points: tuple[float, ...],
) -> float | None:
    """Interpolate the active GGOV2 power ceiling without low-frequency extrapolation.

    :param frequency: Measured frequency in Hz.
    :param flim_points: Descending source frequency thresholds.
    :param plim_points: Associated descending power ceilings.
    :return: Power ceiling in pu, or None when the table is disabled.
    """
    active_count: int = 0
    while active_count < 10 and flim_points[active_count] > 0.0:
        active_count += 1
    if active_count == 0:
        return None
    elif frequency >= flim_points[0]:
        return None
    elif active_count == 1 or frequency <= flim_points[active_count - 1]:
        return plim_points[active_count - 1]
    else:
        for point_index in range(active_count - 1):
            high_frequency: float = flim_points[point_index]
            low_frequency: float = flim_points[point_index + 1]
            if low_frequency <= frequency < high_frequency:
                fraction: float = (frequency - low_frequency) / (high_frequency - low_frequency)
                return plim_points[point_index + 1] + fraction * (
                    plim_points[point_index] - plim_points[point_index + 1]
                )
            else:
                pass
        return plim_points[active_count - 1]


def build_gov_c_t2_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: GovCT2Parameters | None = None,
) -> RmsModelTemplate:
    """Build the GGOV2 governor, temperature selector and ramped frequency ceiling.

    :param vfactory: Factory owning the symbolic equations.
    :param name: Optional unique instance name.
    :param parameters: Canonical GovCT2 values and frequency curve.
    :return: Equation-backed template with speed, electrical-power, reference,
        and supervisory-setpoint inputs.
    :raises ValueError: Invalid source coefficients, curve points, or unsupported branches.
    """
    settings: GovCT2Parameters = GovCT2Parameters() if parameters is None else parameters
    values: tuple[float, ...] = (
        settings.mwbase, settings.r, settings.tpelec, settings.maxerr,
        settings.minerr, settings.kpgov, settings.kigov, settings.kdgov,
        settings.tdgov, settings.vmax, settings.vmin, settings.tact,
        settings.kturb, settings.wfnl, settings.tb, settings.tc, settings.teng,
        settings.tfload, settings.kpload, settings.kiload, settings.ldref,
        settings.dm, settings.ropen, settings.rclose, settings.kimw,
        settings.aset, settings.ka, settings.ta, settings.db, settings.tsa,
        settings.tsb, settings.rup, settings.rdown, settings.prate,
        settings.nominal_frequency, *settings.flim_points, *settings.plim_points,
    )
    if len(settings.flim_points) != 10 or len(settings.plim_points) != 10:
        raise ValueError('GovCT2 requires ten frequency and power curve values')
    elif not all(math.isfinite(value) for value in values):
        raise ValueError('GovCT2 parameters must be finite')
    elif settings.ka < 0.0:
        raise ValueError('GovCT2 acceleration limiter gain ka must be nonnegative')
    elif settings.ka > 0.0 and settings.ta <= 0.0:
        raise ValueError('GovCT2 acceleration limiter requires a positive ta time constant')
    elif settings.teng < 0.0:
        raise ValueError('GovCT2 fuel transport delay teng must be nonnegative')
    elif settings.kturb <= 0.0 or settings.tact <= 0.0 or settings.prate < 0.0:
        raise ValueError('GovCT2 turbine, actuator, and frequency-limit rates are invalid')
    elif settings.kpgov <= 0.0 or settings.kigov < 0.0 or settings.tdgov < 0.0:
        raise ValueError('GovCT2 speed controller gains and times are invalid')
    elif settings.kpload > 0.0 and settings.kiload > 0.0 and settings.tfload <= 0.0:
        raise ValueError('GovCT2 enabled temperature controller requires positive tfload')
    else:
        pass
    active_count: int = 0
    while active_count < 10 and settings.flim_points[active_count] > 0.0:
        active_count += 1
    if any(
            settings.flim_points[index] <= settings.flim_points[index + 1]
            or settings.plim_points[index] < settings.plim_points[index + 1]
            for index in range(max(active_count - 1, 0))
    ):
        raise ValueError('GovCT2 active frequency and power points must descend monotonically')
    elif any(
            settings.flim_points[index] == 0.0 and settings.plim_points[index] != 0.0
            for index in range(active_count, 10)
    ):
        raise ValueError('GovCT2 unused frequency points must have zero power limits')
    else:
        pass

    template_name: str = 'GovCT2' if name is None else name
    control: ControlRealization = ControlRealization(vfactory, template_name)
    omega: Var = control.input('OmegaPu', Const(1.0))
    electrical_power: Var = control.input('ElectricalPowerPu', Const(0.5))
    reference: Var = control.input('PRefPu', Const(0.5))
    power_setpoint: Var = control.input('PmwSetPu', electrical_power)
    speed_reference: Expr = omega - Const(1.0)
    measured_power: Var = control.lag(
        'PeMeasuredPu', electrical_power,
        control.parameter('Tpelec', settings.tpelec), settings.tpelec,
        Const(0.5),
    )
    if settings.rselect == DroopSignalFeedbackKind.electricalPower:
        droop_feedback: Expr = measured_power
        initial_feedback: float = 0.5
    elif settings.rselect == DroopSignalFeedbackKind.fuelValveStroke:
        droop_feedback = Const(0.5)
        initial_feedback = 0.5
    elif settings.rselect == DroopSignalFeedbackKind.governorOutput:
        droop_feedback = Const(0.5)
        initial_feedback = 0.5
    elif settings.rselect == DroopSignalFeedbackKind.none:
        droop_feedback = Const(0.0)
        initial_feedback = 0.0
    else:
        raise ValueError('GovCT2 rselect is not a canonical feedback selector')
    integral_state: Var = control.differential(
        vfactory.add_var(f'MwIntegralPu_{template_name}'),
        settings.kimw * (power_setpoint - measured_power),
        Const(0.0),
    )
    speed_error_raw: Expr = reference + integral_state - speed_reference - settings.r * droop_feedback
    if settings.db > 0.0:
        speed_error: Expr = sym.max(speed_error_raw - settings.db / 2.0, Const(0.0)) + sym.min(
            speed_error_raw + settings.db / 2.0, Const(0.0),
        )
    else:
        speed_error = speed_error_raw
    speed_error_state: Var = control.algebraic(
        'SpeedErrorPu',
        sym.hard_sat(speed_error, settings.minerr, settings.maxerr),
        Const(0.0),
    )
    derivative_output: Expr
    if settings.kdgov > 0.0:
        derivative_output = control.washout(
            'DerivativePu', speed_error_state,
            control.parameter('Tdgov', settings.tdgov), settings.tdgov,
            settings.kdgov / settings.tdgov, Const(0.0),
        )
    else:
        derivative_output = Const(0.0)
    initial_power: float = 0.5
    initial_fuel: float = initial_power / settings.kturb + settings.wfnl
    initial_fuel = min(max(initial_fuel, settings.vmin), settings.vmax)
    valve: Var = vfactory.add_var(f'ActuatorPu_{template_name}')
    selected: Var = vfactory.add_var(f'LowValueSelectPu_{template_name}')
    governor_memory_state: Var = vfactory.add_var(f'GovernorIntegralPu_{template_name}')
    governor_memory: Var = control.differential(
        governor_memory_state,
        (settings.kigov / settings.kpgov) * (selected - governor_memory_state),
        Const(initial_fuel),
        Const(settings.vmin),
        Const(settings.vmax),
    )
    governor_demand: Var = control.algebraic(
        'GovernorDemandPu',
        settings.kpgov * speed_error_state + derivative_output + governor_memory,
        Const(initial_fuel),
    )
    fuel_flow: Var = control.algebraic(
        'FuelFlowPu',
        valve * omega if settings.wfspd else valve,
        Const(initial_fuel),
    )
    fuel_measurement: Expr = (
        fuel_flow * omega ** settings.dm if settings.dm < 0.0 else fuel_flow
    )
    temperature_fuel: Var = control.lead_lag(
        'TemperaturePu', fuel_measurement,
        control.parameter('Tsa', settings.tsa),
        control.parameter('Tsb', settings.tsb),
        settings.tsa, settings.tsb, Const(initial_fuel),
    )
    load_measurement: Var = control.lag(
        'LoadMeasuredPu', temperature_fuel,
        control.parameter('Tfload', settings.tfload), settings.tfload,
        Const(initial_fuel),
    )
    load_error: Var = control.algebraic(
        'LoadErrorPu', settings.ldref / settings.kturb + settings.wfnl - load_measurement,
        Const(settings.ldref / settings.kturb + settings.wfnl - initial_fuel),
    )
    if settings.kpload > 0.0 and settings.kiload > 0.0:
        load_error_initial: float = (
            settings.ldref / settings.kturb + settings.wfnl - initial_fuel
        )
        load_demand: Var = vfactory.add_var(f'LoadDemandPu_{template_name}')
        load_memory: Var = control.algebraic(
            'LoadIntegralPu',
            load_demand - settings.kpload * load_error,
            Const(initial_fuel),
        )
        load_error_rate: Expr = -(
            temperature_fuel - load_measurement
        ) / settings.tfload
        load_demand_rate: Expr = sym.hard_sat(
            settings.kpload * load_error_rate
            + settings.kiload / settings.kpload * (selected - load_memory),
            settings.rdown,
            settings.rup,
        )
        control.differential(
            load_demand,
            load_demand_rate,
            Const(initial_fuel + settings.kpload * load_error_initial),
        )
        temperature_ceiling: Expr = sym.hard_sat(
            load_demand, settings.vmin, Const(1.0),
        )
        temperature_initial: float = initial_fuel
    else:
        temperature_demand: Var = control.algebraic(
            'TemperatureFuelCommandPu', Const(1.0), Const(1.0),
        )
        temperature_ceiling = temperature_demand
        temperature_initial = 1.0

    frequency_hz: Expr = omega * settings.nominal_frequency
    frequency_limit: Expr | None = None
    active_curve_count: int = 0
    while active_curve_count < 10 and settings.flim_points[active_curve_count] > 0.0:
        active_curve_count += 1
    if active_curve_count > 0:
        last_fuel_limit: float = min(
            settings.vmax,
            settings.plim_points[active_curve_count - 1] / settings.kturb + settings.wfnl,
        )
        curve_fuel_limit: Expr = Const(last_fuel_limit)
        if active_curve_count == 1:
            pass
        else:
            for point_index in range(active_curve_count - 1):
                upper_frequency: float = settings.flim_points[point_index]
                lower_frequency: float = settings.flim_points[point_index + 1]
                upper_power: float = settings.plim_points[point_index]
                lower_power: float = settings.plim_points[point_index + 1]
                segment_power: Expr = lower_power + (
                    (frequency_hz - lower_frequency)
                    * (upper_power - lower_power)
                    / (upper_frequency - lower_frequency)
                )
                segment_fuel: Expr = sym.min(
                    settings.vmax,
                    segment_power / settings.kturb + settings.wfnl,
                )
                segment_active: Expr = (
                    sym.heaviside(frequency_hz - lower_frequency)
                    - sym.heaviside(frequency_hz - upper_frequency)
                )
                curve_fuel_limit = curve_fuel_limit + (
                    segment_fuel - last_fuel_limit
                ) * segment_active
        curve_fuel_limit = curve_fuel_limit + (
            settings.vmax - last_fuel_limit
        ) * sym.heaviside(frequency_hz - settings.flim_points[0])
        frequency_limit_state: Var = vfactory.add_var(
            f'FrequencyFuelCeilingPu_{template_name}'
        )
        frequency_limit = control.differential(
            frequency_limit_state,
            sym.hard_sat(
                curve_fuel_limit - frequency_limit_state,
                -settings.prate,
                settings.prate,
            ),
            Const(settings.vmax),
            Const(settings.vmin),
            Const(settings.vmax),
        )
        frequency_ceiling: Expr = frequency_limit
        frequency_power_limit: float | None = get_gov_ct2_frequency_power_limit(
            settings.nominal_frequency,
            settings.flim_points,
            settings.plim_points,
        )
        frequency_initial: float = settings.vmax
        if frequency_power_limit is not None:
            frequency_initial = min(
                max(
                    frequency_power_limit / settings.kturb + settings.wfnl,
                    settings.vmin,
                ),
                settings.vmax,
            )
        else:
            pass
    else:
        frequency_ceiling_var: Var = control.algebraic(
            'FrequencyFuelCeilingPu', Const(settings.vmax), Const(settings.vmax),
        )
        frequency_ceiling = frequency_ceiling_var
        frequency_initial = settings.vmax

    normal_fuel_expression: Expr = sym.hard_sat(
        sym.min(sym.min(governor_demand, temperature_ceiling), frequency_ceiling),
        settings.vmin,
        settings.vmax,
    )
    initial_normal_fuel: float = min(
        initial_fuel,
        temperature_initial,
        frequency_initial,
    )
    normal_fuel: Var = control.algebraic(
        'NormalFuelRequestPu',
        normal_fuel_expression,
        Const(initial_normal_fuel),
    )
    acceleration_request: Var | None = None
    select_expression: Expr = normal_fuel
    if settings.ka > 0.0:
        acceleration_input: Var = control.input('OmegaDerivativePu', Const(0.0))
        acceleration_time: Var = control.parameter('GovCT2.ta', settings.ta)
        acceleration_gain: Var = control.parameter('GovCT2.ka', settings.ka)
        acceleration_setpoint: Var = control.parameter('GovCT2.aset', settings.aset)
        filtered_acceleration: Var = control.lag(
            'FilteredAccelerationPu',
            acceleration_input,
            acceleration_time,
            settings.ta,
            Const(0.0),
        )
        acceleration_offset: Var = control.differential(
            vfactory.add_var(f'AccelerationFuelOffsetPu_{template_name}'),
            acceleration_gain * (acceleration_setpoint - filtered_acceleration),
            Const(0.0),
            Const(settings.vmin) - normal_fuel,
            Const(0.0),
        )
        acceleration_request = control.algebraic(
            'FsrAccelerationPu',
            normal_fuel + acceleration_offset,
            Const(initial_normal_fuel),
        )
        select_expression = sym.min(normal_fuel, acceleration_request)
    else:
        pass
    control.block.algebraic_vars.append(selected)
    control.block.algebraic_eqs.append(selected - select_expression)
    control.block.init_eqs[selected] = Const(initial_normal_fuel)
    velocity: Expr = sym.hard_sat(
        (selected - valve) / settings.tact,
        settings.rclose,
        settings.ropen,
    )
    control.differential(
        valve,
        velocity,
        Const(initial_fuel),
        Const(settings.vmin),
        Const(settings.vmax),
    )
    turbine_fuel: Expr = fuel_flow
    if settings.teng > 0.0:
        delayed_fuel: Var = vfactory.add_var(f'FuelTransportedPu_{template_name}')
        control.block.event_dict[delayed_fuel] = Const(initial_fuel)
        control.block.procedural_logic.append(
            delay(
                input_expr=fuel_flow,
                T=settings.teng,
                output=delayed_fuel,
                name=f'GovCT2.FuelTransportDelay_{template_name}',
            )
        )
        turbine_fuel = delayed_fuel
    else:
        pass
    turbine_power: Var = control.lead_lag(
        'TurbinePowerPu',
        settings.kturb * (turbine_fuel - settings.wfnl),
        control.parameter('Tc', settings.tc),
        control.parameter('Tb', settings.tb),
        settings.tc,
        settings.tb,
        Const(initial_power),
    )
    mechanical_power: Var = control.algebraic(
        'PmPu',
        turbine_power - settings.dm * (omega - Const(1.0))
        if settings.dm > 0.0 else turbine_power,
        Const(initial_power),
    )
    output_variables: tuple[Var, ...] = (mechanical_power, valve, selected)
    if acceleration_request is not None:
        output_variables += (acceleration_request,)
    else:
        pass
    template: RmsModelTemplate = control.finish(
        output_variables,
        'CGMES GovCT2 GGOV2 governor with frequency-dependent fuel ceiling',
    )
    template.comment = 'GGOV2 source equations with frequency-dependent fuel ceiling and optional acceleration limiter.'
    if settings.teng > 0.0:
        template.comment += ' Fuel transport delay uses accepted-sample history with zero-order hold.'
    else:
        pass
    return template
