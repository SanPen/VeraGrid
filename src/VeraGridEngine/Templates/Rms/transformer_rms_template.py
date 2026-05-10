# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import numpy as np
from VeraGridEngine.enumerations import DeviceType, TapPhaseControl, TapModuleControl, WindingType, ParamPowerFlowRefferenceType
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Devices.Branches.transformer import Transformer2W
from VeraGridEngine.Utils.Symbolic.block import Block, VarPowerFlowRefferenceType
from VeraGridEngine.Utils.Symbolic.symbolic import sin, cos
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

    def __init__(self, vf: VarFactory, name: str = "rms_trafo_template"):
        """
        Created the RMS Template of a Bus
        :param vf: VarFactory
        :param name: Name of the RMS Model
        """
        super().__init__(name=name)

        vf = vf
        self.tpe: DeviceType = DeviceType.Transformer2WDevice
        Qf = vf.add_var("Qf")
        Qt = vf.add_var("Qt")
        Pf = vf.add_var("Pf")
        Pt = vf.add_var("Pt")
        m = vf.add_var('m')
        phi = vf.add_var('phi')
        gt = vf.add_var("g")
        bt = vf.add_var("b")
        gFe = vf.add_var('gFe')
        bmu = vf.add_var('bmu')
        vtap_f = vf.add_var('vtap_f')
        vtap_t = vf.add_var('vtap_t')

        # print(f"DEBUG Trafo: R={trafo.R}, X={trafo.X}, G={trafo.G}, B={trafo.B}")
        # print(f"DEBUG Trafo: tap_mod={trafo.tap_module}, tap_phase={trafo.tap_phase}, vtap_f={vtap_f}, vtap_t={vtap_t}")
        # print(f"vtap  p is {vtap_f}")
        # print(f"vtap  t is {vtap_t}")
        # print(f'ys is {ys} ysh is {ysh}')
        Vmf = vf.add_var('Vmf', VarPowerFlowRefferenceType.Vmf)
        Vaf = vf.add_var('Vaf', VarPowerFlowRefferenceType.Vaf)
        Vmt = vf.add_var('Vmt', VarPowerFlowRefferenceType.Vmt)
        Vat = vf.add_var('Vat', VarPowerFlowRefferenceType.Vat)
        inputs = [Vmf, Vaf, Vmt, Vat]
        # Calculate phase displacement matching transformer_admittance logic
        # Use conn attribute (preserves user intent) instead of conn_f/conn_t (may be overwritten by template)
        # conn_f, conn_t = parse_windings_connection(trafo.conn)
        # conn_y_from = conn_f == WindingType.NeutralStar or conn_f == WindingType.GroundedStar
        # conn_y_to = conn_t == WindingType.NeutralStar or conn_t == WindingType.GroundedStar
        # if conn_f == WindingType.Delta and conn_y_to:  # Dy
        #    phase_displacement = np.deg2rad(60.0)
        # elif conn_y_from and conn_t == WindingType.Delta:  # Yd
        #    phase_displacement = np.deg2rad(0.0)
        # else:
        #    phase_displacement = 0.0

        phase_displacement = 0
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
            in_vars=[Vmf, Vaf, Vmt, Vat],
        )
        block.external_mapping = {
            VarPowerFlowRefferenceType.Pf: Pf,
            VarPowerFlowRefferenceType.Pt: Pt,
            VarPowerFlowRefferenceType.Qf: Qf,
            VarPowerFlowRefferenceType.Qt: Qt,
            VarPowerFlowRefferenceType.Vaf: Vaf,
            VarPowerFlowRefferenceType.Vmf: Vmf,
            VarPowerFlowRefferenceType.Vmt: Vmt,
            VarPowerFlowRefferenceType.Vat: Vat,
        }
        block.api_obj_mapping = {
            ParamPowerFlowRefferenceType.g: gt,
            ParamPowerFlowRefferenceType.b: bt,
            ParamPowerFlowRefferenceType.gFe: gFe,
            ParamPowerFlowRefferenceType.bsh: bmu,
            ParamPowerFlowRefferenceType.transformer_tap_module: m,
            ParamPowerFlowRefferenceType.transformer_tap_phase: phi,
            ParamPowerFlowRefferenceType.vtap_f: vtap_f,
            ParamPowerFlowRefferenceType.vtap_t: vtap_t,
        }

        block.parameters[gt] = vf.add_const(0.0)
        block.parameters[bt] = vf.add_const(0.0)
        block.parameters[gFe] = vf.add_const(0.0)
        block.parameters[bmu] = vf.add_const(0.0)
        block.parameters[m] = vf.add_const(1.0)
        block.parameters[phi] = vf.add_const(0.0)
        block.parameters[vtap_f] = vf.add_const(1.0)
        block.parameters[vtap_t] = vf.add_const(1.0)
        #
        # if trafo.tap_module_control_mode != TapModuleControl.fixed:
        #    del block.event_dict[m]
        #        block.init_eqs[m] = vf.add_const(trafo.tap_module)

        #        Ki = vf.add_var('Ki_mod')
        #        Kd = vf.add_var('Kd_mod')
        #        var_ref = vf.add_var('var_ref')

        #        block.event_dict[Ki] = vf.add_const(0.1)
        #        block.event_dict[Kd] = vf.add_const(0.1)

        #        if trafo.tap_module_control_mode == TapModuleControl.Qf:
        #            control_var = Qf
        #            block.event_dict[var_ref] = vf.add_const(trafo.Qset)
        #        elif trafo.tap_module_control_mode == TapModuleControl.Qt:
        #            control_var = Qt
        #            block.event_dict[var_ref] = vf.add_const(trafo.Qset)
        #        elif trafo.tap_module_control_mode == TapModuleControl.Vm:
        #            control_var = Vmt
        #            block.event_dict[var_ref] = vf.add_const(trafo.vset)

        #        PI_control_block, _, _ = tf_to_block(
        #            var_factory=vf,
        #            num=[Ki],
        #            den=[Kd, vf.add_const(1)],
        #            x=control_var - var_ref,
        #            y=m,
        #        )
        #        block.add(PI_control_block)

        #    if trafo.tap_phase_control_mode != TapPhaseControl.fixed:
        #        discretized_control = True
        #        if discretized_control:
        #            del block.event_dict[phi]
        #            block.init_eqs[phi] = vf.add_const(trafo.tap_phase)

        #            Ki = vf.add_var('Ki_phase')
        #            Kp = vf.add_var('Kp_phase')
        #            Tm = vf.add_var('Tm')
        #            var_ref = vf.add_var('var_ref')
        #            block.event_dict[Ki] = vf.add_const(0.1)
        #            block.event_dict[Kp] = vf.add_const(0.1)
        #            block.event_dict[Tm] = vf.add_const(0.1)

        #            if trafo.tap_phase_control_mode == TapPhaseControl.Pf:
        #                control_var = Pf
        #                block.event_dict[var_ref] = vf.add_const(trafo.Pset / Sbase)
        #            elif trafo.tap_phase_control_mode == TapPhaseControl.Pt:
        #                control_var = Pt
        #                block.event_dict[var_ref] = vf.add_const(trafo.Pset / Sbase)

        #            discretized_control,_ = discrete_control_block(
        #                var_factory=vf,
        #                m=m,
        #                m_min=trafo.tap_phase_min,
        #                m_max=trafo.tap_phase_max,
        #                delta_m=trafo.tap_phase_step,
        #                v=control_var,
        #                v_ref=var_ref,
        #                delta_v=0.01,
        #                ts=Tm,
        #            )
        #            block.children.append(discretized_control)
        #        else:
        #            del block.event_dict[phi]
        #            block.init_eqs[phi] = vf.add_const(trafo.tap_phase)

        #            Ki = vf.add_var('Ki_phase')
        #            Kp = vf.add_var('Kp_phase')
        #            var_ref = vf.add_var('var_ref')
        #            block.event_dict[Ki] = vf.add_const(0.1)
        #            block.event_dict[Kp] = vf.add_const(0.1)

        #            if trafo.tap_phase_control_mode == TapPhaseControl.Pf:
        #                control_var = Pf
        #                block.event_dict[var_ref] = vf.add_const(trafo.Pset / Sbase)
        #            elif trafo.tap_phase_control_mode == TapPhaseControl.Pt:
        #                control_var = Pt
        #                block.event_dict[var_ref] = vf.add_const(trafo.Pset / Sbase)

        #            PI_control_block, _ = tf_to_block(
        #                var_factory=vf,
        #                num=[Ki, Kp],
        #                den=[0, vf.add_const(1)],
        #                x=control_var - var_ref,
        #                y=phi,
        #                name="Phase_Control_PI"
        #            )
        #            block.children.append(PI_control_block)
        #    block.unify_blocks()

        block.in_vars = inputs

        self._block = block


class TrafoPhasorRmsTemplate(RmsModelTemplate):

    def __init__(self, vf: VarFactory, name: str = "rms_trafo_phasor_template"):
        """
        Current-based phasor RMS template for a 2-winding transformer.

        Inputs use rectangular bus voltages (Vrf, Vif, Vrt, Vit) and outputs
        branch currents directly (Irf, Iif, Irt, Iit), matching the line phasor
        template interface used by current-balance RMS formulations.
        """
        super().__init__(name=name)

        self.tpe: DeviceType = DeviceType.Transformer2WDevice
        Vrf = vf.add_var("Vrf_" + name, VarPowerFlowRefferenceType.Vrf)
        Vif = vf.add_var("Vif_" + name, VarPowerFlowRefferenceType.Vif)
        Vrt = vf.add_var("Vrt_" + name, VarPowerFlowRefferenceType.Vrt)
        Vit = vf.add_var("Vit_" + name, VarPowerFlowRefferenceType.Vit)

        Irf = vf.add_var("Irf")
        Iif = vf.add_var("Iif")
        Irt = vf.add_var("Irt")
        Iit = vf.add_var("Iit")

        gt = vf.add_var("g")
        bt = vf.add_var("b")
        gFe = vf.add_var("gFe")
        bmu = vf.add_var("bmu")
        tap_module = vf.add_var("tap_module")
        tap_phase = vf.add_var("tap_phase")
        vtap_f = vf.add_var("vtap_f")
        vtap_t = vf.add_var("vtap_t")
        phase_displacement = vf.add_var("phase_displacement")

        theta0 = tap_phase + phase_displacement
        cos_theta0 = cos(theta0)
        sin_theta0 = sin(theta0)

        k_from = tap_module * vtap_f
        k_cross = tap_module * vtap_f * vtap_t
        k_to = vtap_t

        # Admittance coefficients in rectangular form
        gff = (gFe + gt) / (k_from ** 2)
        bff = (bmu / 2 + bt) / (k_from ** 2)
        gtt = (gFe + gt) / (k_to ** 2)
        btt = (bmu / 2 + bt) / (k_to ** 2)

        # Yft = -(gt + j*bt) / (m*vtap_f*vtap_t*exp(-j*theta))
        gft = -(gt * cos_theta0 - bt * sin_theta0) / k_cross
        bft = -(gt * sin_theta0 + bt * cos_theta0) / k_cross

        # Ytf = -(gt + j*bt) / (m*vtap_f*vtap_t*exp(j*theta))
        gtf = -(gt * cos_theta0 + bt * sin_theta0) / k_cross
        btf = (gt * sin_theta0 - bt * cos_theta0) / k_cross

        block = Block(
            algebraic_vars=[Irf, Iif, Irt, Iit],
            algebraic_eqs=[
                Irf - (gff * Vrf - bff * Vif + gft * Vrt - bft * Vit),
                Iif - (bff * Vrf + gff * Vif + bft * Vrt + gft * Vit),
                Irt - (gtf * Vrf - btf * Vif + gtt * Vrt - btt * Vit),
                Iit - (btf * Vrf + gtf * Vif + btt * Vrt + gtt * Vit),
            ],
            in_vars=[Vrf, Vif, Vrt, Vit],
        )

        block.external_mapping = {
            VarPowerFlowRefferenceType.Vrf: Vrf,
            VarPowerFlowRefferenceType.Vif: Vif,
            VarPowerFlowRefferenceType.Vrt: Vrt,
            VarPowerFlowRefferenceType.Vit: Vit,
            VarPowerFlowRefferenceType.Irf: Irf,
            VarPowerFlowRefferenceType.Iif: Iif,
            VarPowerFlowRefferenceType.Irt: Irt,
            VarPowerFlowRefferenceType.Iit: Iit,
        }

        block.api_obj_mapping = {
            ParamPowerFlowRefferenceType.g: gt,
            ParamPowerFlowRefferenceType.b: bt,
            ParamPowerFlowRefferenceType.bsh: bmu,
            ParamPowerFlowRefferenceType.gFe: gFe,
            ParamPowerFlowRefferenceType.transformer_tap_module: tap_module,
            ParamPowerFlowRefferenceType.transformer_tap_ratio: tap_phase,
            ParamPowerFlowRefferenceType.vtap_f: vtap_f,
            ParamPowerFlowRefferenceType.vtap_t: vtap_t,
        }

        block.parameters[gt] = vf.add_const(0.0)
        block.parameters[bt] = vf.add_const(0.0)
        block.parameters[gFe] = vf.add_const(0.0)
        block.parameters[bmu] = vf.add_const(0.0)
        block.parameters[tap_module] = vf.add_const(1.0)
        block.parameters[tap_phase] = vf.add_const(0.0)
        block.parameters[vtap_f] = vf.add_const(1.0)
        block.parameters[vtap_t] = vf.add_const(1.0)
        block.parameters[phase_displacement] = vf.add_const(0)

        self._block = block


def get_transformer2w_rms(vf: VarFactory, use_phasor_template: bool = False):
    if use_phasor_template:
        return TrafoPhasorRmsTemplate(vf=vf)
    return TrafoRmsTemplate(vf=vf)


def initialize_trafo_rms(trafo: Transformer2W, vf: VarFactory):
    """

    :param trafo:
    :param vf:
    :return:
    """
    templ = TrafoRmsTemplate(vf=vf)
    trafo.rms_model = templ.block
    return templ
