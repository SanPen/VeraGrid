# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES IEEE ST2A compound-source excitation template."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.excitation_systems.exst2 import (
    CompoundExciterKind,
    build_exst2_template,
)
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Var


class ExcIEEEST2AParameters:
    """Parameter values declared by the canonical ExcIEEEST2A RDF class."""

    __slots__ = (
        'ka', 'ta', 'vrmax', 'vrmin', 'ke', 'te', 'kf', 'tf', 'kp', 'ki',
        'kc', 'efdmax', 'uelin',
    )

    def __init__(
            self,
            ka: float = 120.0,
            ta: float = 0.15,
            vrmax: float = 1.0,
            vrmin: float = 0.0,
            ke: float = 1.0,
            te: float = 0.5,
            kf: float = 0.05,
            tf: float = 1.0,
            kp: float = 4.88,
            ki: float = 8.0,
            kc: float = 1.82,
            efdmax: float = 99.0,
            uelin: bool = True,
    ) -> None:
        """Store exact RDF fields with EA typical-value defaults.

        :param ka: Voltage regulator gain.
        :param ta: Voltage regulator time in seconds.
        :param vrmax: Regulator output upper limit.
        :param vrmin: Regulator output lower limit.
        :param ke: Exciter field feedback coefficient.
        :param te: Field integration time in seconds.
        :param kf: Field voltage washout gain.
        :param tf: Field washout time in seconds.
        :param kp: Terminal potential source coefficient.
        :param ki: Current compounding source coefficient.
        :param kc: Rectifier commutation loading coefficient.
        :param efdmax: Field voltage upper limit.
        :param uelin: Select high gate when true, additive error when false.
        """
        self.ka: float = ka
        self.ta: float = ta
        self.vrmax: float = vrmax
        self.vrmin: float = vrmin
        self.ke: float = ke
        self.te: float = te
        self.kf: float = kf
        self.tf: float = tf
        self.kp: float = kp
        self.ki: float = ki
        self.kc: float = kc
        self.efdmax: float = efdmax
        self.uelin: bool = uelin


def build_exc_i_e_e_e_s_t2_a_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: ExcIEEEST2AParameters | None = None,
) -> RmsModelTemplate:
    """Build compound-source bridge, regulator, and bounded field equations.

    :param vfactory: Factory allocating the symbolic model variables.
    :param name: Optional unique runtime model name.
    :param parameters: Parsed CGMES settings or EA typical defaults.
    :return: Equation-backed CGMES ST2A model with terminal phasor ports.
    :raises ValueError: Invalid parameter data.
    """
    settings: ExcIEEEST2AParameters = (
        ExcIEEEST2AParameters() if parameters is None else parameters
    )
    template_name: str = 'ExcIEEEST2A' if name is None else name
    values: tuple[float, ...] = (
        settings.ka, settings.ta, settings.vrmax, settings.vrmin, settings.ke,
        settings.te, settings.kf, settings.tf, settings.kp, settings.ki,
        settings.kc, settings.efdmax,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('ExcIEEEST2A parameters must be finite')
    elif settings.ka <= 0.0 or settings.te <= 0.0 or settings.tf <= 0.0:
        raise ValueError('ExcIEEEST2A KA, TE, and TF must be positive')
    elif settings.ta < 0.0 or min(settings.kf, settings.kp, settings.ki, settings.kc, settings.ke) < 0.0:
        raise ValueError('ExcIEEEST2A times and gains must be nonnegative')
    elif settings.vrmin >= settings.vrmax or settings.efdmax <= 0.0:
        raise ValueError('ExcIEEEST2A regulator or field limits are invalid')
    else:
        pass

    kind: CompoundExciterKind = (
        CompoundExciterKind.GATED_MULTIPLICATIVE_BRIDGE
        if settings.uelin
        else CompoundExciterKind.MULTIPLICATIVE_BRIDGE
    )
    template: RmsModelTemplate = build_exst2_template(
        vf=vfactory,
        name=template_name,
        transducer_time=0.0,
        regulator_gain=settings.ka,
        regulator_time=settings.ta,
        regulator_max=settings.vrmax,
        regulator_min=settings.vrmin,
        field_feedback=settings.ke,
        exciter_time=settings.te,
        rate_gain=settings.kf,
        rate_time=settings.tf,
        potential_gain=settings.kp,
        current_gain=settings.ki,
        commutation_gain=settings.kc,
        field_max=settings.efdmax,
        initial_field_voltage=min(1.0, settings.efdmax),
        kind=kind,
    )
    if settings.uelin is False:
        error_variable: Var | None = None
        for algebraic_variable in template.block.algebraic_vars:
            if algebraic_variable.name == f'ErrorPu_{template_name}':
                error_variable = algebraic_variable
            else:
                pass
        if error_variable is not None:
            uel_signal: Var = vfactory.add_var(f'UelPu_{template_name}')
            template.block.in_vars.append(uel_signal)
            template.block.init_eqs[uel_signal] = Const(0.0)
            error_index: int = template.block.algebraic_vars.index(error_variable)
            template.block.algebraic_eqs[error_index] = (
                template.block.algebraic_eqs[error_index] - uel_signal
            )
        else:
            pass
    else:
        pass
    template.comment = 'CGMES ExcIEEEST2A multiplicative compound-source exciter'
    for parameter_name in (
            'enabled', 'ka', 'ta', 'vrmax', 'vrmin', 'ke', 'te', 'kf', 'tf',
            'kp', 'ki', 'kc', 'efdmax', 'uelin',
    ):
        variable_name: str = f'ExcIEEEST2A.{parameter_name}_{template_name}'
        parameter_variable: Var = vfactory.add_var(variable_name)
        template.block.event_dict[parameter_variable] = vfactory.add_const(
            value=None,
            name=variable_name,
        )
    return template
