# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES GovSteamFV4 electro-hydraulic steam governor."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class GovSteamFV4Parameters:
    """Runtime coefficients matching the exact GovSteamFV4 scalar attributes."""

    __slots__ = (
        'kf1', 'kf3', 'lps', 'lpi', 'mxef', 'mnef', 'crmx', 'crmn', 'kpt',
        'kit', 'rvgmx', 'rvgmn', 'svmx', 'svmn', 'srmx', 'srmn', 'kpp', 'kip',
        'rsmimx', 'rsmimn', 'kmp1', 'kmp2', 'srsmp', 'ta', 'tc', 'ty', 'yhpmx',
        'yhpmn', 'tam', 'tcm', 'ympmx', 'ympmn', 'y', 'thp', 'trh', 'tmp',
        'khp', 'pr1', 'pr2', 'psmn', 'kpc', 'kic', 'kdc', 'tdc', 'cpsmx',
        'cpsmn', 'krc', 'tf1', 'tf2', 'tv', 'ksh',
    )

    def __init__(
            self,
            kf1: float = 20.0, kf3: float = 20.0,
            lps: float = 0.03, lpi: float = -0.15,
            mxef: float = 0.05, mnef: float = -0.05,
            crmx: float = 1.2, crmn: float = 0.0,
            kpt: float = 0.3, kit: float = 0.04,
            rvgmx: float = 1.2, rvgmn: float = 0.0,
            svmx: float = 0.0333, svmn: float = -0.0333,
            srmx: float = 1.1, srmn: float = 0.0,
            kpp: float = 1.0, kip: float = 0.5,
            rsmimx: float = 1.1, rsmimn: float = 0.0,
            kmp1: float = 0.5, kmp2: float = 3.5, srsmp: float = 0.43,
            ta: float = 0.8, tc: float = 0.5, ty: float = 0.1,
            yhpmx: float = 1.1, yhpmn: float = 0.0,
            tam: float = 0.8, tcm: float = 0.5,
            ympmx: float = 1.1, ympmn: float = 0.0, y: float = 0.13,
            thp: float = 0.15, trh: float = 10.0, tmp: float = 0.4,
            khp: float = 0.35, pr1: float = 0.2, pr2: float = 0.75,
            psmn: float = 1.0, kpc: float = 0.5, kic: float = 0.0033,
            kdc: float = 1.0, tdc: float = 90.0,
            cpsmx: float = 1.0, cpsmn: float = -1.0, krc: float = 0.05,
            tf1: float = 10.0, tf2: float = 10.0, tv: float = 60.0,
            ksh: float = 0.08,
    ) -> None:
        """Store all 51 canonical model coefficients.

        :param kf1: Speed-feedback frequency bias.
        :param kf3: Fuel frequency-control bias.
        :param lps: Positive speed-load error limit.
        :param lpi: Negative speed-load error limit.
        :param mxef: Upper frequency-correction limit.
        :param mnef: Lower frequency-correction limit.
        :param crmx: Maximum regulator setpoint.
        :param crmn: Minimum regulator setpoint.
        :param kpt: Electro-hydraulic proportional gain.
        :param kit: Electro-hydraulic integral gain.
        :param rvgmx: Maximum electro-hydraulic integral state.
        :param rvgmn: Minimum electro-hydraulic integral state.
        :param svmx: Maximum gate-regulator opening speed.
        :param svmn: Minimum gate-regulator closing speed.
        :param srmx: Maximum servo-valve position.
        :param srmn: Minimum servo-valve position.
        :param kpp: Pressure-feedback proportional gain.
        :param kip: Pressure-feedback integral gain.
        :param rsmimx: Maximum pressure-controller integral state.
        :param rsmimn: Minimum pressure-controller integral state.
        :param kmp1: First intercept-valve characteristic slope.
        :param kmp2: Second intercept-valve characteristic slope.
        :param srsmp: Intercept-valve characteristic breakpoint.
        :param ta: Control-valve opening time.
        :param tc: Control-valve closing time.
        :param ty: Control-valve servo time.
        :param yhpmx: Maximum control-valve position.
        :param yhpmn: Minimum control-valve position.
        :param tam: Intercept-valve opening time.
        :param tcm: Intercept-valve closing time.
        :param ympmx: Maximum intercept-valve position.
        :param ympmn: Minimum intercept-valve position.
        :param y: Stodola turbine flow coefficient.
        :param thp: High-pressure turbine time.
        :param trh: Reheater time.
        :param tmp: Low-pressure turbine time.
        :param khp: High-pressure power fraction.
        :param pr1: First pressure-setpoint characteristic breakpoint.
        :param pr2: Second pressure-setpoint characteristic breakpoint.
        :param psmn: Minimum pressure-setpoint characteristic value.
        :param kpc: Pressure-regulator proportional gain.
        :param kic: Pressure-regulator integral gain.
        :param kdc: Pressure-regulator derivative gain.
        :param tdc: Pressure-regulator derivative time.
        :param cpsmx: Maximum pressure-regulator output.
        :param cpsmn: Minimum pressure-regulator output.
        :param krc: Maximum fuel-flow rate change.
        :param tf1: Fuel-regulator time.
        :param tf2: Steam-chest time.
        :param tv: Boiler time.
        :param ksh: Boiler tube friction pressure-loss coefficient.
        """
        self.kf1: float = kf1
        self.kf3: float = kf3
        self.lps: float = lps
        self.lpi: float = lpi
        self.mxef: float = mxef
        self.mnef: float = mnef
        self.crmx: float = crmx
        self.crmn: float = crmn
        self.kpt: float = kpt
        self.kit: float = kit
        self.rvgmx: float = rvgmx
        self.rvgmn: float = rvgmn
        self.svmx: float = svmx
        self.svmn: float = svmn
        self.srmx: float = srmx
        self.srmn: float = srmn
        self.kpp: float = kpp
        self.kip: float = kip
        self.rsmimx: float = rsmimx
        self.rsmimn: float = rsmimn
        self.kmp1: float = kmp1
        self.kmp2: float = kmp2
        self.srsmp: float = srsmp
        self.ta: float = ta
        self.tc: float = tc
        self.ty: float = ty
        self.yhpmx: float = yhpmx
        self.yhpmn: float = yhpmn
        self.tam: float = tam
        self.tcm: float = tcm
        self.ympmx: float = ympmx
        self.ympmn: float = ympmn
        self.y: float = y
        self.thp: float = thp
        self.trh: float = trh
        self.tmp: float = tmp
        self.khp: float = khp
        self.pr1: float = pr1
        self.pr2: float = pr2
        self.psmn: float = psmn
        self.kpc: float = kpc
        self.kic: float = kic
        self.kdc: float = kdc
        self.tdc: float = tdc
        self.cpsmx: float = cpsmx
        self.cpsmn: float = cpsmn
        self.krc: float = krc
        self.tf1: float = tf1
        self.tf2: float = tf2
        self.tv: float = tv
        self.ksh: float = ksh


def build_gov_steam_f_v4_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: GovSteamFV4Parameters | None = None,
) -> RmsModelTemplate:
    """Build FV4 speed, pressure, electro-hydraulic, boiler, and turbine paths.

    :param vfactory: Factory that owns all symbolic variables.
    :param name: Optional unique template name.
    :param parameters: Canonical CGMES fields; defaults are typical RDF values.
    :return: Equation-backed controller with machine-speed and power ports.
    :raises ValueError: Invalid times, limits, fractions, or pressure curve.
    """
    settings: GovSteamFV4Parameters = (
        GovSteamFV4Parameters() if parameters is None else parameters
    )
    parameter_values: tuple[tuple[str, float], ...] = (
            ('kf1', settings.kf1), ('kf3', settings.kf3), ('lps', settings.lps), ('lpi', settings.lpi),
            ('mxef', settings.mxef), ('mnef', settings.mnef), ('crmx', settings.crmx), ('crmn', settings.crmn),
            ('kpt', settings.kpt), ('kit', settings.kit), ('rvgmx', settings.rvgmx), ('rvgmn', settings.rvgmn),
            ('svmx', settings.svmx), ('svmn', settings.svmn), ('srmx', settings.srmx), ('srmn', settings.srmn),
            ('kpp', settings.kpp), ('kip', settings.kip), ('rsmimx', settings.rsmimx), ('rsmimn', settings.rsmimn),
            ('kmp1', settings.kmp1), ('kmp2', settings.kmp2), ('srsmp', settings.srsmp), ('ta', settings.ta),
            ('tc', settings.tc), ('ty', settings.ty), ('yhpmx', settings.yhpmx), ('yhpmn', settings.yhpmn),
            ('tam', settings.tam), ('tcm', settings.tcm), ('ympmx', settings.ympmx), ('ympmn', settings.ympmn),
            ('y', settings.y), ('thp', settings.thp), ('trh', settings.trh), ('tmp', settings.tmp),
            ('khp', settings.khp), ('pr1', settings.pr1), ('pr2', settings.pr2), ('psmn', settings.psmn),
            ('kpc', settings.kpc), ('kic', settings.kic), ('kdc', settings.kdc), ('tdc', settings.tdc),
            ('cpsmx', settings.cpsmx), ('cpsmn', settings.cpsmn), ('krc', settings.krc), ('tf1', settings.tf1),
            ('tf2', settings.tf2), ('tv', settings.tv), ('ksh', settings.ksh),
        )
    numeric_values: tuple[float, ...] = tuple(value for _, value in parameter_values)
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('CGMES GovSteamFV4 parameters must be finite')
    elif min(settings.tf1, settings.tf2, settings.tdc, settings.ty, settings.tv) < 0.0:
        raise ValueError('CGMES GovSteamFV4 time constants must be nonnegative')
    elif min(settings.ta, settings.tc, settings.tam, settings.tcm,
             settings.thp, settings.trh, settings.tmp) < 0.0:
        raise ValueError('CGMES GovSteamFV4 turbine time constants must be nonnegative')
    elif settings.crmn >= settings.crmx or settings.rvgmn >= settings.rvgmx:
        raise ValueError('CGMES GovSteamFV4 regulator limits must be ordered')
    elif settings.rsmimn >= settings.rsmimx or settings.cpsmn >= settings.cpsmx:
        raise ValueError('CGMES GovSteamFV4 pressure-integrator/output limits must be ordered')
    elif settings.svmn >= 0.0 or settings.svmx <= 0.0 or settings.srmn >= settings.srmx:
        raise ValueError('CGMES GovSteamFV4 servo rate and position limits are invalid')
    elif settings.yhpmn >= settings.yhpmx or settings.ympmn >= settings.ympmx:
        raise ValueError('CGMES GovSteamFV4 turbine valve limits must be ordered')
    elif not 0.0 < settings.khp < 1.0 or not 0.0 < settings.y < 1.0:
        raise ValueError('CGMES GovSteamFV4 requires turbine fraction and flow coefficient in (0, 1)')
    elif settings.pr1 >= settings.pr2 or settings.pr1 < 0.0 or settings.psmn <= 0.0:
        raise ValueError('CGMES GovSteamFV4 pressure setpoint curve is invalid')
    elif settings.srsmp <= settings.ympmn or settings.srsmp >= settings.ympmx:
        raise ValueError('CGMES GovSteamFV4 intercept curve breakpoint is outside limits')
    else:
        pass

    template_name: str = 'GovSteamFV4' if name is None else name
    control: ControlRealization = ControlRealization(vfactory, template_name)
    kf1: Var = control.parameter('kf1', settings.kf1)
    kf3: Var = control.parameter('kf3', settings.kf3)
    lps: Var = control.parameter('lps', settings.lps)
    lpi: Var = control.parameter('lpi', settings.lpi)
    mxef: Var = control.parameter('mxef', settings.mxef)
    mnef: Var = control.parameter('mnef', settings.mnef)
    crmx: Var = control.parameter('crmx', settings.crmx)
    crmn: Var = control.parameter('crmn', settings.crmn)
    kpt: Var = control.parameter('kpt', settings.kpt)
    kit: Var = control.parameter('kit', settings.kit)
    rvgmx: Var = control.parameter('rvgmx', settings.rvgmx)
    rvgmn: Var = control.parameter('rvgmn', settings.rvgmn)
    svmx: Var = control.parameter('svmx', settings.svmx)
    svmn: Var = control.parameter('svmn', settings.svmn)
    srmx: Var = control.parameter('srmx', settings.srmx)
    srmn: Var = control.parameter('srmn', settings.srmn)
    kpp: Var = control.parameter('kpp', settings.kpp)
    kip: Var = control.parameter('kip', settings.kip)
    rsmimx: Var = control.parameter('rsmimx', settings.rsmimx)
    rsmimn: Var = control.parameter('rsmimn', settings.rsmimn)
    kmp1: Var = control.parameter('kmp1', settings.kmp1)
    kmp2: Var = control.parameter('kmp2', settings.kmp2)
    srsmp: Var = control.parameter('srsmp', settings.srsmp)
    ta: Var = control.parameter('ta', settings.ta)
    tc: Var = control.parameter('tc', settings.tc)
    ty: Var = control.parameter('ty', settings.ty)
    yhpmx: Var = control.parameter('yhpmx', settings.yhpmx)
    yhpmn: Var = control.parameter('yhpmn', settings.yhpmn)
    tam: Var = control.parameter('tam', settings.tam)
    tcm: Var = control.parameter('tcm', settings.tcm)
    ympmx: Var = control.parameter('ympmx', settings.ympmx)
    ympmn: Var = control.parameter('ympmn', settings.ympmn)
    y: Var = control.parameter('y', settings.y)
    thp: Var = control.parameter('thp', settings.thp)
    trh: Var = control.parameter('trh', settings.trh)
    tmp: Var = control.parameter('tmp', settings.tmp)
    khp: Var = control.parameter('khp', settings.khp)
    pr1: Var = control.parameter('pr1', settings.pr1)
    pr2: Var = control.parameter('pr2', settings.pr2)
    psmn: Var = control.parameter('psmn', settings.psmn)
    kpc: Var = control.parameter('kpc', settings.kpc)
    kic: Var = control.parameter('kic', settings.kic)
    kdc: Var = control.parameter('kdc', settings.kdc)
    tdc: Var = control.parameter('tdc', settings.tdc)
    cpsmx: Var = control.parameter('cpsmx', settings.cpsmx)
    cpsmn: Var = control.parameter('cpsmn', settings.cpsmn)
    krc: Var = control.parameter('krc', settings.krc)
    tf1: Var = control.parameter('tf1', settings.tf1)
    tf2: Var = control.parameter('tf2', settings.tf2)
    tv: Var = control.parameter('tv', settings.tv)
    ksh: Var = control.parameter('ksh', settings.ksh)

    # The standard diagram uses the turbine MW base for all of these signal paths.
    omega: Var = control.input('OmegaPu', Const(1.0))
    power_reference: Var = control.input('PRefPu', Const(1.0))
    electrical_power: Var = control.input('PePu', power_reference)
    speed_error: Expr = Const(1.0) - omega
    frequency_bias: Expr = sym.hard_sat(kf1 * speed_error, lpi, lps)
    frequency_correction: Expr = sym.hard_sat(kf3 * speed_error, mnef, mxef)
    pressure_reference: Expr = psmn + (Const(1.0) - psmn) * sym.hard_sat(
        (power_reference - pr1) / (pr2 - pr1), Const(0.0), Const(1.0),
    )
    speed_reference: Var = control.algebraic(
        'GovSteamFV4RegulatorReferencePu',
        sym.hard_sat(power_reference + frequency_bias, crmn, crmx),
        Const(1.0),
    )

    # The electro-hydraulic PI, bounded gate servo, and KF3 branch form X.
    electro_error: Expr = speed_reference - electrical_power
    electro_integral: Var = vfactory.add_var(
        f'GovSteamFV4ElectroHydraulicIntegralPu_{template_name}'
    )
    control.differential(
        state=electro_integral,
        derivative=kit * electro_error,
        initial=Const(0.0),
        lower=rvgmn,
        upper=rvgmx,
    )
    electro_output: Var = control.algebraic(
        'GovSteamFV4ElectroHydraulicOutputPu',
        kpt * electro_error + electro_integral,
        Const(0.0),
    )
    electro_servo: Var = vfactory.add_var(
        f'GovSteamFV4ElectroHydraulicServoPu_{template_name}'
    )
    control.differential(
        state=electro_servo,
        derivative=sym.hard_sat(electro_output, svmn, svmx),
        initial=Const(0.0),
        lower=srmn,
        upper=srmx,
    )
    electro_control: Var = control.algebraic(
        'GovSteamFV4ElectroHydraulicControlPu',
        electro_servo + frequency_correction,
        Const(1.0),
    )

    # Boiler pressure feedback closes both pressure controllers and the turbine flow loop.
    boiler_pressure: Var = vfactory.add_var(
        f'GovSteamFV4BoilerPressurePu_{template_name}'
    )
    steam_flow: Var = vfactory.add_var(f'GovSteamFV4SteamFlowPu_{template_name}')
    pressure_feedback: Var = control.algebraic(
        'GovSteamFV4BoilerSteamPressurePu',
        boiler_pressure - ksh * steam_flow * steam_flow,
        Const(1.0),
    )
    pressure_error: Expr = pressure_reference - pressure_feedback

    # Pressure PID output CPS and pressure PI output SRSM follow separate diagram branches.
    pressure_integral: Var = vfactory.add_var(
        f'GovSteamFV4PressureIntegralPu_{template_name}'
    )
    control.differential(
        state=pressure_integral,
        derivative=kic * pressure_error,
        initial=Const(0.0),
        lower=cpsmn,
        upper=cpsmx,
    )
    pressure_derivative_filter: Var = control.lag(
        'GovSteamFV4PressureDerivativeFilterPu', pressure_error, tdc,
        settings.tdc, Const(0.0),
    )
    pressure_derivative: Var = control.algebraic(
        'GovSteamFV4PressureDerivativePu', -kdc * pressure_derivative_filter,
        Const(0.0),
    )
    pressure_output: Var = control.algebraic(
        'GovSteamFV4PressureControllerPu',
        sym.hard_sat((kpc + kdc) * pressure_error + pressure_integral + pressure_derivative,
                     cpsmn, cpsmx),
        Const(0.0),
    )
    valve_pressure_integral: Var = vfactory.add_var(
        f'GovSteamFV4ValvePressureIntegralPu_{template_name}'
    )
    control.differential(
        state=valve_pressure_integral,
        derivative=kip * pressure_error,
        initial=Const(0.0),
        lower=rsmimn,
        upper=rsmimx,
    )
    valve_pressure_reference: Var = control.algebraic(
        'GovSteamFV4ValvePressureReferencePu',
        kpp * pressure_error + valve_pressure_integral,
        Const(0.5),
    )

    # The fuel regulator integrates the limited correction around its unit bias.
    fuel_regulator: Var = vfactory.add_var(f'GovSteamFV4FuelRegulatorPu_{template_name}')
    fuel_regulator_error: Expr = (
        Const(1.0) + (pressure_output + frequency_bias) * electro_control - fuel_regulator
    )
    control.differential(
        state=fuel_regulator,
        derivative=sym.hard_sat(fuel_regulator_error, -krc, krc),
        initial=Const(1.0),
        lower=crmn,
        upper=crmx,
    )
    fuel_flow: Var = control.lag(
        'GovSteamFV4FuelFlowPu', fuel_regulator, tf1, settings.tf1,
        Const(1.0),
    )
    boiler_input: Var = control.lag(
        'GovSteamFV4BoilerInputPu', fuel_flow, tf2, settings.tf2,
        Const(1.0),
    )

    # The control-valve PI command passes through asymmetric rate and position limits.
    if settings.ty == 0.0:
        control_valve: Var = control.algebraic(
            'GovSteamFV4ControlValvePu',
            sym.hard_sat(valve_pressure_reference, yhpmn, yhpmx),
            Const(0.5),
        )
    else:
        control_valve: Var = vfactory.add_var(
            f'GovSteamFV4ControlValvePu_{template_name}'
        )
        control_valve_error: Expr = valve_pressure_reference - control_valve
        if settings.ta > 0.0 and settings.tc > 0.0:
            control_valve_rate: Expr = sym.hard_sat(
                control_valve_error, Const(-1.0 / settings.tc), Const(1.0 / settings.ta),
            ) / ty
        elif settings.ta == 0.0 and settings.tc > 0.0:
            control_valve_rate = sym.max(control_valve_error / ty, Const(-1.0 / settings.tc))
        elif settings.tc == 0.0 and settings.ta > 0.0:
            control_valve_rate = sym.min(control_valve_error / ty, Const(1.0 / settings.ta))
        else:
            control_valve_rate = control_valve_error / ty
        control.differential(
            state=control_valve,
            derivative=control_valve_rate,
            initial=Const(0.5),
            lower=yhpmn,
            upper=yhpmx,
        )

    # The intercept-valve curve is driven by SRSM, with its specified 0.1 bias.
    intercept_target: Expr = Const(0.1) + kmp1 * valve_pressure_reference + (
        kmp2 - kmp1
    ) * sym.max(valve_pressure_reference - srsmp, Const(0.0))
    if settings.ty == 0.0:
        intercept_valve: Var = control.algebraic(
            'GovSteamFV4InterceptValvePu',
            sym.hard_sat(intercept_target, ympmn, ympmx),
            Const(0.5),
        )
    else:
        intercept_valve: Var = vfactory.add_var(
            f'GovSteamFV4InterceptValvePu_{template_name}'
        )
        intercept_error: Expr = sym.hard_sat(intercept_target, ympmn, ympmx) - intercept_valve
        if settings.tam > 0.0 and settings.tcm > 0.0:
            intercept_rate: Expr = sym.hard_sat(
                intercept_error, Const(-1.0 / settings.tcm), Const(1.0 / settings.tam),
            ) / ty
        elif settings.tam == 0.0 and settings.tcm > 0.0:
            intercept_rate = sym.max(intercept_error / ty, Const(-1.0 / settings.tcm))
        elif settings.tcm == 0.0 and settings.tam > 0.0:
            intercept_rate = sym.min(intercept_error / ty, Const(1.0 / settings.tam))
        else:
            intercept_rate = intercept_error / ty
        control.differential(
            state=intercept_valve,
            derivative=intercept_rate,
            initial=Const(0.5),
            lower=ympmn,
            upper=ympmx,
        )

    # Stodola coupling gives the HP turbine, reheater and LP turbine power paths.
    high_pressure_flow: Var = control.algebraic(
        'GovSteamFV4HighPressureFlowPu', control_valve * pressure_feedback,
        Const(0.5),
    )
    hp_power: Var = control.lag(
        'GovSteamFV4HighPressurePowerPu', high_pressure_flow, thp / (Const(1.0) - y),
        settings.thp / (1.0 - settings.y), Const(0.5),
    )
    reheater_power: Var = vfactory.add_var(
        f'GovSteamFV4ReheaterPowerPu_{template_name}'
    )
    reheater_flow_expression: Expr = (hp_power - y * reheater_power) / (Const(1.0) - y)
    control.block.algebraic_vars.append(steam_flow)
    control.block.algebraic_eqs.append(steam_flow - reheater_flow_expression)
    control.block.init_eqs[steam_flow] = Const(0.0)
    reheater_flow: Var = control.algebraic(
        'GovSteamFV4ReheaterFlowPu', steam_flow, Const(0.0),
    )
    reheater_return_flow: Expr = y * reheater_power
    if settings.trh == 0.0:
        control.block.algebraic_vars.append(reheater_power)
        control.block.algebraic_eqs.append(reheater_power - steam_flow / y)
        control.block.init_eqs[reheater_power] = Const(0.5)
    else:
        control.differential(
            state=reheater_power,
            derivative=(steam_flow - reheater_return_flow) / trh,
            initial=Const(0.5),
        )
    reheater_power_flow: Var = control.algebraic(
        'GovSteamFV4ReheaterPowerFlowPu', intercept_valve * reheater_power,
        Const(0.5),
    )
    lp_turbine_state: Var = control.lag(
        'GovSteamFV4LowPressureTurbineStatePu',
        reheater_power_flow, tmp, settings.tmp, Const(0.5),
    )
    lp_power: Var = control.algebraic(
        'GovSteamFV4LowPressurePowerPu', (Const(1.0) - khp) * lp_turbine_state,
        Const(0.5),
    )
    turbine_power: Var = control.algebraic(
        'gov.PmPu', khp * hp_power + lp_power, power_reference,
    )
    if settings.tv == 0.0:
        control.block.algebraic_vars.append(boiler_pressure)
        control.block.algebraic_eqs.append(boiler_input - steam_flow)
        control.block.init_eqs[boiler_pressure] = Const(1.0)
    else:
        control.differential(
            state=boiler_pressure,
            derivative=(boiler_input - steam_flow) / tv,
            initial=Const(1.0),
        )

    # Keep unused diagram labels coupled to their source coefficients for editing and inspection.
    # Retain secondary regulator limits as editable event parameters even when inactive.
    for parameter_name, parameter_value in parameter_values:
        parameter_variable: Var = vfactory.add_var(
            f'GovSteamFV4.{parameter_name}_{template_name}'
        )
        control.block.event_dict[parameter_variable] = vfactory.add_const(
            parameter_value,
            name=parameter_variable.name,
        )
    template: RmsModelTemplate = control.finish(
        (turbine_power,),
        'CGMES GovSteamFV4 electro-hydraulic steam governor',
    )
    template.comment = (
        'IEC 61970-302:2023-06 Figure 84 pressure and electro-hydraulic loops, '
        'rate-limited valve servos, boiler pressure loss, Stodola turbine coupling, '
        'and HP/reheater/LP power paths.'
    )
    return template
