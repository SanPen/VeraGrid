# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES IEEE ST3A excitation template."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.synchronous_machines.genrou_exc_gov_rms_template import (
    Esst3aRmsParameters,
    configure_esst3a_block,
    get_esst3a_rms_template,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class ExcIEEEST3AParameters:
    """Exact scalar fields from the canonical ExcIEEEST3A RDF class."""

    __slots__ = (
        'vimax', 'vimin', 'ka', 'ta', 'tb', 'tc', 'vrmax', 'vrmin', 'km',
        'tm', 'vmmax', 'vmmin', 'kg', 'kp', 'thetap', 'ki', 'kc', 'xl',
        'vbmax', 'vgmax',
    )

    def __init__(
            self,
            vimax: float = 0.2,
            vimin: float = -0.2,
            ka: float = 20.0,
            ta: float = 0.0,
            tb: float = 5.0,
            tc: float = 1.0,
            vrmax: float = 99.0,
            vrmin: float = -99.0,
            km: float = 8.0,
            tm: float = 0.4,
            vmmax: float = 99.0,
            vmmin: float = 0.0,
            kg: float = 1.0,
            kp: float = 3.67,
            thetap: float = 3.33,
            ki: float = 0.435,
            kc: float = 0.01,
            xl: float = 0.0098,
            vbmax: float = 5.48,
            vgmax: float = 3.86,
    ) -> None:
        """Store canonical parameters using ESST3A reference typical values.

        :param vimax: Input error upper limit.
        :param vimin: Input error lower limit.
        :param ka: Voltage regulator gain.
        :param ta: Regulator lead stage time.
        :param tb: Regulator lag time.
        :param tc: Regulator lead time.
        :param vrmax: Regulator output upper limit.
        :param vrmin: Regulator output lower limit.
        :param km: Exciter gain.
        :param tm: Exciter time constant.
        :param vmmax: Exciter input upper limit.
        :param vmmin: Exciter input lower limit.
        :param kg: Field voltage feedback gain.
        :param kp: Potential source gain.
        :param thetap: Potential source phase angle in degrees.
        :param ki: Current source gain.
        :param kc: Commutation coefficient.
        :param xl: Potential source reactance.
        :param vbmax: Rectifier output upper limit.
        :param vgmax: Feedback upper limit.
        """
        self.vimax: float = vimax
        self.vimin: float = vimin
        self.ka: float = ka
        self.ta: float = ta
        self.tb: float = tb
        self.tc: float = tc
        self.vrmax: float = vrmax
        self.vrmin: float = vrmin
        self.km: float = km
        self.tm: float = tm
        self.vmmax: float = vmmax
        self.vmmin: float = vmmin
        self.kg: float = kg
        self.kp: float = kp
        self.thetap: float = thetap
        self.ki: float = ki
        self.kc: float = kc
        self.xl: float = xl
        self.vbmax: float = vbmax
        self.vgmax: float = vgmax


def build_exc_i_e_e_e_s_t3_a_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: ExcIEEEST3AParameters | None = None,
) -> RmsModelTemplate:
    """Build the equation graph and map canonical CGMES fields to its events.

    :param vfactory: Factory allocating symbolic variables.
    :param name: Optional unique runtime name.
    :param parameters: Parsed RDF values or reference defaults.
    :return: Equation-backed ESST3A graph with its native terminal signal ports.
    :raises ValueError: Invalid parameter set.
    """
    settings: ExcIEEEST3AParameters = (
        ExcIEEEST3AParameters() if parameters is None else parameters
    )
    template_name: str = 'ExcIEEEST3A' if name is None else name
    values: tuple[float, ...] = (
        settings.vimax, settings.vimin, settings.ka, settings.ta, settings.tb,
        settings.tc, settings.vrmax, settings.vrmin, settings.km, settings.tm,
        settings.vmmax, settings.vmmin, settings.kg, settings.kp,
        settings.thetap, settings.ki, settings.kc, settings.xl, settings.vbmax,
        settings.vgmax,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('ExcIEEEST3A parameters must be finite')
    elif settings.ta < 0.0:
        raise ValueError('ExcIEEEST3A TA must be nonnegative')
    elif settings.tb <= 0.0 or settings.tm <= 0.0 or settings.ka <= 0.0:
        raise ValueError('ExcIEEEST3A TB, TM, and KA must be positive')
    elif settings.vimin >= settings.vimax or settings.vrmin >= settings.vrmax:
        raise ValueError('ExcIEEEST3A regulator limits are invalid')
    elif settings.vmmin >= settings.vmmax or min(
            settings.km, settings.kg, settings.kp, settings.ki, settings.kc,
            settings.xl, settings.vbmax, settings.vgmax,
    ) < 0.0:
        raise ValueError('ExcIEEEST3A gains, source, or field limits are invalid')
    else:
        pass

    template: RmsModelTemplate = get_esst3a_rms_template(
        vfactory=vfactory,
        name=template_name,
    )
    runtime_block: Block = template.block.children[0]
    configure_esst3a_block(
        block=runtime_block,
        parameters=Esst3aRmsParameters(
            tr=0.0,
            vimax=settings.vimax,
            vimin=settings.vimin,
            km=settings.km,
            tc=settings.tc,
            tb=settings.tb,
            ka=settings.ka,
            ta=settings.ta,
            vrmax=settings.vrmax,
            vrmin=settings.vrmin,
            kg=settings.kg,
            kp=settings.kp,
            ki=settings.ki,
            vbmax=settings.vbmax,
            kc=settings.kc,
            xl=settings.xl,
            vgmax=settings.vgmax,
            thetap=settings.thetap,
            tm=settings.tm,
            vmmax=settings.vmmax,
            vmmin=settings.vmmin,
        ),
        vfactory=vfactory,
    )
    lagged_voltage: Var | None = None
    terminal_voltage: Var | None = None
    for state_variable in runtime_block.state_vars:
        if state_variable.name == 'LG_y':
            lagged_voltage = state_variable
        else:
            pass
    for input_variable in runtime_block.in_vars:
        if input_variable.name == 'Vm_':
            terminal_voltage = input_variable
        else:
            pass
    if lagged_voltage is not None and terminal_voltage is not None:
        transducer_index: int = runtime_block.state_vars.index(lagged_voltage)
        runtime_block.update_model(lagged_voltage, terminal_voltage)
        runtime_block.state_vars.pop(transducer_index)
        runtime_block.state_eqs.pop(transducer_index)
        runtime_block.init_eqs.pop(terminal_voltage, None)
    else:
        raise RuntimeError('The native ESST3A transducer ports changed unexpectedly')
    # IEEE ST3A adds a distinct regulator state before VR limits only when TA is positive.
    if settings.ta > 0.0:
        law1_signal: Var | None = None
        vg_signal: Var | None = None
        vrs_signal: Var | None = None
        ta_parameter: Var | None = None
        vrmax_parameter: Var | None = None
        vrmin_parameter: Var | None = None
        candidate_variable: Var
        for candidate_variable in runtime_block.algebraic_vars:
            if candidate_variable.name == 'LAW1_y':
                law1_signal = candidate_variable
            else:
                pass
            if candidate_variable.name == 'VG_y':
                vg_signal = candidate_variable
            else:
                pass
            if candidate_variable.name == 'vrs':
                vrs_signal = candidate_variable
            else:
                pass
        else:
            pass
        for candidate_variable in runtime_block.event_dict:
            if candidate_variable.name == 'TA':
                ta_parameter = candidate_variable
            else:
                pass
            if candidate_variable.name == 'VRMAX':
                vrmax_parameter = candidate_variable
            else:
                pass
            if candidate_variable.name == 'VRMIN':
                vrmin_parameter = candidate_variable
            else:
                pass
        else:
            pass
        if (
                law1_signal is None or vg_signal is None or vrs_signal is None
                or ta_parameter is None or vrmax_parameter is None or vrmin_parameter is None
        ):
            raise RuntimeError('The native ESST3A regulator ports or parameters changed unexpectedly')
        else:
            regulator_state: Var = vfactory.add_var(f'VRState_{template_name}')
            regulator_output: Var = vfactory.add_var(f'VR_{template_name}')
            law1_initial: Expr | Const | None = runtime_block.init_eqs.get(law1_signal, None)
            if law1_initial is None:
                raise RuntimeError('The native ESST3A regulator demand has no equilibrium initialization')
            else:
                pass
            runtime_block.state_vars.append(regulator_state)
            runtime_block.diff_vars.append(
                vfactory.add_diff_var(
                    name=f'd_VRState_{template_name}',
                    base_var=regulator_state,
                )
            )
            runtime_block.state_eqs.append((law1_signal - regulator_state) / ta_parameter)
            runtime_block.init_eqs[regulator_state] = law1_initial
            runtime_block.algebraic_vars.append(regulator_output)
            runtime_block.algebraic_eqs.append(
                sym.hard_sat(regulator_state, vrmin_parameter, vrmax_parameter) - regulator_output
            )
            runtime_block.init_eqs[regulator_output] = sym.hard_sat(
                law1_initial,
                vrmin_parameter,
                vrmax_parameter,
            )
            # The inner-loop feedback uses limited VR, not the raw KA regulator demand.
            vrs_equation_replaced: bool = False
            for equation_index in range(len(runtime_block.algebraic_eqs)):
                equation: Expr = runtime_block.algebraic_eqs[equation_index]
                if (
                        equation.contains_var(law1_signal)
                        and equation.contains_var(vg_signal)
                        and equation.contains_var(vrs_signal)
                ):
                    runtime_block.algebraic_eqs[equation_index] = (
                        regulator_output - vg_signal - vrs_signal
                    )
                    vrs_equation_replaced = True
                else:
                    pass
            else:
                pass
            if not vrs_equation_replaced:
                raise RuntimeError('The native ESST3A regulator-to-feedback equation changed unexpectedly')
            else:
                pass
    else:
        pass
    template.comment = 'CGMES ExcIEEEST3A compound-source static excitation model'
    parameter_fields: tuple[str, ...] = (
        'vimax', 'vimin', 'ka', 'ta', 'tb', 'tc', 'vrmax', 'vrmin', 'km',
        'tm', 'vmmax', 'vmmin', 'kg', 'kp', 'thetap', 'ki', 'kc', 'xl',
        'vbmax', 'vgmax',
    )
    for parameter_name in parameter_fields:
        parameter_var: Var = vfactory.add_var(
            f'ExcIEEEST3A.{parameter_name}_{template_name}',
        )
        runtime_block.event_dict[parameter_var] = vfactory.add_const(value=None)
    return template
