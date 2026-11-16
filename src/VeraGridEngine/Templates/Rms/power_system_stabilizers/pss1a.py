# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""IEEE PSS1A single-input stabilizer represented by the documented IEEEST map."""

from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.power_system_stabilizers.ieeest import (
    IeeestParameters,
    build_ieeest_template,
)


class Pss1aParameters:
    """Physical settings from the PSS1A to IEEEST correspondence table."""

    __slots__ = ('filter_coefficients', 'lead1', 'lag1', 'lead2', 'lag2',
                 'washout_time', 'gain', 'upper', 'lower')

    def __init__(self, filter_coefficients: tuple[float, float, float] = (0.1, 0.01, 0.1),
                 lead1: float = 0.2, lag1: float = 0.05, lead2: float = 0.2,
                 lag2: float = 0.05, washout_time: float = 5.0, gain: float = 1.0,
                 upper: float = 0.1, lower: float = -0.1) -> None:
        """Store PSS1A's three filter coefficients and stabilizer settings.

        :param filter_coefficients: A1, A2 and transducer time Tr.
        :param lead1: First phase numerator time T1, seconds.
        :param lag1: First phase denominator time T2, seconds.
        :param lead2: Second phase numerator time T3, seconds.
        :param lag2: Second phase denominator time T4, seconds.
        :param washout_time: Washout time TW, used for both IEEEST reset times.
        :param gain: Stabilizer gain KS.
        :param upper: Supplementary output maximum VSTMAX.
        :param lower: Supplementary output minimum VSTMIN.
        """
        self.filter_coefficients: tuple[float, float, float] = filter_coefficients
        self.lead1: float = lead1
        self.lag1: float = lag1
        self.lead2: float = lead2
        self.lag2: float = lag2
        self.washout_time: float = washout_time
        self.gain: float = gain
        self.upper: float = upper
        self.lower: float = lower


def build_pss1a_template(vf: VarFactory, name: str | None = None,
                         parameters: Pss1aParameters | None = None) -> RmsModelTemplate:
    """Build PSS1A using Siemens' explicit IEEEST parameter correspondence.

    :param vf: Shared symbolic variable factory.
    :param name: Optional runtime model name.
    :param parameters: PSS1A coefficients; defaults are representative only.
    :return: IEEEST realization restricted to the documented PSS1A structure.
    """
    settings: Pss1aParameters = Pss1aParameters() if parameters is None else parameters
    template_name: str = 'PSS1A' if name is None else name
    values: tuple[float, ...] = settings.filter_coefficients + (
        settings.lead1, settings.lag1, settings.lead2, settings.lag2,
        settings.washout_time, settings.gain, settings.upper, settings.lower,
    )
    if len(settings.filter_coefficients) != 3:
        raise ValueError('PSS1A requires exactly A1, A2 and Tr filter coefficients')
    elif not all(math.isfinite(value) for value in values):
        raise ValueError('PSS1A coefficients must be finite')
    else:
        pass
    ieeest: IeeestParameters = IeeestParameters(
        filter_coefficients=(settings.filter_coefficients[0], settings.filter_coefficients[1],
                             settings.filter_coefficients[2], 0.0, 0.0, 0.0),
        lead1=settings.lead1,
        lag1=settings.lag1,
        lead2=settings.lead2,
        lag2=settings.lag2,
        reset_numerator=settings.washout_time,
        reset_denominator=settings.washout_time,
        gain=settings.gain,
        upper=settings.upper,
        lower=settings.lower,
        voltage_upper=0.0,
        voltage_lower=0.0,
    )
    return build_ieeest_template(vf, template_name, ieeest)
