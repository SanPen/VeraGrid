# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import numpy as np
from VeraGridEngine.enumerations import DeviceType, TapPhaseControl, TapModuleControl, WindingType
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Devices.Branches.transformer import Transformer2W
from VeraGridEngine.Utils.Symbolic.block import Block, VarPowerFlowRefferenceType
from VeraGridEngine.Utils.Symbolic.symbolic import sin, cos
from VeraGridEngine.Templates.templates_common_functions import tf_to_diffblock_with_output, tf_to_block, discrete_control_block
from VeraGridEngine.enumerations import WindingsConnection


def parse_windings_connection(conn: WindingsConnection) -> tuple[WindingType, WindingType]:
    """
    Parse a WindingsConnection enum into (conn_f, conn_t) WindingType values.
    
    WindingsConnection values are two-character strings:
    - G: GroundedStar
    - S: NeutralStar (ungrounded star)  
    - D: Delta
    
    Examples:
    - GG -> (GroundedStar, GroundedStar)
    - GD -> (GroundedStar, Delta)
    - DD -> (Delta, Delta)
    """
    conn_str = str(conn)
    if len(conn_str) != 2:
        raise ValueError(f"Invalid WindingsConnection: {conn}")
    
    char_to_winding = {
        'G': WindingType.GroundedStar,
        'S': WindingType.NeutralStar,
        'D': WindingType.Delta,
    }
    
    conn_f = char_to_winding.get(conn_str[0])
    conn_t = char_to_winding.get(conn_str[1])
    
    if conn_f is None or conn_t is None:
        raise ValueError(f"Invalid WindingsConnection characters: {conn_str}")
    
    return conn_f, conn_t


class TrafoRmsTemplate(RmsModelTemplate):
    __slots__ = (
        "tpe",
        "_block",
    )

    def __init__(self, trafo:Transformer2W, vf: VarFactory, Sbase:float = 100, name: str = "rms_bus_template"):
        """
        Created the RMS Template of a Bus
        :param vf: VarFactory
        :param name: Name of the RMS Model
        """
        super().__init__(name=name)

        vf = vf
        self.tpe: DeviceType = DeviceType.TransformerTypeDevice
        if trafo.rms_model.empty():
            Qf = vf.add_var("Qf")
            Qt = vf.add_var("Qt")
            Pf = vf.add_var("Pf")
            Pt = vf.add_var("Pt")
            m = vf.add_var('m')
            phi = vf.add_var('phi')

            ys = 1.0 / complex(trafo.R, trafo.X)
            ysh = trafo.G + 1j * trafo.B
            gt = vf.add_var("g")
            bt = vf.add_var("b")
            gFe = vf.add_var('gFe')
            bmu = vf.add_var('bmu')
            vtap_f, vtap_t = trafo.get_virtual_taps()
            print(f"DEBUG Trafo: R={trafo.R}, X={trafo.X}, G={trafo.G}, B={trafo.B}")
            print(f"DEBUG Trafo: tap_mod={trafo.tap_module}, tap_phase={trafo.tap_phase}, vtap_f={vtap_f}, vtap_t={vtap_t}")

            print(f"vtap  p is {vtap_f}")
            print(f"vtap  t is {vtap_t}")
            print(f'ys is {ys} ysh is {ysh}')

            Vmf = trafo.bus_from.rms_model.E(VarPowerFlowRefferenceType.Vm)
            Vaf = trafo.bus_from.rms_model.E(VarPowerFlowRefferenceType.Va)
            Vmt = trafo.bus_to.rms_model.E(VarPowerFlowRefferenceType.Vm)
            Vat = trafo.bus_to.rms_model.E(VarPowerFlowRefferenceType.Va)

            # Calculate phase displacement matching transformer_admittance logic
            # Use conn attribute (preserves user intent) instead of conn_f/conn_t (may be overwritten by template)
            conn_f, conn_t = parse_windings_connection(trafo.conn)
            conn_y_from = conn_f == WindingType.NeutralStar or conn_f == WindingType.GroundedStar
            conn_y_to = conn_t == WindingType.NeutralStar or conn_t == WindingType.GroundedStar

            if conn_f == WindingType.Delta and conn_y_to:  # Dy
                phase_displacement = np.deg2rad(60.0)
            elif conn_y_from and conn_t == WindingType.Delta:  # Yd
                phase_displacement = np.deg2rad(0.0)
            else:
                phase_displacement = 0.0
            theta_hk = Vaf - Vat
            block = Block(
                algebraic_vars=[Pf, Pt, Qf, Qt],
                algebraic_eqs=[
                    # From side: Pf = Re(Vf * (Yff*Vf + Yft*Vt)*)
                    Pf - ((Vmf ** 2 * (gFe + gt)) / (m * vtap_f) ** 2 - gt / (m * vtap_f * vtap_t) * Vmf * Vmt * cos(
                        theta_hk - phi) - bt / (m * vtap_f * vtap_t) * Vmf * Vmt * sin(
                        theta_hk - phi - phase_displacement)),
                    Qf - (-Vmf ** 2 * (bmu / 2 + bt) / (m * vtap_f) ** 2 - gt / (m * vtap_f * vtap_t) * Vmf * Vmt * sin(
                        theta_hk - phi) + bt / (m * vtap_f * vtap_t) * Vmf * Vmt * cos(
                        theta_hk - phi - phase_displacement)),
                    # To side: Pt = Re(Vt * (Ytf*Vf + Ytt*Vt)*)
                    Pt - ((Vmt ** 2 * (gFe + gt)) / vtap_t ** 2 - gt / (m * vtap_f * vtap_t) * Vmt * Vmf * cos(
                        theta_hk - phi) + bt / (m * vtap_f * vtap_t) * Vmt * Vmf * sin(
                        theta_hk - phi - phase_displacement)),
                    Qt - (-Vmt ** 2 * (bmu / 2 + bt) / vtap_t ** 2 + gt / (m * vtap_f * vtap_t) * Vmt * Vmf * sin(
                        theta_hk - phi) + bt / (m * vtap_f * vtap_t) * Vmt * Vmf * cos(
                        theta_hk - phi - phase_displacement)),
                ],
                event_dict={
                    m: vf.add_const(trafo.tap_module),
                    phi: vf.add_const(trafo.tap_phase)
                },
                in_vars=[Vmf, Vaf, Vmt, Vat],
            )

            block.external_mapping = {
                VarPowerFlowRefferenceType.Pf: Pf,
                VarPowerFlowRefferenceType.Pt: Pt,
                VarPowerFlowRefferenceType.Qf: Qf,
                VarPowerFlowRefferenceType.Qt: Qt,
            }

            block.parameters[gt] = vf.add_const(ys.real)
            block.parameters[bt] = vf.add_const(ys.imag)
            block.parameters[gFe] = vf.add_const(ysh.real)
            block.parameters[bmu] = vf.add_const(ysh.imag)

            if trafo.tap_module_control_mode != TapModuleControl.fixed:
                del block.event_dict[m]
                block.init_eqs[m] = vf.add_const(trafo.tap_module)

                Ki = vf.add_var('Ki_mod')
                Kd = vf.add_var('Kd_mod')
                var_ref = vf.add_var('var_ref')

                block.event_dict[Ki] = vf.add_const(0.1)
                block.event_dict[Kd] = vf.add_const(0.1)

                if trafo.tap_module_control_mode == TapModuleControl.Qf:
                    control_var = Qf
                    block.event_dict[var_ref] = vf.add_const(trafo.Qset)
                elif trafo.tap_module_control_mode == TapModuleControl.Qt:
                    control_var = Qt
                    block.event_dict[var_ref] = vf.add_const(trafo.Qset)
                elif trafo.tap_module_control_mode == TapModuleControl.Vm:
                    control_var = Vmt
                    block.event_dict[var_ref] = vf.add_const(trafo.vset)

                PI_control_block, _, _ = tf_to_block(
                    var_factory=vf,
                    num=[Ki],
                    den=[Kd, vf.add_const(1)],
                    x=control_var - var_ref,
                    y=m,
                )
                block.add(PI_control_block)

            if trafo.tap_phase_control_mode != TapPhaseControl.fixed:
                discretized_control = True
                if discretized_control:
                    del block.event_dict[phi]
                    block.init_eqs[phi] = vf.add_const(trafo.tap_phase)

                    Ki = vf.add_var('Ki_phase')
                    Kp = vf.add_var('Kp_phase')
                    Tm = vf.add_var('Tm')
                    var_ref = vf.add_var('var_ref')
                    block.event_dict[Ki] = vf.add_const(0.1)
                    block.event_dict[Kp] = vf.add_const(0.1)
                    block.event_dict[Tm] = vf.add_const(0.1)

                    if trafo.tap_phase_control_mode == TapPhaseControl.Pf:
                        control_var = Pf
                        block.event_dict[var_ref] = vf.add_const(trafo.Pset / Sbase)
                    elif trafo.tap_phase_control_mode == TapPhaseControl.Pt:
                        control_var = Pt
                        block.event_dict[var_ref] = vf.add_const(trafo.Pset / Sbase)

                    discretized_control,_ = discrete_control_block(
                        var_factory=vf,
                        m=m,
                        m_min=trafo.tap_phase_min,
                        m_max=trafo.tap_phase_max,
                        delta_m=trafo.tap_phase_step,
                        v=control_var,
                        v_ref=var_ref,
                        delta_v=0.01,
                        ts=Tm,
                    )
                    block.children.append(discretized_control)
                else:
                    del block.event_dict[phi]
                    block.init_eqs[phi] = vf.add_const(trafo.tap_phase)

                    Ki = vf.add_var('Ki_phase')
                    Kp = vf.add_var('Kp_phase')
                    var_ref = vf.add_var('var_ref')
                    block.event_dict[Ki] = vf.add_const(0.1)
                    block.event_dict[Kp] = vf.add_const(0.1)

                    if trafo.tap_phase_control_mode == TapPhaseControl.Pf:
                        control_var = Pf
                        block.event_dict[var_ref] = vf.add_const(trafo.Pset / Sbase)
                    elif trafo.tap_phase_control_mode == TapPhaseControl.Pt:
                        control_var = Pt
                        block.event_dict[var_ref] = vf.add_const(trafo.Pset / Sbase)

                    PI_control_block, _ = tf_to_block(
                        var_factory=vf,
                        num=[Ki, Kp],
                        den=[0, vf.add_const(1)],
                        x=control_var - var_ref,
                        y=phi,
                        name="Phase_Control_PI"
                    )
                    block.children.append(PI_control_block)
            block.unify_blocks()

            self._block = block

def initialize_trafo_rms(trafo: Transformer2W, vf: VarFactory, Sbase: float = 100):
    """

    :param trafo:
    :param vf:
    :param Sbase:
    :return:
    """
    trafo.rms_model = TrafoRmsTemplate(vf=vf, trafo=trafo, Sbase=Sbase).block
