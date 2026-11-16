# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES IEEE ST5B excitation template."""

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.excitation_systems.st5b import (
    ExcitationLimiterLocation,
    ParallelChannelExciterParameters,
    build_st5b_template,
)
from VeraGridEngine.Utils.Symbolic.symbolic import Var


class ExcIEEEST5BParameters:
    """Exact numeric fields of canonical ExcIEEEST5B."""

    __slots__ = (
        'kr', 't1', 'kc', 'vrmax', 'vrmin', 'tc1', 'tb1', 'tc2', 'tb2',
        'toc1', 'tob1', 'toc2', 'tob2', 'tuc1', 'tub1', 'tuc2', 'tub2',
    )

    def __init__(
            self,
            kr: float = 20.0,
            t1: float = 0.05,
            kc: float = 0.1,
            vrmax: float = 5.0,
            vrmin: float = -5.0,
            tc1: float = 0.1,
            tb1: float = 0.2,
            tc2: float = 0.05,
            tb2: float = 0.1,
            toc1: float = 0.05,
            tob1: float = 0.15,
            toc2: float = 0.04,
            tob2: float = 0.08,
            tuc1: float = 0.2,
            tub1: float = 0.3,
            tuc2: float = 0.1,
            tub2: float = 0.2,
    ) -> None:
        """Store RDF fields using the documented ST5B physical defaults.

        :param kr: Regulator gain.
        :param t1: Field output time constant.
        :param kc: Field-current loading coefficient.
        :param vrmax: Regulator upper limit.
        :param vrmin: Regulator lower limit.
        :param tc1: Normal channel lead time.
        :param tb1: Normal channel lag time.
        :param tc2: Normal channel second lead time.
        :param tb2: Normal channel second lag time.
        :param toc1: Maximum channel first lead time.
        :param tob1: Maximum channel first lag time.
        :param toc2: Maximum channel second lead time.
        :param tob2: Maximum channel second lag time.
        :param tuc1: Minimum channel first lead time.
        :param tub1: Minimum channel first lag time.
        :param tuc2: Minimum channel second lead time.
        :param tub2: Minimum channel second lag time.
        """
        self.kr: float = kr
        self.t1: float = t1
        self.kc: float = kc
        self.vrmax: float = vrmax
        self.vrmin: float = vrmin
        self.tc1: float = tc1
        self.tb1: float = tb1
        self.tc2: float = tc2
        self.tb2: float = tb2
        self.toc1: float = toc1
        self.tob1: float = tob1
        self.toc2: float = toc2
        self.tob2: float = tob2
        self.tuc1: float = tuc1
        self.tub1: float = tub1
        self.tuc2: float = tuc2
        self.tub2: float = tub2


def build_exc_i_e_e_e_s_t5_b_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: ExcIEEEST5BParameters | None = None,
) -> RmsModelTemplate:
    """Build the three-channel bounded ST5B equation graph.

    :param vfactory: Factory allocating symbolic variables.
    :param name: Optional unique runtime name.
    :param parameters: Parsed CGMES fields or physical defaults.
    :return: Equation-backed ST5B model with terminal and limiter ports.
    """
    settings: ExcIEEEST5BParameters = (
        ExcIEEEST5BParameters() if parameters is None else parameters
    )
    template_name: str = 'ExcIEEEST5B' if name is None else name
    template: RmsModelTemplate = build_st5b_template(
        vf=vfactory,
        name=template_name,
        parameters=ParallelChannelExciterParameters(
            tr=0.0,
            tc1=settings.tc1,
            tb1=settings.tb1,
            tc2=settings.tc2,
            tb2=settings.tb2,
            kr=settings.kr,
            vrmax=settings.vrmax,
            vrmin=settings.vrmin,
            t1=settings.t1,
            kc=settings.kc,
            tuc1=settings.tuc1,
            tub1=settings.tub1,
            tuc2=settings.tuc2,
            tub2=settings.tub2,
            toc1=settings.toc1,
            tob1=settings.tob1,
            toc2=settings.toc2,
            tob2=settings.tob2,
            minimum_location=ExcitationLimiterLocation.REFERENCE_GATE,
            maximum_location=ExcitationLimiterLocation.REFERENCE_GATE,
        ),
    )
    template.comment = 'CGMES ExcIEEEST5B three-channel static excitation model'
    parameter_fields: tuple[str, ...] = (
        'kr', 't1', 'kc', 'vrmax', 'vrmin', 'tc1', 'tb1', 'tc2', 'tb2',
        'toc1', 'tob1', 'toc2', 'tob2', 'tuc1', 'tub1', 'tuc2', 'tub2',
    )
    for parameter_name in parameter_fields:
        parameter_var: Var = vfactory.add_var(
            f'ExcIEEEST5B.{parameter_name}_{template_name}',
        )
        template.block.event_dict[parameter_var] = vfactory.add_const(value=None)
    return template
