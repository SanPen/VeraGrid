# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES IEEE ST7B output-feedback excitation template."""

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.IO.cim.cgmes.dynamics.schema import (
    ExcST7BOELselectorKind,
    ExcST7BUELselectorKind,
)
from VeraGridEngine.Templates.Rms.excitation_systems.st7b import (
    build_st7b_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.self_feedback_exciter import (
    ExcitationLimiterLocation,
    SelfFeedbackExciterParameters,
)
from VeraGridEngine.Utils.Symbolic.symbolic import Var


class ExcIEEEST7BParameters:
    """Exact numeric and selector fields from canonical ExcIEEEST7B."""

    __slots__ = (
        'kh', 'kia', 'kl', 'kpa', 'oelin', 'tb', 'tc', 'tf', 'tg', 'tia',
        'uelin', 'vmax', 'vmin', 'vrmax', 'vrmin',
    )

    def __init__(
            self,
            kh: float = 1.0,
            kia: float = 1.0,
            kl: float = 1.0,
            kpa: float = 20.0,
            oelin: ExcST7BOELselectorKind = ExcST7BOELselectorKind.noOELinput,
            tb: float = 0.2,
            tc: float = 0.1,
            tf: float = 0.2,
            tg: float = 0.1,
            tia: float = 0.5,
            uelin: ExcST7BUELselectorKind = ExcST7BUELselectorKind.noUELinput,
            vmax: float = 1.2,
            vmin: float = 0.8,
            vrmax: float = 5.0,
            vrmin: float = -5.0,
    ) -> None:
        """Store canonical values using the documented ST7B reference values.

        :param kh: Lower regulator capability feedback gain.
        :param kia: Delivered-field feedback gain.
        :param kl: Upper regulator capability feedback gain.
        :param kpa: Proportional regulator gain.
        :param oelin: OEL insertion selector.
        :param tb: Regulator phase lag time in seconds.
        :param tc: Regulator phase lead time in seconds.
        :param tf: Measurement shaping lag time in seconds.
        :param tg: Measurement shaping lead time in seconds.
        :param tia: Field-feedback lag time in seconds.
        :param uelin: UEL insertion selector.
        :param vmax: Reference upper limit.
        :param vmin: Reference lower limit.
        :param vrmax: Terminal-scaled field upper limit.
        :param vrmin: Terminal-scaled field lower limit.
        """
        self.kh: float = kh
        self.kia: float = kia
        self.kl: float = kl
        self.kpa: float = kpa
        self.oelin: ExcST7BOELselectorKind = oelin
        self.tb: float = tb
        self.tc: float = tc
        self.tf: float = tf
        self.tg: float = tg
        self.tia: float = tia
        self.uelin: ExcST7BUELselectorKind = uelin
        self.vmax: float = vmax
        self.vmin: float = vmin
        self.vrmax: float = vrmax
        self.vrmin: float = vrmin


def _selector_location(
        selector: ExcST7BOELselectorKind | ExcST7BUELselectorKind,
        oel_selector: bool,
) -> ExcitationLimiterLocation:
    """Map a CGMES ST7B selector to its diagram gate location.

    :param selector: Canonical OEL or UEL selector value.
    :param oel_selector: True for OEL enum values.
    :return: Native physical gate location; absent input uses a bypass gate.
    """
    if oel_selector is True and selector == ExcST7BOELselectorKind.addVref:
        return ExcitationLimiterLocation.REFERENCE_SUM
    elif oel_selector is True and selector == ExcST7BOELselectorKind.inputLVgate:
        return ExcitationLimiterLocation.REFERENCE_GATE
    elif oel_selector is True and selector == ExcST7BOELselectorKind.outputLVgate:
        return ExcitationLimiterLocation.OUTPUT_GATE
    elif oel_selector is False and selector == ExcST7BUELselectorKind.addVref:
        return ExcitationLimiterLocation.REFERENCE_SUM
    elif oel_selector is False and selector == ExcST7BUELselectorKind.inputHVgate:
        return ExcitationLimiterLocation.REFERENCE_GATE
    elif oel_selector is False and selector == ExcST7BUELselectorKind.outputHVgate:
        return ExcitationLimiterLocation.OUTPUT_GATE
    else:
        return ExcitationLimiterLocation.REFERENCE_GATE


def build_exc_i_e_e_e_s_t7_b_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: ExcIEEEST7BParameters | None = None,
) -> RmsModelTemplate:
    """Build ST7B equations with exact canonical RDF events.

    :param vfactory: Factory allocating symbolic variables.
    :param name: Optional unique runtime name.
    :param parameters: Parsed CGMES fields or reference defaults.
    :return: Equation-backed ST7B graph with limiter selection encoded.
    """
    settings: ExcIEEEST7BParameters = (
        ExcIEEEST7BParameters() if parameters is None else parameters
    )
    template_name: str = 'ExcIEEEST7B' if name is None else name
    template: RmsModelTemplate = build_st7b_template(
        vf=vfactory,
        name=template_name,
        parameters=SelfFeedbackExciterParameters(
            tr=0.0,
            tg=settings.tg,
            tf=settings.tf,
            vmax=settings.vmax,
            vmin=settings.vmin,
            kpa=settings.kpa,
            vrmax=settings.vrmax,
            vrmin=settings.vrmin,
            kh=settings.kh,
            kl=settings.kl,
            tc=settings.tc,
            tb=settings.tb,
            kia=settings.kia,
            tia=settings.tia,
            minimum_location=_selector_location(settings.uelin, False),
            maximum_location=_selector_location(settings.oelin, True),
        ),
    )
    template.comment = 'CGMES ExcIEEEST7B output-feedback static excitation model'
    parameter_fields: tuple[str, ...] = (
        'kh', 'kia', 'kl', 'kpa', 'oelin', 'tb', 'tc', 'tf', 'tg', 'tia',
        'uelin', 'vmax', 'vmin', 'vrmax', 'vrmin',
    )
    for parameter_name in parameter_fields:
        parameter_var: Var = vfactory.add_var(
            f'ExcIEEEST7B.{parameter_name}_{template_name}',
        )
        template.block.event_dict[parameter_var] = vfactory.add_const(value=None)
    return template
