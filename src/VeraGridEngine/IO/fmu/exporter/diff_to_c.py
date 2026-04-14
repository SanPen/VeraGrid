# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from .config import IntegrationMethod


def render_discrete_derivative(
    *,
    method: IntegrationMethod,
    state_expr: str,
    history_expr: str,
    d_history_expr: str,
    history2_expr: str,
    step_expr: str,
) -> str:
    if method == IntegrationMethod.BACKWARD_EULER:
        return f"(({state_expr}) - ({history_expr})) / ({step_expr})"
    if method == IntegrationMethod.TRAPEZOIDAL:
        return f"((2.0 / ({step_expr})) * (({state_expr}) - ({history_expr})) - ({d_history_expr}))"
    if method == IntegrationMethod.BDF2:
        return f"((1.5 * ({state_expr}) - 2.0 * ({history_expr}) + 0.5 * ({history2_expr})) / ({step_expr}))"
    raise ValueError(f"Unsupported integration method: {method}")
