# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""PSS/E CIM5, CIM6 and CIMW induction-motor RMS equations."""

from __future__ import annotations

import math
from enum import Enum

import numpy as np
from scipy.optimize import OptimizeResult, root

import VeraGridEngine.Utils.Symbolic.symbolic as sym
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.auxiliary_functions import _build_diff_vars
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
from VeraGridEngine.Utils.procedural_logic import ProceduralLogicBase
from VeraGridEngine.Utils.procedural_logic import delay, flipflop, pickup_dropoff
from VeraGridEngine.enumerations import (
    DeviceType,
    VarPowerFlowReferenceType,
)


class PsseCimMotorModel(Enum):
    """Select the PSS/E load-motor torque convention."""

    CIM5 = 'CIM5'
    CIM6 = 'CIM6'
    CIMW = 'CIMW'


class PsseCimMotorType(Enum):
    """Select PSS/E motor type A or B circuit reduction."""

    TYPE_A = 1
    TYPE_B = 2


class PsseCimMotorParameters:
    """Store the PSS/E CIM load-motor source parameters and load bases."""

    __slots__ = (
        'ra', 'xa', 'xm', 'r1', 'x1', 'r2', 'x2', 'e1', 'se1', 'e2', 'se2',
        'mbase', 'pmult', 'load_mw', 'system_base_mva', 'inertia', 'vi', 'ti',
        'tb', 'damping', 'tnom', 'a', 'b', 'd', 'exponent', 'c0',
        'torque_reference', 'q_adjustment', 'operating_point',
    )

    def __init__(
            self,
            ra: float,
            xa: float,
            xm: float,
            r1: float,
            x1: float,
            r2: float,
            x2: float,
            e1: float,
            se1: float,
            e2: float,
            se2: float,
            mbase: float,
            pmult: float,
            load_mw: float,
            system_base_mva: float,
            inertia: float,
            vi: float,
            ti: float,
            tb: float,
            damping: float,
            tnom: float,
            a: float = 0.0,
            b: float = 0.0,
            d: float = 0.0,
            exponent: float = 1.0,
            c0: float | None = None,
            torque_reference: float | None = None,
            q_adjustment: float = 0.0,
            operating_point: tuple[float, ...] | None = None,
    ) -> None:
        """Store source-order machine data and the resolved system bases.

        :param ra: Stator resistance on motor MVA base.
        :param xa: Stator leakage reactance on motor MVA base.
        :param xm: Magnetizing reactance on motor MVA base.
        :param r1: First rotor-cage resistance.
        :param x1: First rotor-cage reactance.
        :param r2: Second rotor-cage resistance, zero for single cage.
        :param x2: Second rotor-cage reactance, zero for single cage.
        :param e1: First saturation voltage point.
        :param se1: Saturation factor at ``e1``.
        :param e2: Second saturation voltage point.
        :param se2: Saturation factor at ``e2``.
        :param mbase: Explicit motor MVA base, or zero to use ``pmult``.
        :param pmult: Motor share multiplier when ``mbase`` is zero.
        :param load_mw: Associated load MW used by the PSS/E base rule.
        :param system_base_mva: Network MVA base.
        :param inertia: Motor inertia on motor base.
        :param vi: Undervoltage relay threshold in per unit.
        :param ti: Undervoltage pickup time in cycles.
        :param tb: Breaker delay in cycles.
        :param damping: PSS/E CIM5 damping factor.
        :param tnom: CIM5/CIM6 starting torque at one per-unit speed.
        :param a: CIM6/CIMW quadratic torque coefficient.
        :param b: CIM6/CIMW linear torque coefficient.
        :param d: CIM5 damping exponent or CIM6/CIMW torque coefficient.
        :param exponent: CIM6/CIMW torque exponent.
        :param c0: CIM6 independent coefficient or initialized CIMW coefficient.
        :param torque_reference: Online torque ``To`` from load-flow initialization.
        :param q_adjustment: Initial Mvar-difference admittance on motor base.
        :param operating_point: Solved speed, fluxes, currents, torque and Q adjustment.
        """
        self.ra: float = ra
        self.xa: float = xa
        self.xm: float = xm
        self.r1: float = r1
        self.x1: float = x1
        self.r2: float = r2
        self.x2: float = x2
        self.e1: float = e1
        self.se1: float = se1
        self.e2: float = e2
        self.se2: float = se2
        self.mbase: float = mbase
        self.pmult: float = pmult
        self.load_mw: float = load_mw
        self.system_base_mva: float = system_base_mva
        self.inertia: float = inertia
        self.vi: float = vi
        self.ti: float = ti
        self.tb: float = tb
        self.damping: float = damping
        self.tnom: float = tnom
        self.a: float = a
        self.b: float = b
        self.d: float = d
        self.exponent: float = exponent
        self.c0: float | None = c0
        self.torque_reference: float | None = torque_reference
        self.q_adjustment: float = q_adjustment
        self.operating_point: tuple[float, ...] | None = operating_point


def default_psse_cim_motor_parameters(
        model: PsseCimMotorModel,
) -> PsseCimMotorParameters:
    """Create neutral editor values for a PSS/E CIM model template.

    These values make the model constructible in the catalog; DYR conversion
    must replace them with the complete source record and solved load bases.

    :param model: PSS/E torque-law model selection.
    :return: Neutral model parameters on matching 15 MVA bases.
    """
    tnom: float = 1.0
    a: float = 0.0
    b: float = 0.0
    d: float = 1.0 if model == PsseCimMotorModel.CIM5 else 0.0
    exponent: float = 1.0
    c0: float | None
    if model == PsseCimMotorModel.CIM6:
        c0 = 1.0
    elif model == PsseCimMotorModel.CIMW:
        c0 = 1.0
    else:
        c0 = None
    parameters: PsseCimMotorParameters = PsseCimMotorParameters(
        ra=0.0,
        xa=0.0759,
        xm=3.1241,
        r1=0.0085,
        x1=0.0759,
        r2=0.0,
        x2=0.0,
        e1=1.0,
        se1=0.0,
        e2=1.2,
        se2=0.0,
        mbase=15.0,
        pmult=1.0,
        load_mw=15.0,
        system_base_mva=15.0,
        inertia=0.4,
        vi=0.0,
        ti=0.0,
        tb=0.0,
        damping=d,
        tnom=tnom,
        a=a,
        b=b,
        d=d,
        exponent=exponent,
        c0=c0,
        torque_reference=1.0,
    )
    return parameters


def _validate_psse_cim_motor(
        model: PsseCimMotorModel,
        parameters: PsseCimMotorParameters,
) -> tuple[bool, float]:
    """Validate source values and return cage selection and motor-base ratio.

    :param model: PSS/E torque-law model selection.
    :param parameters: Source data and resolved load/system bases.
    :return: Whether the model is single cage and motor/system MVA ratio.
    :raises ValueError: If the PSS/E parameter contract is invalid.
    """
    numeric_values: tuple[float, ...] = (
        parameters.ra, parameters.xa, parameters.xm, parameters.r1,
        parameters.x1, parameters.r2, parameters.x2, parameters.e1,
        parameters.se1, parameters.e2, parameters.se2, parameters.mbase,
        parameters.pmult, parameters.load_mw, parameters.system_base_mva,
        parameters.inertia, parameters.vi, parameters.ti, parameters.tb,
        parameters.damping, parameters.tnom, parameters.a, parameters.b,
        parameters.d, parameters.exponent,
        parameters.q_adjustment,
    )
    finite_values: bool = all(math.isfinite(value) for value in numeric_values)
    if parameters.c0 is not None:
        finite_values = finite_values and math.isfinite(parameters.c0)
    else:
        pass
    if parameters.torque_reference is not None:
        finite_values = finite_values and math.isfinite(parameters.torque_reference)
    else:
        pass
    if parameters.operating_point is not None:
        finite_values = finite_values and (
            len(parameters.operating_point) == 9
            and all(math.isfinite(value) for value in parameters.operating_point)
        )
    else:
        pass

    if not finite_values:
        raise ValueError('PSS/E CIM motor parameters must be finite')
    elif (
        parameters.ra < 0.0 or parameters.xa < 0.0 or parameters.xm <= 0.0
        or parameters.r1 <= 0.0 or parameters.x1 < 0.0
        or parameters.r2 < 0.0 or parameters.x2 < 0.0
        or ((parameters.r2 == 0.0) != (parameters.x2 == 0.0))
        or parameters.e1 < 0.0 or parameters.e2 <= 0.0
        or parameters.se1 < 0.0 or parameters.se2 < 0.0
        or parameters.tnom < 0.0
    ):
        raise ValueError('PSS/E CIM motor requires valid stator and cage impedances')
    elif (
        parameters.inertia <= 0.0 or parameters.system_base_mva <= 0.0
        or parameters.load_mw <= 0.0 or parameters.mbase < 0.0
        or parameters.pmult < 0.0 or parameters.vi < 0.0
        or parameters.ti < 0.0 or parameters.tb < 0.0
    ):
        raise ValueError('PSS/E CIM motor requires positive inertia and resolved bases')
    elif model == PsseCimMotorModel.CIM6 and parameters.c0 is None:
        raise ValueError('CIM6 requires the source-defined independent C0 coefficient')
    else:
        pass

    motor_base_mva: float
    if parameters.mbase > 0.0:
        motor_base_mva = parameters.mbase
    else:
        motor_base_mva = parameters.pmult * parameters.load_mw
    if motor_base_mva <= 0.0:
        raise ValueError('PSS/E CIM motor base resolves to zero')
    else:
        pass
    single_cage: bool = parameters.r2 == 0.0 and parameters.x2 == 0.0
    base_ratio: float = motor_base_mva / parameters.system_base_mva
    result: tuple[bool, float] = (single_cage, base_ratio)
    return result


def calculate_cimw_c0(
        coefficient_a: float,
        coefficient_b: float,
        coefficient_d: float,
        exponent: float,
        initialized_speed: float,
) -> float:
    """Calculate the CIMW torque constant at its initialized rotor speed.

    :param coefficient_a: Speed-squared torque coefficient.
    :param coefficient_b: Speed torque coefficient.
    :param coefficient_d: Exponential torque coefficient.
    :param exponent: Exponent applied to rotor speed.
    :param initialized_speed: Solved initial rotor speed in per unit.
    :return: CIMW source-defined constant term.
    :raises ValueError: If any input or result is nonfinite.
    """
    source_values: tuple[float, ...] = (
        coefficient_a, coefficient_b, coefficient_d, exponent, initialized_speed,
    )
    if all(math.isfinite(value) for value in source_values):
        c0: float = (
            1.0 - coefficient_a * initialized_speed ** 2
            - coefficient_b * initialized_speed
            - coefficient_d * initialized_speed ** exponent
        )
    else:
        raise ValueError('CIMW C0 inputs must be finite')
    if math.isfinite(c0):
        return c0
    else:
        raise ValueError('CIMW C0 calculation is nonfinite')


def _saturation_coefficients(
        parameters: PsseCimMotorParameters,
) -> tuple[float, float]:
    """Reduce PSS/E's two saturation points to the CIM quadratic curve.

    :param parameters: PSS/E machine saturation values.
    :return: The source threshold and quadratic coefficient.
    """
    threshold: float = parameters.e1
    coefficient: float = 0.0
    if parameters.se1 > 0.0 and parameters.se2 > 0.0 and parameters.e1 != parameters.e2:
        saturation_ratio: float = math.sqrt(
            parameters.se1 * parameters.e1 / (parameters.se2 * parameters.e2)
        )
        if abs(saturation_ratio - 1.0) > 1.0e-12:
            threshold = parameters.e2 - (
                (parameters.e1 - parameters.e2) / (saturation_ratio - 1.0)
            )
            coefficient = (
                parameters.se2 * parameters.e2 * (saturation_ratio - 1.0) ** 2
                / (parameters.e1 - parameters.e2) ** 2
            )
        else:
            coefficient = 0.0
    else:
        coefficient = 0.0
    result: tuple[float, float] = (threshold, coefficient)
    return result


def _psse_cim_motor_equilibrium_residual(
        state: np.ndarray,
        parameters: PsseCimMotorParameters,
        model: PsseCimMotorModel,
        voltage_d: float,
        voltage_q: float,
        active_power_target: float,
        frequency_hz: float,
        reduction: tuple[float, float, float, float, float, float],
        saturation: tuple[float, float],
) -> np.ndarray:
    """Evaluate steady PSS/E CIM motor equations for the operating-point solve.

    :param state: Fluxes, currents, speed and online torque reference.
    :param parameters: Source saturation, torque and circuit values.
    :param model: PSS/E CIM mechanical model.
    :param voltage_d: Terminal d-axis voltage in per unit.
    :param voltage_q: Terminal q-axis voltage in per unit.
    :param active_power_target: Solved load active power on motor base.
    :param frequency_hz: PSS/E system frequency in hertz.
    :param reduction: ``Ll, Lp, Lpp, Tp0, Tpp0`` and armature resistance.
    :param saturation: Saturation voltage threshold and quadratic coefficient.
    :return: Eight steady-state residuals for the eight unknowns.
    """
    epr: float = float(state[0])
    epi: float = float(state[1])
    cage_real: float = float(state[2])
    cage_imaginary: float = float(state[3])
    current_d: float = float(state[4])
    current_q: float = float(state[5])
    omega: float = float(state[6])
    torque_reference: float = float(state[7])
    ll: float = reduction[0]
    lp: float = reduction[1]
    lpp: float = reduction[2]
    tp0: float = reduction[3]
    tpp0: float = reduction[4]
    resistance: float = reduction[5]
    constant_one: float = (lpp - ll) / max(lp - ll, 1.0e-12)
    constant_two: float = (lp - lpp) / max(lp - ll, 1.0e-12)
    constant_three: float = lp - ll
    constant_four: float = (lp - lpp) / max((lp - ll) ** 2, 1.0e-12)
    constant_five: float = (parameters.xa + parameters.xm) - lp
    eppr: float = constant_one * epr + constant_two * cage_real
    eppi: float = constant_one * epi + constant_two * cage_imaginary
    epp: float = math.sqrt(eppr ** 2 + eppi ** 2)
    threshold: float = saturation[0]
    coefficient: float = saturation[1]
    saturation_voltage: float = coefficient * max(epp - threshold, 0.0) ** 2 / max(epp, 1.0e-12)
    saturation_ratio: float = saturation_voltage / max(epp, 1.0e-12)
    slip: float = 1.0 - omega
    angular_frequency: float = 2.0 * math.pi * frequency_hz
    epr_equation: float = (
        eppi * saturation_ratio
        + epi * tp0 * angular_frequency * slip
        - epr
        - ((epr - cage_real - current_q * constant_three) * constant_four + current_q)
        * constant_five
    )
    epi_equation: float = (
        (current_d - (current_d * constant_three + epi - cage_imaginary) * constant_four)
        * constant_five
        - epr * tp0 * angular_frequency * slip
        - saturation_ratio * eppr
        - epi
    )
    cage_real_equation: float = (
        tpp0 * angular_frequency * slip * cage_imaginary
        + epr - cage_real - current_q * constant_three
    )
    cage_imaginary_equation: float = (
        current_d * constant_three + epi - cage_imaginary
        - cage_real * tpp0 * angular_frequency * slip
    )
    voltage_d_equation: float = voltage_d - eppr - resistance * current_d + lpp * current_q
    voltage_q_equation: float = voltage_q - eppi - resistance * current_q - lpp * current_d
    active_power_equation: float = (
        voltage_d * current_d + voltage_q * current_q - active_power_target
    )
    electromagnetic_torque: float = eppr * current_d + eppi * current_q
    torque_curve: float
    if model == PsseCimMotorModel.CIM5:
        torque_curve = omega ** parameters.damping
    else:
        c0_value: float
        if model == PsseCimMotorModel.CIMW:
            c0_value = calculate_cimw_c0(
                coefficient_a=parameters.a,
                coefficient_b=parameters.b,
                coefficient_d=parameters.d,
                exponent=parameters.exponent,
                initialized_speed=omega,
            )
        else:
            c0_value = float(parameters.c0)
        torque_curve = (
            parameters.a * omega ** 2 + parameters.b * omega
            + c0_value + parameters.d * omega ** parameters.exponent
        )
    mechanical_equation: float = electromagnetic_torque - torque_reference * torque_curve
    residual: np.ndarray = np.array((
        epr_equation,
        epi_equation,
        cage_real_equation,
        cage_imaginary_equation,
        voltage_d_equation,
        voltage_q_equation,
        active_power_equation,
        mechanical_equation,
    ), dtype=np.float64)
    return residual


def solve_psse_cim_motor_operating_point(
        model: PsseCimMotorModel,
        motor_type: PsseCimMotorType,
        parameters: PsseCimMotorParameters,
        voltage_magnitude: float,
        voltage_angle: float,
        active_power_target: float,
        reactive_power_target: float,
        nominal_frequency_hz: float,
) -> tuple[float, float, float, float, float, float, float, float, float] | None:
    """Solve PSS/E CIM motor steady fluxes, speed, torque and Q adjustment.

    PSS/E selects the motor slip from the solved active load. The online shaft
    torque is then the equilibrium electromagnetic torque, and the manual's
    Mvar-difference admittance reconciles the motor reactive power to the
    solved load flow.

    :param model: CIM5, CIM6 or CIMW torque convention.
    :param motor_type: PSS/E Type A or Type B circuit.
    :param parameters: Source circuit and torque parameters.
    :param voltage_magnitude: Solved bus voltage magnitude in per unit.
    :param voltage_angle: Solved bus voltage angle in radians.
    :param active_power_target: Positive motor active load on its MVA base.
    :param reactive_power_target: Positive motor reactive load on its MVA base.
    :param nominal_frequency_hz: PSS/E system frequency in hertz.
    :return: Speed, Epr/Epi/Ekr/Eki, Id/Iq, online torque reference and Q admittance.
    """
    target_values: tuple[float, ...] = (
        voltage_magnitude, voltage_angle, active_power_target,
        reactive_power_target, nominal_frequency_hz,
    )
    if not all(math.isfinite(value) for value in target_values):
        result = None
    elif (
        voltage_magnitude <= 0.0 or active_power_target <= 0.0
        or nominal_frequency_hz <= 0.0
    ):
        result = None
    else:
        single_cage: bool
        motor_base_ratio: float
        single_cage, motor_base_ratio = _validate_psse_cim_motor(model, parameters)
        ll: float = parameters.xa
        lp: float = parameters.xa + parameters.x1 * parameters.xm / (parameters.x1 + parameters.xm)
        if single_cage:
            lpp: float = lp
            tp0: float = (parameters.x1 + parameters.xm) / (
                2.0 * math.pi * nominal_frequency_hz * parameters.r1
            )
            tpp0: float = 1.0e-7
        elif motor_type == PsseCimMotorType.TYPE_A:
            lpp = parameters.xa + (
                parameters.x1 * parameters.xm * parameters.x2
                / (parameters.x1 * parameters.x2 + parameters.x1 * parameters.xm
                   + parameters.x2 * parameters.xm)
            )
            tp0 = (parameters.x1 + parameters.xm) / (
                2.0 * math.pi * nominal_frequency_hz * parameters.r1
            )
            tpp0 = (
                parameters.x2 + parameters.x1 * parameters.xm / (parameters.x1 + parameters.xm)
            ) / (2.0 * math.pi * nominal_frequency_hz * parameters.r2)
        else:
            lpp = parameters.xa + (
                parameters.xm * (parameters.x1 + parameters.x2)
                / (parameters.x1 + parameters.x2 + parameters.xm)
            )
            tp0 = (parameters.x1 + parameters.x2 + parameters.xm) / (
                2.0 * math.pi * nominal_frequency_hz * parameters.r2
            )
            tpp0 = (
                (parameters.x1 + parameters.xm) * parameters.x2
                / (parameters.x1 + parameters.xm + parameters.x2)
            ) / (2.0 * math.pi * nominal_frequency_hz * parameters.r1)
        reduction: tuple[float, float, float, float, float, float] = (
            ll, lp, lpp, tp0, tpp0, parameters.ra,
        )
        saturation: tuple[float, float] = _saturation_coefficients(parameters)
        voltage_d: float = -voltage_magnitude * math.sin(voltage_angle)
        voltage_q: float = voltage_magnitude * math.cos(voltage_angle)
        current_d_guess: float = reactive_power_target / voltage_magnitude
        current_q_guess: float = active_power_target / voltage_magnitude
        epr_guess: float = voltage_d - parameters.ra * current_d_guess + lpp * current_q_guess
        epi_guess: float = voltage_q - parameters.ra * current_q_guess - lpp * current_d_guess
        initial_torque: float = max(active_power_target, 1.0e-6)
        speed_guesses: tuple[float, ...] = (0.99, 0.97, 0.94, 0.90, 0.85, 0.75, 0.60)
        solved_values: np.ndarray | None = None
        speed_guess: float
        for speed_guess in speed_guesses:
            initial_state: np.ndarray = np.array((
                epr_guess, epi_guess, epr_guess, epi_guess,
                current_d_guess, current_q_guess, speed_guess,
                initial_torque / max(speed_guess, 1.0e-6),
            ), dtype=np.float64)
            solution: OptimizeResult = root(
                _psse_cim_motor_equilibrium_residual,
                initial_state,
                args=(
                    parameters, model, voltage_d, voltage_q, active_power_target,
                    nominal_frequency_hz, reduction, saturation,
                ),
                method='hybr',
                tol=1.0e-10,
            )
            solution_values: np.ndarray = np.asarray(solution.x, dtype=np.float64)
            residual_values: np.ndarray = _psse_cim_motor_equilibrium_residual(
                solution_values,
                parameters,
                model,
                voltage_d,
                voltage_q,
                active_power_target,
                nominal_frequency_hz,
                reduction,
                saturation,
            )
            solution_valid: bool = (
                solution.success
                and np.all(np.isfinite(solution_values))
                and np.all(np.isfinite(residual_values))
                and float(np.max(np.abs(residual_values))) <= 1.0e-7
                and 0.0 < float(solution_values[6]) <= 1.0
                and float(solution_values[7]) >= 0.0
            )
            if solution_valid:
                solved_values = solution_values
                break
            else:
                pass
        else:
            pass

        if solved_values is None:
            result = None
        else:
            solved_speed: float = float(solved_values[6])
            solved_epr: float = float(solved_values[0])
            solved_epi: float = float(solved_values[1])
            solved_cage_real: float = float(solved_values[2])
            solved_cage_imaginary: float = float(solved_values[3])
            solved_current_d: float = float(solved_values[4])
            solved_current_q: float = float(solved_values[5])
            solved_torque: float = float(solved_values[7])
            constant_one: float = (lpp - ll) / max(lp - ll, 1.0e-12)
            constant_two: float = (lp - lpp) / max(lp - ll, 1.0e-12)
            terminal_eppr: float = constant_one * solved_epr + constant_two * solved_cage_real
            terminal_eppi: float = constant_one * solved_epi + constant_two * solved_cage_imaginary
            motor_reactive_power: float = (
                voltage_q * solved_current_d - voltage_d * solved_current_q
            )
            q_admittance: float = (
                reactive_power_target - motor_reactive_power
            ) / (voltage_magnitude ** 2)
            if math.isfinite(q_admittance) and math.isfinite(motor_base_ratio):
                result = (
                    solved_speed, solved_epr, solved_epi, solved_cage_real,
                    solved_cage_imaginary, solved_current_d, solved_current_q,
                    solved_torque, q_admittance,
                )
            else:
                result = None
    return result


def build_psse_cim_motor_template(
        vf: VarFactory,
        model: PsseCimMotorModel,
        motor_type: PsseCimMotorType,
        parameters: PsseCimMotorParameters,
        name: str | None = None,
        nominal_frequency_hz: float = 50.0,
) -> RmsModelTemplate:
    """Build PSS/E CIM5, CIM6 or CIMW induction-motor RMS equations.

    The circuit reductions and electrical state equations follow the OpenIPSL
    PSS/E CIM implementation archived with the research sources. P/Q are
    converted from motor base to system base, and the undervoltage relay uses
    PSS/E cycle-valued timing parameters.

    :param vf: Variable factory used for symbolic model construction.
    :param model: CIM5, CIM6 or CIMW mechanical torque law.
    :param motor_type: PSS/E Type A or Type B rotor-cage circuit.
    :param parameters: PSS/E record data and resolved load bases.
    :param name: Optional runtime instance name.
    :param nominal_frequency_hz: System frequency used by PSS/E time constants.
    :return: Native RMS load template for the selected PSS/E CIM model.
    :raises ValueError: If model parameters or frequency are invalid.
    """
    if not math.isfinite(nominal_frequency_hz) or nominal_frequency_hz <= 0.0:
        raise ValueError('PSS/E CIM motor frequency must be finite and positive')
    else:
        pass
    single_cage: bool
    motor_to_system_base: float
    single_cage, motor_to_system_base = _validate_psse_cim_motor(
        model=model,
        parameters=parameters,
    )
    if model == PsseCimMotorModel.CIMW and parameters.c0 is None:
        raise ValueError('CIMW template requires C0 calculated from initialized motor speed')
    else:
        pass
    template_name: str = model.value if name is None else name
    template: RmsModelTemplate = RmsModelTemplate(name=template_name)
    template.tpe = DeviceType.LoadDevice

    # Terminal polar values are the device boundary; the PSS/E motor equations
    # use a network-reference d/q frame derived from these solved bus values.
    terminal_voltage: Var = vf.add_var(
        name=f'Vm_{template_name}', reference=VarPowerFlowReferenceType.Vm,
    )
    terminal_angle: Var = vf.add_var(
        name=f'Va_{template_name}', reference=VarPowerFlowReferenceType.Va,
    )
    voltage_d: Var = vf.add_var(name=f'VdPu_{template_name}')
    voltage_q: Var = vf.add_var(name=f'VqPu_{template_name}')
    current_d: Var = vf.add_var(name=f'IrPu_{template_name}')
    current_q: Var = vf.add_var(name=f'IiPu_{template_name}')
    omega: Var = vf.add_var(name=f'OmegaPu_{template_name}')
    epr: Var = vf.add_var(name=f'EprPu_{template_name}')
    epi: Var = vf.add_var(name=f'EpiPu_{template_name}')
    cage_real: Var = vf.add_var(name=f'EkrPu_{template_name}')
    cage_imaginary: Var = vf.add_var(name=f'EkiPu_{template_name}')
    state_variables: list[Var] = list((epr, epi, cage_real, cage_imaginary, omega))

    active_power: Var = vf.add_var(
        name=f'PLoadPu_{template_name}', reference=VarPowerFlowReferenceType.P,
    )
    reactive_power: Var = vf.add_var(
        name=f'QLoadPu_{template_name}', reference=VarPowerFlowReferenceType.Q,
    )
    electromagnetic_torque: Var = vf.add_var(name=f'TePu_{template_name}')
    load_torque: Var = vf.add_var(name=f'TLoadPu_{template_name}')
    torque_reference: Var = vf.add_var(name=f'ToPu_{template_name}')
    q_adjustment_variable: Var = vf.add_var(name=f'QADJUST_{template_name}')

    # The event table retains the named PSS/E values so imported records remain
    # inspectable and the source contract stays explicit in saved models.
    source_parameter_values: tuple[tuple[str, float | None], ...] = (
        ('RA', parameters.ra), ('XA', parameters.xa), ('XM', parameters.xm),
        ('R1', parameters.r1), ('X1', parameters.x1), ('R2', parameters.r2),
        ('X2', parameters.x2), ('E1', parameters.e1), ('SE1', parameters.se1),
        ('E2', parameters.e2), ('SE2', parameters.se2), ('MBASE', parameters.mbase),
        ('PMULT', parameters.pmult), ('H', parameters.inertia), ('VI', parameters.vi),
        ('TI', parameters.ti), ('TB', parameters.tb),
        ('D', parameters.damping if model == PsseCimMotorModel.CIM5 else parameters.d),
        ('TNOM', parameters.tnom), ('A', parameters.a), ('B', parameters.b),
        ('E', parameters.exponent), ('C0', parameters.c0),
    )
    event_parameters: dict[Var, Expr | Const] = dict()
    parameter_label: str
    parameter_value: float | None
    for parameter_label, parameter_value in source_parameter_values:
        event_variable: Var = vf.add_var(name=f'{parameter_label}_{template_name}')
        event_parameters[event_variable] = vf.add_const(value=parameter_value)
    torque_initial_value: float
    q_adjustment_initial_value: float = parameters.q_adjustment
    if parameters.operating_point is None:
        torque_initial_value = parameters.torque_reference or parameters.tnom
    else:
        torque_initial_value = parameters.operating_point[7]
        q_adjustment_initial_value = parameters.operating_point[8]
    event_parameters[torque_reference] = vf.add_const(value=torque_initial_value)
    event_parameters[q_adjustment_variable] = vf.add_const(value=q_adjustment_initial_value)

    # These exact reductions distinguish the PSS/E type-A and type-B circuits.
    pi: Const = vf.add_const(value=math.pi)
    two: Const = vf.add_const(value=2.0)
    frequency_base: Expr = two * pi * vf.add_const(value=nominal_frequency_hz)
    xa: Const = vf.add_const(value=parameters.xa)
    xm: Const = vf.add_const(value=parameters.xm)
    x1: Const = vf.add_const(value=parameters.x1)
    x2: Const = vf.add_const(value=parameters.x2)
    r1: Const = vf.add_const(value=parameters.r1)
    r2: Const = vf.add_const(value=parameters.r2)
    ra: Const = vf.add_const(value=parameters.ra)
    ll: Expr = xa
    ls: Expr = xa + xm
    lp: Expr = xa + x1 * xm / (x1 + xm)
    lpp: Expr
    tp0: Expr
    tpp0: Expr
    if single_cage:
        lpp = lp
        tp0 = (x1 + xm) / (frequency_base * r1)
        tpp0 = vf.add_const(value=1.0e-7)
    elif motor_type == PsseCimMotorType.TYPE_A:
        lpp = xa + x1 * xm * x2 / (x1 * x2 + x1 * xm + x2 * xm)
        tp0 = (x1 + xm) / (frequency_base * r1)
        tpp0 = (x2 + x1 * xm / (x1 + xm)) / (frequency_base * r2)
    else:
        lpp = xa + xm * (x1 + x2) / (x1 + x2 + xm)
        tp0 = (x1 + x2 + xm) / (frequency_base * r2)
        parallel_reactance: Expr = (x1 + xm) * x2 / (x1 + xm + x2)
        tpp0 = parallel_reactance / (frequency_base * r1)

    # The published equations use these five dimensionless flux coefficients.
    epsilon: Const = vf.add_const(value=1.0e-12)
    one: Const = vf.add_const(value=1.0)
    constant_one: Expr = (lpp - ll) / sym.max(lp - ll, epsilon)
    constant_two: Expr = (lp - lpp) / sym.max(lp - ll, epsilon)
    constant_three: Expr = lp - ll
    constant_four: Expr = (lp - lpp) / sym.max((lp - ll) ** 2, epsilon)
    constant_five: Expr = ls - lp
    slip: Expr = one - omega
    eppr: Expr = constant_one * epr + constant_two * cage_real
    eppi: Expr = constant_one * epi + constant_two * cage_imaginary

    # PSS/E's saturation law is a thresholded quadratic divided by voltage.
    saturation_threshold, saturation_gain = _saturation_coefficients(parameters)
    epp: Expr = sym.sqrt(eppr ** 2 + eppi ** 2)
    saturation: Expr = (
        vf.add_const(value=saturation_gain)
        * sym.max(epp - vf.add_const(value=saturation_threshold), vf.add_const(value=0.0)) ** 2
        / sym.max(epp, epsilon)
    )
    saturation_ratio: Expr = saturation / sym.max(epp, epsilon)

    # The five-state two-cage flux equations are transcribed from the archived
    # PSS/E CIM model reference; the one-cage branch removes the redundant cage.
    epr_derivative: Expr = (
        eppi * saturation_ratio
        + epi * (tp0 * frequency_base * slip)
        - epr
        - ((epr - cage_real - current_q * constant_three) * constant_four + current_q)
        * constant_five
    ) / tp0
    epi_derivative: Expr = (
        (current_d - (current_d * constant_three + epi - cage_imaginary) * constant_four)
        * constant_five
        - epr * (tp0 * frequency_base * slip)
        - saturation_ratio * eppr
        - epi
    ) / tp0
    cage_real_derivative: Expr = (
        (tpp0 * frequency_base * slip) * cage_imaginary
        + epr - cage_real - current_q * constant_three
    ) / tpp0
    cage_imaginary_derivative: Expr = (
        current_d * constant_three + epi - cage_imaginary
        - cage_real * (tpp0 * frequency_base * slip)
    ) / tpp0

    torque_curve: Expr
    if model == PsseCimMotorModel.CIM5:
        torque_curve = torque_reference * omega ** vf.add_const(value=parameters.damping)
    elif model == PsseCimMotorModel.CIM6:
        torque_curve = torque_reference * (
            vf.add_const(value=parameters.a) * omega ** 2
            + vf.add_const(value=parameters.b) * omega
            + vf.add_const(value=float(parameters.c0))
            + vf.add_const(value=parameters.d) * omega ** vf.add_const(value=parameters.exponent)
        )
    else:
        torque_curve = torque_reference * (
            vf.add_const(value=parameters.a) * omega ** 2
            + vf.add_const(value=parameters.b) * omega
            + vf.add_const(value=float(parameters.c0))
            + vf.add_const(value=parameters.d) * omega ** vf.add_const(value=parameters.exponent)
        )
    electromagnetic_torque_expression: Expr = eppr * current_d + eppi * current_q
    state_equations: list[Expr] = list((
        epr_derivative,
        epi_derivative,
        cage_real_derivative,
        cage_imaginary_derivative,
        (electromagnetic_torque_expression - load_torque) /
        (two * vf.add_const(value=parameters.inertia)),
    ))

    # The relay timers are expressed in seconds internally; PSS/E stores cycles.
    breaker_open: Var = vf.add_var(name=f'BreakerOpen_{template_name}')
    relay_timer: Var = vf.add_var(name=f'RelayTimerComplete_{template_name}')
    breaker_command: Var = vf.add_var(name=f'BreakerCommandDelayed_{template_name}')
    event_parameters[breaker_open] = vf.add_const(value=0.0)
    event_parameters[relay_timer] = vf.add_const(value=0.0)
    event_parameters[breaker_command] = vf.add_const(value=0.0)
    procedural_logic: list[ProceduralLogicBase] = list()
    if parameters.vi > 0.0:
        relay_pickup_seconds: Expr = vf.add_const(value=parameters.ti / nominal_frequency_hz)
        breaker_delay_seconds: Expr = vf.add_const(value=parameters.tb / nominal_frequency_hz)
        procedural_logic.extend((
            pickup_dropoff(
                output=relay_timer,
                boolexpr=terminal_voltage < vf.add_const(value=parameters.vi),
                Tpick=relay_pickup_seconds,
                Tdrop=vf.add_const(value=0.0),
                name=f'{template_name}_undervoltage_timer',
            ),
            delay(
                input_expr=relay_timer,
                T=breaker_delay_seconds,
                output=breaker_command,
                name=f'{template_name}_breaker_delay',
            ),
            flipflop(
                boolset=breaker_command > vf.add_const(value=0.5),
                boolreset=vf.add_const(value=0.0) < vf.add_const(value=0.0),
                output=breaker_open,
                name=f'{template_name}_breaker_latch',
            ),
        ))
    else:
        pass

    breaker_closed: Expr = vf.add_const(value=1.0) - breaker_open
    motor_to_system: Const = vf.add_const(value=motor_to_system_base)
    active_power_expression: Expr = (
        breaker_closed * motor_to_system * (voltage_d * current_d + voltage_q * current_q)
    )
    reactive_power_expression: Expr = (
        breaker_closed * motor_to_system * (
            voltage_q * current_d - voltage_d * current_q
            + q_adjustment_variable * terminal_voltage ** 2
        )
    )
    algebraic_variables: list[Var] = list((
        voltage_d, voltage_q, current_d, current_q, electromagnetic_torque,
        load_torque, active_power, reactive_power,
    ))
    algebraic_equations: list[Expr] = list((
        voltage_d + terminal_voltage * sym.sin(terminal_angle),
        voltage_q - terminal_voltage * sym.cos(terminal_angle),
        voltage_d - eppr - ra * current_d + lpp * current_q,
        voltage_q - eppi - ra * current_q - lpp * current_d,
        electromagnetic_torque - electromagnetic_torque_expression,
        load_torque - torque_curve,
        active_power - active_power_expression,
        reactive_power - reactive_power_expression,
    ))
    initialization_equations: dict[Var, Expr] = dict()
    initialization_equations[voltage_d] = -terminal_voltage * sym.sin(terminal_angle)
    initialization_equations[voltage_q] = terminal_voltage * sym.cos(terminal_angle)
    initialization_equations[active_power] = active_power_expression
    initialization_equations[reactive_power] = reactive_power_expression
    if parameters.operating_point is not None:
        initialization_equations[epr] = vf.add_const(value=parameters.operating_point[1])
        initialization_equations[epi] = vf.add_const(value=parameters.operating_point[2])
        initialization_equations[cage_real] = vf.add_const(value=parameters.operating_point[3])
        initialization_equations[cage_imaginary] = vf.add_const(value=parameters.operating_point[4])
        initialization_equations[omega] = vf.add_const(value=parameters.operating_point[0])
    else:
        pass
    template.block = Block(
        state_vars=state_variables,
        diff_vars=_build_diff_vars(vf=vf, state_vars=state_variables),
        state_eqs=state_equations,
        algebraic_vars=algebraic_variables,
        algebraic_eqs=algebraic_equations,
        init_eqs=initialization_equations,
        event_dict=event_parameters,
        procedural_logic=procedural_logic,
        in_vars=[terminal_voltage, terminal_angle],
        out_vars=[active_power, reactive_power, omega, electromagnetic_torque, breaker_open],
        name=template_name,
    )
    template.block.external_mapping = {
        VarPowerFlowReferenceType.Vm: terminal_voltage,
        VarPowerFlowReferenceType.Va: terminal_angle,
        VarPowerFlowReferenceType.P: active_power,
        VarPowerFlowReferenceType.Q: reactive_power,
    }
    cage_description: str
    if single_cage:
        cage_description = 'one-cage'
    else:
        cage_description = 'two-cage'
    template.comment = (
        f'PSS/E {model.value} {motor_type.name} {cage_description} induction motor; '
        'P/Q are converted from motor base to system base. '
        'Online torque reference must be seeded from the solved motor operating point.'
    )
    return template


def build_cim5_template(
        vf: VarFactory,
        name: str | None = None,
        parameters: PsseCimMotorParameters | None = None,
        motor_type: PsseCimMotorType = PsseCimMotorType.TYPE_A,
) -> RmsModelTemplate:
    """Build the catalog-facing PSS/E CIM5 motor template.

    :param vf: Variable factory used for symbolic model construction.
    :param name: Optional runtime instance name.
    :param parameters: Optional complete source and load-base values.
    :param motor_type: PSS/E Type A or Type B circuit.
    :return: Native CIM5 load-motor template.
    """
    selected_parameters: PsseCimMotorParameters
    if parameters is None:
        selected_parameters = default_psse_cim_motor_parameters(PsseCimMotorModel.CIM5)
    else:
        selected_parameters = parameters
    template: RmsModelTemplate = build_psse_cim_motor_template(
        vf=vf,
        model=PsseCimMotorModel.CIM5,
        motor_type=motor_type,
        parameters=selected_parameters,
        name=name,
    )
    return template


def build_cim6_template(
        vf: VarFactory,
        name: str | None = None,
        parameters: PsseCimMotorParameters | None = None,
        motor_type: PsseCimMotorType = PsseCimMotorType.TYPE_A,
) -> RmsModelTemplate:
    """Build the catalog-facing PSS/E CIM6 motor template.

    :param vf: Variable factory used for symbolic model construction.
    :param name: Optional runtime instance name.
    :param parameters: Optional complete source and load-base values.
    :param motor_type: PSS/E Type A or Type B circuit.
    :return: Native CIM6 load-motor template.
    """
    selected_parameters: PsseCimMotorParameters
    if parameters is None:
        selected_parameters = default_psse_cim_motor_parameters(PsseCimMotorModel.CIM6)
    else:
        selected_parameters = parameters
    template: RmsModelTemplate = build_psse_cim_motor_template(
        vf=vf,
        model=PsseCimMotorModel.CIM6,
        motor_type=motor_type,
        parameters=selected_parameters,
        name=name,
    )
    return template


def build_cimw_psse_template(
        vf: VarFactory,
        name: str | None = None,
        parameters: PsseCimMotorParameters | None = None,
        motor_type: PsseCimMotorType = PsseCimMotorType.TYPE_A,
) -> RmsModelTemplate:
    """Build the catalog-facing PSS/E CIMW motor template.

    :param vf: Variable factory used for symbolic model construction.
    :param name: Optional runtime instance name.
    :param parameters: Optional complete source and load-base values.
    :param motor_type: PSS/E Type A or Type B circuit.
    :return: Native CIMW load-motor template.
    """
    selected_parameters: PsseCimMotorParameters
    if parameters is None:
        selected_parameters = default_psse_cim_motor_parameters(PsseCimMotorModel.CIMW)
    else:
        selected_parameters = parameters
    template: RmsModelTemplate = build_psse_cim_motor_template(
        vf=vf,
        model=PsseCimMotorModel.CIMW,
        motor_type=motor_type,
        parameters=selected_parameters,
        name=name,
    )
    return template
