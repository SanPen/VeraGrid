# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Voltage-dependent current capability and priority for renewable electrical control."""
from __future__ import annotations

import math
from enum import Enum

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.procedural_logic import PickupDropoffLogic, SampledValueLogic
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class Reeca1CurrentPriority(Enum):
    """Select which commanded current reserves converter capacity first."""

    REACTIVE = 0
    ACTIVE = 1


class Reeca1CurrentLimitSettings:
    """Store converter capability and both voltage-dependent limit curves."""

    __slots__ = ('imax', 'reactive_curve', 'active_curve', 'priority', 'trv', 'thld2',
                 'bidirectional_active_current')

    def __init__(self, imax: float = 1.2,
                 reactive_curve: tuple[tuple[float, float], ...] = ((.2, 0.), (1.2, 1.2)),
                 active_curve: tuple[tuple[float, float], ...] = ((.2, 0.), (1.2, 1.2)),
                 priority: Reeca1CurrentPriority = Reeca1CurrentPriority.REACTIVE,
                 trv: float = 0., thld2: float = 0.,
                 bidirectional_active_current: bool = False) -> None:
        """Store the current limit settings in per-unit voltage and current.

        :param imax: Maximum total converter current.
        :param reactive_curve: Two to four voltage/current points for VDL1.
        :param active_curve: Two to four voltage/current points for VDL2.
        :param priority: Current channel that reserves capacity first.
        :param trv: REECA1 terminal-voltage measurement time, seconds.
        :param thld2: Active-current-ceiling hold after fault clearance, seconds.
        :param bidirectional_active_current: Permit negative active current for storage.
        :return: None.
        """
        self.imax: float = imax
        self.reactive_curve: tuple[tuple[float, float], ...] = reactive_curve
        self.active_curve: tuple[tuple[float, float], ...] = active_curve
        self.priority: Reeca1CurrentPriority = priority
        self.trv: float = trv
        self.thld2: float = thld2
        self.bidirectional_active_current: bool = bidirectional_active_current


def _validate_curve(points: tuple[tuple[float, float], ...]) -> bool:
    """Check the ordered, nonnegative two-to-four-point VDL source contract.

    :param points: Voltage/current pairs after the source's zero terminator.
    :return: Whether the supplied curve can be interpolated without ambiguity.
    """
    if len(points) < 2 or len(points) > 4:
        return False
    else:
        pass
    previous_voltage: float = -math.inf
    voltage: float
    current: float
    for voltage, current in points:
        if (not math.isfinite(voltage) or not math.isfinite(current)
                or voltage <= 0 or voltage <= previous_voltage
                or current < 0):
            return False
        else:
            previous_voltage = voltage
    return True


def reeca1_curve_from_source_pairs(
        source_pairs: tuple[tuple[float, float], ...],
) -> tuple[tuple[float, float], ...]:
    """Remove optional zero-terminated VDL pairs from a four-pair source record.

    The first two voltage entries are mandatory. Later zero-voltage entries
    terminate the curve and must be paired with zero current; all following
    pairs must also be zero. A zero *current* at a positive voltage remains a
    valid physical endpoint.

    :param source_pairs: Four ordered voltage/current pairs from the DYR row.
    :return: The two to four active curve points.
    :raises ValueError: Missing, nonzero-after-terminator or unordered points.
    """
    if len(source_pairs) != 4:
        raise ValueError('REECA1 source VDL requires four supplied pairs')
    else:
        pass
    points: list[tuple[float, float]] = list()
    terminated: bool = False
    index: int
    pair: tuple[float, float]
    for index, pair in enumerate(source_pairs):
        voltage: float = pair[0]
        current: float = pair[1]
        if voltage == 0:
            if index < 2 or current != 0:
                raise ValueError('REECA1 mandatory VDL point or terminator is invalid')
            else:
                terminated = True
        elif terminated:
            raise ValueError('REECA1 VDL has data after its zero terminator')
        else:
            points.append(pair)
    selected: tuple[tuple[float, float], ...] = tuple(points)
    if not _validate_curve(selected):
        raise ValueError('REECA1 source VDL curve is invalid')
    else:
        return selected


def _voltage_dependent_limit(
        control: ControlRealization, voltage: Expr,
        points: tuple[tuple[float, float], ...], name: str,
) -> Expr:
    """Interpolate a VDL curve, holding its endpoint currents outside the range.

    :param control: Controller variable owner.
    :param voltage: Live terminal voltage magnitude.
    :param points: Validated voltage/current pairs.
    :param name: Distinct VDL parameter-name prefix.
    :return: Piecewise linear current ceiling.
    """
    previous_v: Var = control.parameter(name + 'V1', points[0][0])
    previous_i: Var = control.parameter(name + 'I1', points[0][1])
    result: Expr = previous_i
    index: int
    for index in range(1, len(points)):
        next_v: Var = control.parameter(name + 'V' + str(index + 1), points[index][0])
        next_i: Var = control.parameter(name + 'I' + str(index + 1), points[index][1])
        # Each saturated voltage span contributes only inside its own segment.
        span: Expr = sym.hard_sat(voltage - previous_v, Const(0.), next_v - previous_v)
        result = result + (next_i - previous_i) * span / (next_v - previous_v)
        previous_v = next_v
        previous_i = next_i
    return result


def build_reeca1_current_limit_template(
        vf: VarFactory,
        name: str = 'REECA1 current limits',
        settings: Reeca1CurrentLimitSettings | None = None,
) -> RmsModelTemplate:
    """Build the current-capability part of the renewable electrical controller.

    Positive active current and signed reactive current use the converter MVA
    base. The source priority choice reserves its channel first, then limits
    the other with the remaining current circle. Each channel also obeys its
    own voltage-dependent VDL curve. This is a component, not the complete
    REECA1 controller or a PSS/E DYR binding.

    :param vf: Shared symbolic variable factory.
    :param name: Unique controller instance name.
    :param settings: Current capability and VDL curve settings.
    :return: Algebraic controller with voltage and current-command inputs.
    :raises ValueError: Invalid source curve, current capability, priority or measurement time.
    """
    selected: Reeca1CurrentLimitSettings = Reeca1CurrentLimitSettings() if settings is None else settings
    if not math.isfinite(selected.imax) or selected.imax <= 0:
        raise ValueError('Converter maximum current must be positive and finite')
    elif not isinstance(selected.priority, Reeca1CurrentPriority):
        raise ValueError('REECA1 current priority is invalid')
    elif not isinstance(selected.bidirectional_active_current, bool):
        raise ValueError('REECA1 bidirectional-current selector is invalid')
    elif not math.isfinite(selected.trv) or selected.trv < 0:
        raise ValueError('REECA1 voltage measurement time is invalid')
    elif not math.isfinite(selected.thld2) or selected.thld2 < 0:
        raise ValueError('REECA1 active-current hold time is invalid')
    elif not _validate_curve(selected.reactive_curve) or not _validate_curve(selected.active_curve):
        raise ValueError('REECA1 voltage-dependent limit curve is invalid')
    else:
        pass

    control: ControlRealization = ControlRealization(vf, name)
    imax: Var = control.parameter('IMAX', selected.imax)
    voltage: Var = control.input('TerminalVoltagePu', Const(1.))
    ip_command: Var = control.input('ActiveCommandPu', Const(0.))
    iq_command: Var = control.input('ReactiveCommandPu', Const(0.))
    fault_flag: Var | None = None
    if selected.thld2 > 0:
        fault_flag = control.input('VoltageDipFlag', Const(0.))
    else:
        pass
    # REECA1 uses the measured voltage for both VDL tables. A zero TRV is
    # an exact bypass; a positive TRV owns the source's voltage-filter state.
    measured_voltage: Expr = voltage
    if selected.trv > 0:
        trv: Var = control.parameter('TRV', selected.trv)
        measured_voltage = control.lag('MeasuredVoltagePu', voltage, trv,
                                       selected.trv, voltage)
    else:
        pass
    vdl1: Expr = _voltage_dependent_limit(control, measured_voltage, selected.reactive_curve, 'VDL1')
    vdl2: Expr = _voltage_dependent_limit(control, measured_voltage, selected.active_curve, 'VDL2')
    iq_cap: Expr
    ip_cap: Expr
    if selected.priority is Reeca1CurrentPriority.REACTIVE:
        iq_cap = sym.min(vdl1, imax)
        # Appendix B calculates the other channel's capability from the
        # commanded current, even when its own VDL bound clips that command.
        ip_cap = sym.min(vdl2, sym.sqrt(sym.max(imax * imax - iq_command * iq_command, Const(0.))))
    else:
        ip_cap = sym.min(vdl2, imax)
        iq_cap = sym.min(vdl1, sym.sqrt(sym.max(imax * imax - ip_command * ip_command, Const(0.))))
    ip_effective_cap: Expr = ip_cap
    if selected.thld2 > 0 and fault_flag is not None:
        # Keep the last faulted ceiling; after clearance the relay expires
        # exactly at Thld2 while the VDL and current circle keep updating.
        held_cap: Var = vf.add_var('HeldFaultIpmaxPu_' + name)
        hold_mode: Var = vf.add_var('ActiveLimitRecoveryHold_' + name)
        control.block.mode_dict[held_cap] = Const(selected.imax)
        control.block.mode_dict[hold_mode] = Const(0.)
        thld2: Var = control.parameter('THLD2', selected.thld2)
        control.block.procedural_logic.append(SampledValueLogic(
            output_var_name=held_cap.name,
            source_expr=fault_flag * ip_cap + (Const(1.) - fault_flag) * held_cap,
            name='REECA1 faulted active-current ceiling ' + name,
        ))
        control.block.procedural_logic.append(PickupDropoffLogic(
            output_var_name=hold_mode.name, bool_expr=fault_flag,
            pickup_delay_expr=Const(0.), drop_delay_expr=thld2,
            name='REECA1 active-current recovery hold ' + name,
        ))
        ip_effective_cap = ip_cap + (hold_mode - fault_flag) * (held_cap - ip_cap)
    else:
        pass
    active_current_minimum: Expr = (
        -ip_effective_cap if selected.bidirectional_active_current else Const(0.)
    )
    ip_limited: Var = control.algebraic(
        'LimitedActiveCommandPu',
        sym.hard_sat(ip_command, active_current_minimum, ip_effective_cap), Const(0.),
    )
    iq_limited: Var = control.algebraic(
        'LimitedReactiveCommandPu', sym.hard_sat(iq_command, -iq_cap, iq_cap), Const(0.),
    )
    iq_capability: Var = control.algebraic('ReactiveCapabilityPu', iq_cap, Const(selected.imax))
    return control.finish((ip_limited, iq_limited, iq_capability),
                          'Voltage-dependent renewable current limits with explicit P/Q priority')
