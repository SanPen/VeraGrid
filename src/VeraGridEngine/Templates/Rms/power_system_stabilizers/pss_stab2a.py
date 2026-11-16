# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""CGMES adapter for the matching RMS international STAB2A realization."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.power_system_stabilizers.stab2a import (
    build_stab2a_template,
)


class PssSTAB2AParameters:
    """Canonical eight-field STAB2A filter settings."""

    __slots__ = ('k2', 'k3', 'k4', 'k5', 't2', 't3', 't5', 'hlim')

    def __init__(
            self,
            k2: float = 1.0,
            k3: float = 1.0,
            k4: float = 1.0,
            k5: float = 1.0,
            t2: float = 1.0,
            t3: float = 0.1,
            t5: float = 0.1,
            hlim: float = 0.1,
    ) -> None:
        """Store the canonical CGMES filter values.

        :param k2: Gain of each electrical-power washout stage.
        :param k3: Gain of the parallel-path lag.
        :param k4: Gain of the direct output path.
        :param k5: Gain of each final low-pass stage.
        :param t2: Common washout time constant in seconds.
        :param t3: Parallel-path lag time constant in seconds.
        :param t5: Common output-filter time constant in seconds.
        :param hlim: Symmetric stabilizer-output limit.
        """
        self.k2: float = k2
        self.k3: float = k3
        self.k4: float = k4
        self.k5: float = k5
        self.t2: float = t2
        self.t3: float = t3
        self.t5: float = t5
        self.hlim: float = hlim


def build_pss_s_t_a_b2_a_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: PssSTAB2AParameters | None = None,
) -> RmsModelTemplate:
    """Build CGMES STAB2A by adapting the exact matching RMS equation graph.

    :param vfactory: Factory allocating all state, parameter and output symbols.
    :param name: Optional unique runtime model label.
    :param parameters: Canonical CGMES parameter values.
    :return: Six-state stabilizer graph with one electrical-power input.
    :raises ValueError: Nonfinite coefficients or nonpositive times/output limit.
    """
    settings: PssSTAB2AParameters = (
        PssSTAB2AParameters() if parameters is None else parameters
    )
    numeric_values: tuple[float, ...] = (
        settings.k2, settings.k3, settings.k4, settings.k5,
        settings.t2, settings.t3, settings.t5, settings.hlim,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('PssSTAB2A parameters must be finite')
    elif min(settings.t2, settings.t3, settings.t5, settings.hlim) <= 0.0:
        raise ValueError('PssSTAB2A requires positive filter times and output limit')
    else:
        pass

    template_name: str = 'PssSTAB2A' if name is None else name
    template: RmsModelTemplate = build_stab2a_template(
        vf=vfactory,
        name=template_name,
        k2=settings.k2,
        t2=settings.t2,
        k3=settings.k3,
        t3=settings.t3,
        k4=settings.k4,
        k5=settings.k5,
        t5=settings.t5,
        output_limit=settings.hlim,
    )
    template.comment = (
        'CGMES PssSTAB2A adapted from the exact same-topology RMS international '
        'STAB2A equation graph; canonical RDF parameters are retained below.'
    )

    # Importer parameter copying requires the canonical RDF property prefix.
    parameter_names: tuple[str, ...] = (
        'k2', 'k3', 'k4', 'k5', 't2', 't3', 't5', 'hlim',
    )
    for parameter_name in parameter_names:
        variable_name: str = f'PssSTAB2A.{parameter_name}_{template_name}'
        parameter_variable = vfactory.add_var(variable_name)
        template.block.event_dict[parameter_variable] = vfactory.add_const(
            value=None,
            name=variable_name,
        )
    return template
