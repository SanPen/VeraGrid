# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES IEEE DC4B excitation template."""

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.excitation_systems.dc_exciter import DcExciterParameters, RotatingLimiterLocation
from VeraGridEngine.Templates.Rms.excitation_systems.pid_rotating_exciter import (
    PidRotatingExciterKind,
    build_pid_rotating_exciter,
)
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var


class ExcIEEEDC4BParameters:
    """Parameter values declared by the canonical ExcIEEEDC4B RDF class."""

    __slots__ = (
        'ka', 'ta', 'kp', 'ki', 'kd', 'td', 'vrmax', 'vrmin', 'ke', 'te',
        'kf', 'tf', 'efd1', 'seefd1', 'efd2', 'seefd2', 'vemin', 'oelin',
        'uelin',
    )

    def __init__(
            self,
            ka: float = 1.0,
            ta: float = 0.2,
            kp: float = 20.0,
            ki: float = 20.0,
            kd: float = 20.0,
            td: float = 0.01,
            vrmax: float = 2.7,
            vrmin: float = -0.9,
            ke: float = 1.0,
            te: float = 0.8,
            kf: float = 0.0,
            tf: float = 1.0,
            efd1: float = 1.75,
            seefd1: float = 0.08,
            efd2: float = 2.33,
            seefd2: float = 0.27,
            vemin: float = 0.0,
            oelin: bool = True,
            uelin: bool = True,
    ) -> None:
        """Store the exact RDF parameter surface with EA typical defaults.

        :param ka: Amplifier gain.
        :param ta: Amplifier time constant in seconds.
        :param kp: Voltage error proportional gain.
        :param ki: Voltage error integral gain.
        :param kd: Voltage error derivative gain.
        :param td: Derivative filter time constant in seconds.
        :param vrmax: Amplifier output upper limit.
        :param vrmin: Amplifier output lower limit.
        :param ke: Exciter field constant.
        :param te: Exciter field time constant in seconds.
        :param kf: Field voltage washout gain.
        :param tf: Field washout time constant in seconds.
        :param efd1: First saturation voltage sample.
        :param seefd1: Saturation factor at ``efd1``.
        :param efd2: Second saturation voltage sample.
        :param seefd2: Saturation factor at ``efd2``.
        :param vemin: Exciter field voltage lower limit.
        :param oelin: Use the overexcitation low gate when true.
        :param uelin: Use the underexcitation high gate when true.
        """
        self.ka: float = ka
        self.ta: float = ta
        self.kp: float = kp
        self.ki: float = ki
        self.kd: float = kd
        self.td: float = td
        self.vrmax: float = vrmax
        self.vrmin: float = vrmin
        self.ke: float = ke
        self.te: float = te
        self.kf: float = kf
        self.tf: float = tf
        self.efd1: float = efd1
        self.seefd1: float = seefd1
        self.efd2: float = efd2
        self.seefd2: float = seefd2
        self.vemin: float = vemin
        self.oelin: bool = oelin
        self.uelin: bool = uelin


def build_exc_i_e_e_e_d_c4_b_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: ExcIEEEDC4BParameters | None = None,
) -> RmsModelTemplate:
    """Build DC4B bounded PID regulation and rotating field equations.

    The physical PID, terminal-powered amplifier, field saturation and washout
    use the shared RMS excitation kernel. CGMES-specific gate selectors and RDF
    property audit symbols are kept on this standalone catalog template.

    :param vfactory: Factory owning symbolic variables.
    :param name: Optional runtime model name.
    :param parameters: Parsed CGMES settings or EA typical defaults.
    :return: Equation-backed CGMES DC4B model.
    """
    settings: ExcIEEEDC4BParameters = (
        ExcIEEEDC4BParameters() if parameters is None else parameters
    )
    template_name: str = 'ExcIEEEDC4B' if name is None else name
    physical_parameters: DcExciterParameters = DcExciterParameters(
        tr=0.0,
        ka=settings.ka,
        ta=settings.ta,
        vrmax=settings.vrmax,
        vrmin=settings.vrmin,
        ke=settings.ke,
        te=settings.te,
        kf=settings.kf,
        tf=settings.tf,
        e1=settings.efd1,
        se1=settings.seefd1,
        e2=settings.efd2,
        se2=settings.seefd2,
        initial_field_voltage=1.0,
        field_min=settings.vemin,
    )
    minimum_location: RotatingLimiterLocation = (
        RotatingLimiterLocation.TAKEOVER_GATE
        if settings.uelin
        else RotatingLimiterLocation.SUMMATION
    )
    maximum_location: RotatingLimiterLocation = (
        RotatingLimiterLocation.TAKEOVER_GATE
        if settings.oelin
        else RotatingLimiterLocation.SUMMATION
    )
    template: RmsModelTemplate = build_pid_rotating_exciter(
        vf=vfactory,
        name=template_name,
        kind=PidRotatingExciterKind.BOUNDED_TERMINAL_SUPPLY,
        parameters=physical_parameters,
        kp=settings.kp,
        ki=settings.ki,
        kd=settings.kd,
        td=settings.td,
        minimum_location=minimum_location,
        maximum_location=maximum_location,
    )
    if settings.oelin is False:
        # The shared physical kernel accepts signed addition; CGMES defines OEL subtraction.
        oel_signal: Var | None = None
        for input_variable in template.block.in_vars:
            if input_variable.name == f'OelPu_{template_name}':
                oel_signal = input_variable
            else:
                pass
        if oel_signal is not None:
            oel_sign_substitution: dict[Var, Expr] = dict()
            oel_sign_substitution[oel_signal] = Const(0.0) - oel_signal
            for runtime_block in template.block.get_all_blocks():
                for equation_index, equation in enumerate(runtime_block.state_eqs):
                    runtime_block.state_eqs[equation_index] = equation.subs(
                        oel_sign_substitution,
                    )
                for equation_index, equation in enumerate(runtime_block.algebraic_eqs):
                    runtime_block.algebraic_eqs[equation_index] = equation.subs(
                        oel_sign_substitution,
                    )
        else:
            pass
    else:
        pass
    template.comment = 'CGMES ExcIEEEDC4B bounded terminal-powered PID exciter'
    for parameter_name in (
            'enabled', 'ka', 'ta', 'kp', 'ki', 'kd', 'td', 'vrmax', 'vrmin',
            'ke', 'te', 'kf', 'tf', 'efd1', 'seefd1', 'efd2', 'seefd2',
            'vemin', 'oelin', 'uelin',
    ):
        variable_name: str = f'ExcIEEEDC4B.{parameter_name}_{template_name}'
        parameter_variable: Var = vfactory.add_var(variable_name)
        template.block.event_dict[parameter_variable] = vfactory.add_const(
            value=None,
            name=variable_name,
        )
    return template
