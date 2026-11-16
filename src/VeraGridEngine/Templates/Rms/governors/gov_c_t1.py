# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""CGMES GovCT1 implementation of the GGOV1 combustion-turbine governor."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.IO.cim.cgmes.dynamics.schema import DroopSignalFeedbackKind
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Templates.Rms.governors.ggov1 import (
    FuelFlowCharacteristic,
    GovernorDroopFeedback,
    TrackedGovernorParameters,
    build_ggov1_template,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.procedural_logic import delay
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class GovCT1Parameters:
    """All canonical scalar fields used by the supported GovCT1 paths."""

    __slots__ = (
        'mwbase', 'r', 'rselect', 'tpelec', 'maxerr', 'minerr', 'kpgov',
        'kigov', 'kdgov', 'tdgov', 'vmax', 'vmin', 'tact', 'kturb', 'wfnl',
        'tb', 'tc', 'wfspd', 'teng', 'tfload', 'kpload', 'kiload', 'ldref',
        'dm', 'ropen', 'rclose', 'kimw', 'aset', 'ka', 'ta', 'db', 'tsa',
        'tsb', 'rup', 'rdown',
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
            vmin: float = 0.15,
            tact: float = 0.5,
            kturb: float = 1.5,
            wfnl: float = 0.2,
            tb: float = 0.5,
            tc: float = 0.0,
            wfspd: bool = True,
            teng: float = 0.0,
            tfload: float = 3.0,
            kpload: float = 2.0,
            kiload: float = 0.67,
            ldref: float = 1.0,
            dm: float = 0.0,
            ropen: float = 0.1,
            rclose: float = -0.1,
            kimw: float = 0.01,
            aset: float = 0.01,
            ka: float = 0.0,
            ta: float = 0.1,
            db: float = 0.0,
            tsa: float = 4.0,
            tsb: float = 5.0,
            rup: float = 99.0,
            rdown: float = -99.0,
    ) -> None:
        """Store canonical GovCT1 values, including unsupported source paths.

        :param mwbase: Governor active-power base in MW.
        :param r: Permanent speed droop.
        :param rselect: Canonical feedback selection.
        :param tpelec: Electrical-power measurement time constant in seconds.
        :param maxerr: Upper governor error limit.
        :param minerr: Lower governor error limit.
        :param kpgov: Speed governor proportional gain.
        :param kigov: Speed governor integral gain.
        :param kdgov: Speed governor derivative gain.
        :param tdgov: Derivative filter time constant in seconds.
        :param vmax: Maximum fuel-valve command.
        :param vmin: Minimum fuel-valve command.
        :param tact: Valve actuator time constant in seconds.
        :param kturb: Turbine fuel-to-power gain.
        :param wfnl: No-load fuel flow.
        :param tb: Turbine lag time in seconds.
        :param tc: Turbine lead time in seconds.
        :param wfspd: Select fuel flow proportional to shaft speed.
        :param teng: Fuel transport delay in seconds.
        :param tfload: Load-controller measurement time in seconds.
        :param kpload: Load-controller proportional gain.
        :param kiload: Load-controller integral gain.
        :param ldref: Load-controller fuel reference.
        :param dm: Turbine speed sensitivity coefficient.
        :param ropen: Maximum valve opening rate.
        :param rclose: Maximum valve closing rate.
        :param kimw: Electrical power reset gain.
        :param aset: Acceleration override set point.
        :param ka: Acceleration override gain.
        :param ta: Acceleration measurement time in seconds.
        :param db: Symmetric speed governor deadband.
        :param tsa: Temperature measurement lead time in seconds.
        :param tsb: Temperature measurement lag time in seconds.
        :param rup: Maximum load-controller rise rate.
        :param rdown: Maximum load-controller fall rate.
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


def build_gov_c_t1_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: GovCT1Parameters | None = None,
) -> RmsModelTemplate:
    """Build the supported CGMES GovCT1 GGOV1 transfer graph.

    :param vfactory: Symbol factory owning model variables.
    :param name: Optional unique instance name.
    :param parameters: Canonical GovCT1 scalar values.
    :return: Governor graph with the source-required host inputs and outputs.
    :raises ValueError: An enabled acceleration limiter has invalid coefficients.
    """
    settings: GovCT1Parameters = GovCT1Parameters() if parameters is None else parameters
    if settings.ka < 0.0 or not math.isfinite(settings.ka):
        raise ValueError('GovCT1 acceleration limiter gain ka must be finite and nonnegative')
    elif settings.ka > 0.0 and (not math.isfinite(settings.ta) or settings.ta <= 0.0):
        raise ValueError('GovCT1 acceleration limiter requires a positive ta time constant')
    elif not math.isfinite(settings.teng) or settings.teng < 0.0:
        raise ValueError('GovCT1 fuel transport delay teng must be finite and nonnegative')
    else:
        pass
    feedback: GovernorDroopFeedback
    if settings.rselect == DroopSignalFeedbackKind.electricalPower:
        feedback = GovernorDroopFeedback.ELECTRICAL_POWER
    elif settings.rselect == DroopSignalFeedbackKind.none:
        feedback = GovernorDroopFeedback.ISOCHRONOUS
    elif settings.rselect == DroopSignalFeedbackKind.fuelValveStroke:
        feedback = GovernorDroopFeedback.VALVE_STROKE
    elif settings.rselect == DroopSignalFeedbackKind.governorOutput:
        feedback = GovernorDroopFeedback.REQUESTED_STROKE
    else:
        raise ValueError('GovCT1 requires a canonical rselect value')
    fuel_characteristic: FuelFlowCharacteristic = (
        FuelFlowCharacteristic.SHAFT_DRIVEN if settings.wfspd
        else FuelFlowCharacteristic.INDEPENDENT
    )
    tracked: TrackedGovernorParameters = TrackedGovernorParameters(
        feedback=feedback,
        fuel_characteristic=fuel_characteristic,
        droop=settings.r,
        power_time=settings.tpelec,
        error_limits=(settings.minerr, settings.maxerr),
        governor_gains=(settings.kpgov, settings.kigov, settings.kdgov),
        derivative_time=settings.tdgov,
        valve_limits=(settings.vmin, settings.vmax),
        actuator_time=settings.tact,
        valve_rates=(settings.rclose, settings.ropen),
        turbine_gain=settings.kturb,
        no_load_fuel=settings.wfnl,
        turbine_times=(settings.tc, settings.tb),
        load_time=settings.tfload,
        load_gains=(settings.kpload, settings.kiload),
        load_reference=settings.ldref,
        damping=settings.dm,
        reset_gain=settings.kimw,
        deadband=settings.db,
        temperature_times=(settings.tsa, settings.tsb),
        load_rates=(settings.rdown, settings.rup),
    )
    template_name: str = 'GovCT1' if name is None else name
    template: RmsModelTemplate = build_ggov1_template(
        vf=vfactory,
        name=template_name,
        parameters=tracked,
    )
    if settings.ka > 0.0:
        normal_fuel: Var | None = None
        normal_demand: Var | None = None
        load_limit: Var | None = None
        selected_fuel: Var | None = None
        candidate_variable: Var
        for candidate_variable in template.block.get_all_vars():
            if candidate_variable.name == f'LowValueSelectPu_{template_name}':
                selected_fuel = candidate_variable
            else:
                pass
            if candidate_variable.name == f'GovernorDemandPu_{template_name}':
                normal_demand = candidate_variable
            else:
                pass
            if candidate_variable.name == f'LimitedLoadDemandPu_{template_name}':
                load_limit = candidate_variable
            else:
                pass
        else:
            pass
        if selected_fuel is not None and normal_demand is not None:
            control: ControlRealization = ControlRealization(vfactory, template_name)
            acceleration_input: Var = control.input('OmegaDerivativePu', Const(0.0))
            acceleration_time: Var = control.parameter('GovCT1.ta', settings.ta)
            acceleration_gain: Var = control.parameter('GovCT1.ka', settings.ka)
            acceleration_setpoint: Var = control.parameter('GovCT1.aset', settings.aset)
            filtered_acceleration: Var = control.lag(
                'FilteredAccelerationPu',
                acceleration_input,
                acceleration_time,
                settings.ta,
                Const(0.0),
            )
            base_fuel_initial: Expr | Const | None = template.block.init_eqs.get(
                selected_fuel,
                None,
            )
            if base_fuel_initial is None:
                base_fuel_initial = Const(0.0)
            else:
                pass
            base_fuel: Var = control.algebraic(
                'NormalFuelRequestPu',
                sym.hard_sat(
                    sym.min(
                        normal_demand,
                        Const(1.0) if load_limit is None else load_limit,
                    ),
                    settings.vmin,
                    settings.vmax,
                ),
                base_fuel_initial,
            )
            # Bounding the offset to [Vmin - FSR, 0] makes this inactive branch track FSR.
            acceleration_offset: Var = control.differential(
                vfactory.add_var(f'AccelerationFuelOffsetPu_{template_name}'),
                acceleration_gain * (acceleration_setpoint - filtered_acceleration),
                Const(0.0),
                Const(settings.vmin) - base_fuel,
                Const(0.0),
            )
            acceleration_request: Var = control.algebraic(
                'FsrAccelerationPu',
                base_fuel + acceleration_offset,
                base_fuel_initial,
            )
            for equation_index in range(len(template.block.algebraic_eqs)):
                current_equation: Expr = template.block.algebraic_eqs[equation_index]
                if current_equation.contains_var(selected_fuel):
                    template.block.algebraic_eqs[equation_index] = (
                        selected_fuel
                        - sym.hard_sat(
                            sym.min(base_fuel, acceleration_request),
                            settings.vmin,
                            settings.vmax,
                        )
                    )
                else:
                    pass
            else:
                pass
            template.block.children.append(control.block)
            template.block.out_vars.append(acceleration_request)
        else:
            raise ValueError('GovCT1 GGOV1 graph is missing its acceleration limiter ports')
    else:
        pass
    if settings.teng > 0.0:
        fuel_flow: Var | None = None
        turbine_power: Var | None = None
        turbine_power_state: Var | None = None
        candidate_variable: Var
        for candidate_variable in template.block.get_all_vars():
            if candidate_variable.name == f'FuelFlowPu_{template_name}':
                fuel_flow = candidate_variable
            else:
                pass
            if candidate_variable.name == f'TurbinePowerPu_{template_name}':
                turbine_power = candidate_variable
            else:
                pass
            if candidate_variable.name == f'TurbinePowerPuState_{template_name}':
                turbine_power_state = candidate_variable
            else:
                pass
        else:
            pass
        if fuel_flow is None or turbine_power is None:
            raise ValueError('GovCT1 GGOV1 graph is missing the fuel-flow or turbine-power signal')
        else:
            # Fuel sensing stays immediate; only the fuel-to-turbine path includes transport delay.
            delayed_fuel: Var = vfactory.add_var(f'FuelTransportedPu_{template_name}')
            fuel_flow_initial: Expr | Const | None = template.block.init_eqs.get(fuel_flow, None)
            if fuel_flow_initial is None:
                fuel_flow_initial = Const(0.0)
            else:
                pass
            template.block.event_dict[delayed_fuel] = fuel_flow_initial
            template.block.procedural_logic.append(
                delay(
                    input_expr=fuel_flow,
                    T=settings.teng,
                    output=delayed_fuel,
                    name=f'GovCT1.FuelTransportDelay_{template_name}',
                )
            )
            runtime_block: Block = template.block
            turbine_algebraic_replaced: bool = False
            for algebraic_index in range(len(runtime_block.algebraic_eqs)):
                algebraic_equation = runtime_block.algebraic_eqs[algebraic_index]
                if (
                        algebraic_equation.contains_var(turbine_power)
                        and algebraic_equation.contains_var(fuel_flow)
                ):
                    runtime_block.algebraic_eqs[algebraic_index] = algebraic_equation.subs(
                        {fuel_flow: delayed_fuel},
                    )
                    turbine_algebraic_replaced = True
                else:
                    pass
            else:
                pass
            if not turbine_algebraic_replaced:
                raise ValueError('GovCT1 GGOV1 graph has no fuel-driven turbine output equation')
            else:
                pass
            if turbine_power_state is not None:
                turbine_state_replaced: bool = False
                for state_index in range(len(runtime_block.state_vars)):
                    state_variable: Var = runtime_block.state_vars[state_index]
                    state_equation: Expr = runtime_block.state_eqs[state_index]
                    if (
                            state_variable.uid == turbine_power_state.uid
                            and state_equation.contains_var(fuel_flow)
                    ):
                        runtime_block.state_eqs[state_index] = state_equation.subs(
                            {fuel_flow: delayed_fuel},
                        )
                        turbine_state_replaced = True
                    else:
                        pass
                else:
                    pass
                if not turbine_state_replaced:
                    raise ValueError('GovCT1 GGOV1 graph has no fuel-driven turbine state equation')
                else:
                    pass
            elif settings.tb > 0.0:
                raise ValueError('GovCT1 GGOV1 graph is missing its positive-time turbine state')
            else:
                pass
    else:
        pass
    template.comment = 'CGMES GovCT1 GGOV1 equations, including acceleration fuel limiting when ka is positive.'
    if settings.teng > 0.0:
        template.comment += (
            ' Fuel transport delay uses accepted-sample history with zero-order hold.'
        )
    else:
        pass
    return template
