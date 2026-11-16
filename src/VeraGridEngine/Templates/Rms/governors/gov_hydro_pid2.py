# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""CGMES GovHydroPID2 adapter to the PID hydraulic governor equations."""

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.governors.pidgov import (
    HydroDroopFeedback,
    PidHydroGovernorParameters,
    build_pidgov_template,
)


class GovHydroPID2Parameters:
    """Canonical GovHydroPID2 fields with their RDF names and units."""

    __slots__ = (
        'mwbase', 'treg', 'rperm', 'kp', 'ki', 'kd', 'ta', 'tb', 'velmax',
        'velmin', 'gmax', 'gmin', 'tw', 'd', 'g0', 'g1', 'p1', 'g2', 'p2',
        'p3', 'atw', 'feedbackSignal',
    )

    def __init__(
            self,
            mwbase: float = 100.0,
            treg: float = 0.02,
            rperm: float = 0.05,
            kp: float = 2.0,
            ki: float = 1.0,
            kd: float = 0.1,
            ta: float = 0.1,
            tb: float = 0.2,
            velmax: float = 0.2,
            velmin: float = -0.15,
            gmax: float = 1.0,
            gmin: float = 0.0,
            tw: float = 1.0,
            d: float = 0.5,
            g0: float = 0.08,
            g1: float = 0.4,
            p1: float = 0.3,
            g2: float = 0.7,
            p2: float = 0.65,
            p3: float = 1.0,
            atw: float = 1.0,
            feedbackSignal: bool = True,
    ) -> None:
        """Store the RDF fields without changing their names or units.

        :param mwbase: Governor power base in MW.
        :param treg: Droop-feedback measurement time in seconds.
        :param rperm: Permanent speed droop.
        :param kp: Proportional gain.
        :param ki: Integral gain.
        :param kd: Derivative gain.
        :param ta: Regulator filter time in seconds.
        :param tb: Gate servo time in seconds.
        :param velmax: Maximum gate opening rate in pu/s.
        :param velmin: Minimum gate closing rate in pu/s.
        :param gmax: Maximum gate position.
        :param gmin: Minimum gate position.
        :param tw: Water starting time in seconds.
        :param d: Turbine speed damping.
        :param g0: No-load gate characteristic point.
        :param g1: First gate characteristic point.
        :param p1: Power at ``g1``.
        :param g2: Second gate characteristic point.
        :param p2: Power at ``g2``.
        :param p3: Power at full gate.
        :param atw: Water-time multiplier.
        :param feedbackSignal: Select gate feedback when true, electrical-power feedback otherwise.
        """
        self.mwbase: float = mwbase
        self.treg: float = treg
        self.rperm: float = rperm
        self.kp: float = kp
        self.ki: float = ki
        self.kd: float = kd
        self.ta: float = ta
        self.tb: float = tb
        self.velmax: float = velmax
        self.velmin: float = velmin
        self.gmax: float = gmax
        self.gmin: float = gmin
        self.tw: float = tw
        self.d: float = d
        self.g0: float = g0
        self.g1: float = g1
        self.p1: float = p1
        self.g2: float = g2
        self.p2: float = p2
        self.p3: float = p3
        self.atw: float = atw
        self.feedbackSignal: bool = feedbackSignal


def get_gov_hydro_pid2_gate_for_power(
        parameters: GovHydroPID2Parameters,
        power: float,
) -> float | None:
    """Invert the monotone piecewise-linear gate/power curve.

    :param parameters: Canonical model coefficients.
    :param power: Turbine power in pu on ``mwbase``.
    :return: Gate position in pu, or ``None`` when the curve is not invertible.
    """
    if parameters.p1 <= 0.0 or parameters.p2 <= parameters.p1 or parameters.p3 <= parameters.p2:
        return None
    else:
        pass
    first_slope: float = parameters.p1 / (parameters.g1 - parameters.g0)
    second_slope: float = (parameters.p2 - parameters.p1) / (parameters.g2 - parameters.g1)
    third_slope: float = (parameters.p3 - parameters.p2) / (1.0 - parameters.g2)
    if power <= parameters.p1:
        gate: float = parameters.g0 + power / first_slope
    elif power <= parameters.p2:
        gate = parameters.g1 + (power - parameters.p1) / second_slope
    else:
        gate = parameters.g2 + (power - parameters.p2) / third_slope
    if parameters.gmin <= gate <= parameters.gmax:
        return gate
    else:
        return None


def build_gov_hydro_p_i_d2_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: GovHydroPID2Parameters | None = None,
) -> RmsModelTemplate:
    """Build the CGMES PID hydro control and turbine equation graph.

    :param vfactory: Factory that owns the runtime variables.
    :param name: Optional unique runtime name.
    :param parameters: Canonical GovHydroPID2 fields.
    :return: Equation-backed template with speed, reference, electrical-power, and Pm ports.
    """
    settings: GovHydroPID2Parameters = (
        GovHydroPID2Parameters() if parameters is None else parameters
    )
    feedback: HydroDroopFeedback = (
        HydroDroopFeedback.GATE_POSITION
        if settings.feedbackSignal
        else HydroDroopFeedback.ELECTRICAL_POWER
    )
    pid_parameters: PidHydroGovernorParameters = PidHydroGovernorParameters(
        droop=settings.rperm,
        detector_time=settings.treg,
        kp=settings.kp,
        ki=settings.ki,
        kd=settings.kd,
        controller_time=settings.ta,
        servo_time=settings.tb,
        damping=settings.d,
        g0=settings.g0,
        g1=settings.g1,
        p1=settings.p1,
        g2=settings.g2,
        p2=settings.p2,
        p3=settings.p3,
        gate_max=settings.gmax,
        gate_min=settings.gmin,
        water_factor=settings.atw,
        water_time=settings.tw,
        opening_rate=settings.velmax,
        closing_rate=settings.velmin,
        feedback=feedback,
    )
    template: RmsModelTemplate = build_pidgov_template(
        vf=vfactory,
        name='GovHydroPID2' if name is None else name,
        parameters=pid_parameters,
    )
    return template
