# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""AC9C first-order field-feedback filter."""
from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Var


class Ac9cFieldFeedbackSettings:
    """Store AC9C field-feedback gain, lag and initial operating point."""

    __slots__ = ('kf', 'tf', 'signal0', 'feedback0')

    def __init__(self, kf: float = 0.0, tf: float = 0.0,
                 signal0: float = 0.0, feedback0: float = 0.0) -> None:
        """Store gain, time and equilibrium values.

        :param kf: Feedback transfer gain.
        :param tf: Feedback lag time in seconds.
        :param signal0: Initial source feedback signal.
        :param feedback0: Initial filtered feedback output.
        """
        self.kf: float = kf
        self.tf: float = tf
        self.signal0: float = signal0
        self.feedback0: float = feedback0


def build_ac9c_field_feedback_template(
        vf: VarFactory,
        name: str = 'AC9C field feedback',
        settings: Ac9cFieldFeedbackSettings | None = None,
) -> RmsModelTemplate:
    """Build the source ``KF/(1+s*TF)`` feedback element.

    The source signal is exposed as an input because its connection belongs to
    the unfinished AC9C exciter and current-feedback routing. A positive TF
    creates one filter state; zero TF reduces to the static KF gain.

    :param vf: Symbol factory owning filter symbols.
    :param name: Unique component label.
    :param settings: Gain, time and solved initial signal/output.
    :return: Native component exposing ``FilteredFeedbackPu``.
    :raises ValueError: Nonfinite gain/time/initialization or negative TF.
    """
    selected: Ac9cFieldFeedbackSettings = (
        Ac9cFieldFeedbackSettings() if settings is None else settings
    )
    values: tuple[float, ...] = (
        selected.kf, selected.tf, selected.signal0, selected.feedback0,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('AC9C field-feedback settings must be finite')
    elif selected.tf < 0.0:
        raise ValueError('AC9C field-feedback TF must be nonnegative')
    elif selected.tf == 0.0 and selected.feedback0 != selected.kf * selected.signal0:
        raise ValueError('AC9C zero-TF feedback initial value must match static gain')
    else:
        pass

    control: ControlRealization = ControlRealization(vf, name)
    gain: Var = control.parameter('KF', selected.kf)
    time: Var = control.parameter('TF', selected.tf)
    signal: Var = control.input('FieldFeedbackSignalPu', Const(selected.signal0))
    feedback: Var = control.lag(
        'FilteredFeedbackPu', gain * signal, time, selected.tf, Const(selected.feedback0),
    )
    return control.finish((feedback,), 'AC9C first-order field-feedback filter')
