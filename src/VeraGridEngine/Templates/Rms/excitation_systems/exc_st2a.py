# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES ExcST2A static excitation model."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class ExcST2AParameters:
    """Canonical ExcST2A values used to select the equation topology."""

    __slots__ = (
        'ka', 'ta', 'vrmax', 'vrmin', 'ke', 'te', 'kf', 'tf', 'kp', 'ki',
        'kc', 'efdmax', 'uelin', 'tb', 'tc',
    )

    def __init__(
            self,
            ka: float = 120.0,
            ta: float = 0.15,
            vrmax: float = 1.0,
            vrmin: float = -1.0,
            ke: float = 1.0,
            te: float = 0.5,
            kf: float = 0.05,
            tf: float = 0.7,
            kp: float = 4.88,
            ki: float = 8.0,
            kc: float = 1.82,
            efdmax: float = 99.0,
            uelin: bool = False,
            tb: float = 0.0,
            tc: float = 0.0,
    ) -> None:
        """Store all canonical ExcST2A RDF properties.

        :param ka: Voltage regulator gain.
        :param ta: Voltage regulator time constant in seconds.
        :param vrmax: Regulator upper output limit.
        :param vrmin: Regulator lower output limit.
        :param ke: Exciter field feedback coefficient.
        :param te: Exciter field time constant in seconds.
        :param kf: Field voltage washout gain.
        :param tf: Field voltage washout time constant in seconds.
        :param kp: Terminal voltage source coefficient.
        :param ki: Terminal current source coefficient.
        :param kc: Rectifier commutation loading coefficient.
        :param efdmax: Exciter field voltage upper limit.
        :param uelin: Select the high gate when true, additive UEL when false.
        :param tb: Voltage-error lead-lag lag time in seconds.
        :param tc: Voltage-error lead-lag lead time in seconds.
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
        self.tb: float = tb
        self.tc: float = tc


def build_exc_s_t2_a_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: ExcST2AParameters | None = None,
) -> RmsModelTemplate:
    """Build the CGMES ExcST2A lead-lag, static bridge, and field equations.

    The local CGMES EA diagram defines the input voltage lead-lag, selectable
    UEL addition/high gate, bounded regulator lag, multiplicative potential
    source, Kf/Tf field-voltage washout, and bounded field integrator. Terminal
    voltage/current phasors drive the potential-source and rectifier equations.

    :param vfactory: Factory allocating the symbolic model variables.
    :param name: Optional unique runtime model name.
    :param parameters: Canonical CGMES properties or the EA typical defaults.
    :return: Equation-backed CGMES ExcST2A block with machine signal ports.
    :raises ValueError: Invalid gains, limits, or time-constant combinations.
    """
    settings: ExcST2AParameters = ExcST2AParameters() if parameters is None else parameters
    template_name: str = 'ExcST2A' if name is None else name
    parameter_names: tuple[str, ...] = (
        'ka', 'ta', 'vrmax', 'vrmin', 'ke', 'te', 'kf', 'tf', 'kp', 'ki',
        'kc', 'efdmax', 'tb', 'tc',
    )
    parameter_values: tuple[float, ...] = (
        settings.ka, settings.ta, settings.vrmax, settings.vrmin, settings.ke,
        settings.te, settings.kf, settings.tf, settings.kp, settings.ki,
        settings.kc, settings.efdmax, settings.tb, settings.tc,
    )
    if not all(math.isfinite(value) for value in parameter_values):
        raise ValueError('ExcST2A numeric parameters must be finite')
    elif settings.uelin not in (True, False):
        raise ValueError('ExcST2A uelin must be boolean')
    elif min(settings.ta, settings.te, settings.tf, settings.tb, settings.tc) < 0.0:
        raise ValueError('ExcST2A time constants must be nonnegative')
    elif settings.tb == 0.0 and settings.tc != 0.0:
        raise ValueError('ExcST2A lead Tc requires positive lag Tb')
    elif settings.tf == 0.0 and settings.kf != 0.0:
        raise ValueError('ExcST2A nonzero Kf requires positive Tf')
    elif settings.ka <= 0.0 or settings.efdmax <= 0.0:
        raise ValueError('ExcST2A Ka and Efdmax must be positive')
    elif settings.vrmin >= settings.vrmax:
        raise ValueError('ExcST2A regulator lower limit must be below its upper limit')
    elif settings.ki == 0.0 and settings.kp == 0.0:
        raise ValueError('ExcST2A requires a nonzero potential or current source gain')
    elif settings.te == 0.0 and settings.ke == 0.0:
        raise ValueError('ExcST2A algebraic field equation requires nonzero Ke')
    else:
        pass

    # Keep RDF values as runtime events so imported edits alter the equations.
    builder: ControlRealization = ControlRealization(vfactory, template_name)
    parameter_by_name: dict[str, Var] = dict()
    for parameter_index in range(len(parameter_names)):
        parameter_name: str = parameter_names[parameter_index]
        parameter_variable: Var = vfactory.add_var(
            f'ExcST2A.{parameter_name}_{template_name}',
        )
        builder.block.event_dict[parameter_variable] = vfactory.add_const(
            value=parameter_values[parameter_index], name=parameter_variable.name,
        )
        parameter_by_name[parameter_name] = parameter_variable
    uelin: Var = vfactory.add_var(f'ExcST2A.uelin_{template_name}')
    builder.block.event_dict[uelin] = vfactory.add_const(
        value=float(settings.uelin), name=uelin.name,
    )
    ka: Var = parameter_by_name['ka']
    ta: Var = parameter_by_name['ta']
    vrmax: Var = parameter_by_name['vrmax']
    vrmin: Var = parameter_by_name['vrmin']
    ke: Var = parameter_by_name['ke']
    te: Var = parameter_by_name['te']
    kf: Var = parameter_by_name['kf']
    tf: Var = parameter_by_name['tf']
    kp: Var = parameter_by_name['kp']
    ki: Var = parameter_by_name['ki']
    kc: Var = parameter_by_name['kc']
    efdmax: Var = parameter_by_name['efdmax']
    tb: Var = parameter_by_name['tb']
    tc: Var = parameter_by_name['tc']

    # These ports match the detailed-machine and compound-source wiring contract.
    voltage_reference: Var = builder.input('VRefPu', Const(1.0))
    supplementary_voltage: Var = builder.input('VsPu', Const(0.0))
    uel_signal: Var = builder.input('VuelPu', Const(0.0))
    terminal_voltage: Var = builder.input('VmPu', Const(1.0))
    terminal_voltage_real: Var = builder.input('VrPu', Const(1.0))
    terminal_voltage_imag: Var = builder.input('ViPu', Const(0.0))
    terminal_current_real: Var = builder.input('IrPu', Const(0.5))
    terminal_current_imag: Var = builder.input('IiPu', Const(0.0))
    field_current: Var = builder.input('IfdPu', Const(1.0))
    # The potential-source phasor follows the EA diagram's Kp*Vt + j*Ki*It.
    bridge_real: Expr = kp * terminal_voltage_real - ki * terminal_current_imag
    bridge_imag: Expr = kp * terminal_voltage_imag + ki * terminal_current_real
    potential: Var = builder.algebraic(
        'PotentialPu', sym.sqrt(bridge_real ** 2 + bridge_imag ** 2), Const(1.0),
    )
    loading: Var = builder.algebraic(
        'RectifierLoadingPu', sym.safe_divide(kc * sym.abs(field_current), potential, 1.0),
        Const(0.0),
    )
    rectifier: Expr = sym.f_exc(loading)
    bridge: Var = builder.algebraic(
        'BridgePu', potential * rectifier, Const(1.0),
    )

    # Declare field feedback before forming the voltage error so the loop is explicit.
    field_voltage: Var = vfactory.add_var(f'EfdPu_{template_name}')
    feedback: Expr = Const(0.0)
    if settings.kf != 0.0:
        feedback = builder.washout(
            'FeedbackPu', field_voltage, tf, settings.tf, kf / tf, Const(1.0),
        )
    else:
        pass

    # UEL is added at the error sum or selected by the downstream high gate.
    voltage_error: Expr = (
        voltage_reference - terminal_voltage + supplementary_voltage
        + (Const(1.0) - uelin) * uel_signal - feedback
    )
    lead_lag: Var = builder.lead_lag(
        'VoltageLeadLagPu', voltage_error, tc, tb, settings.tc, settings.tb, Const(0.0),
    )
    gated_error: Expr = (
        uelin * sym.max(lead_lag, uel_signal)
        + (Const(1.0) - uelin) * lead_lag
    )

    # The regulator follows Ka/(1+sTa), with its bounded output as the state.
    regulator_demand: Expr = ka * gated_error
    regulator: Var = builder.lag(
        'RegulatorPu', regulator_demand, ta, settings.ta, Const(0.0), vrmin, vrmax,
    )

    # The field state is bounded and driven by the product of regulator and bridge.
    field_forcing: Expr = regulator * bridge
    if settings.te > 0.0:
        builder.differential(
            field_voltage, (field_forcing - ke * field_voltage) / te,
            Const(1.0), Const(0.0), efdmax,
        )
    else:
        builder.block.algebraic_vars.append(field_voltage)
        builder.block.algebraic_eqs.append(
            field_voltage - sym.hard_sat(sym.safe_divide(field_forcing, ke, 0.0), Const(0.0), efdmax),
        )
        builder.block.init_eqs[field_voltage] = Const(1.0)
    builder.block.out_vars.append(field_voltage)

    enabled_variable: Var = vfactory.add_var(f'ExcST2A.enabled_{template_name}')
    builder.block.event_dict[enabled_variable] = vfactory.add_const(
        value=None, name=enabled_variable.name,
    )
    template: RmsModelTemplate = builder.finish(
        (field_voltage,), 'CGMES ExcST2A voltage regulator, compound bridge, and field equations',
    )
    return template
