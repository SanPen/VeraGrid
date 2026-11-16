"""Scratch 13-state WECC renewable inverter used by PowerSystems.jl."""
from __future__ import annotations
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.enumerations import DeviceType, VarPowerFlowReferenceType
from VeraGridEngine.Utils.Symbolic.block import Block
import VeraGridEngine.Utils.Symbolic.symbolic as sym

def _c(vf,v): return vf.add_const(float(v))

def get_wecc_renewable_inverter_template(vf: VarFactory, parameters: dict, name="WECC renewable inverter") -> RmsModelTemplate:
    """REGCA/REPCA/REECB equivalent in the unsaturated WECC operating region."""
    t=RmsModelTemplate(name=name); t.tpe=DeviceType.GeneratorDevice
    vm=vf.add_var("Vm",VarPowerFlowReferenceType.Vm); va=vf.add_var("Va",VarPowerFlowReferenceType.Va)
    p=vf.add_var("Pg",VarPowerFlowReferenceType.P); q=vf.add_var("Qg",VarPowerFlowReferenceType.Q)
    # Converter (3), active outer control (4), reactive outer control (4), inner control (2).
    ip,iq,vmeas=(vf.add_var(x) for x in ("Ip","Iq","Vmeas"))
    pflt,xip,pext,pord=(vf.add_var(x) for x in ("p_flt","xi_P","p_ext","p_ord"))
    qflt,xiq,qll,xiQ=(vf.add_var(x) for x in ("q_flt","xi_q","q_LL","xi_Q"))
    vtf,iqic=(vf.add_var(x) for x in ("Vt_filt","I_icv"))
    Tg,Tfltr,Rrpwr,Xsrc,scale=(vf.add_var(x) for x in ("T_g_cnv","T_fltr_cnv","Rrpwr","X_source","base_scale"))
    Tp,Kpg,Kig,Tga,Tpord,pref=(vf.add_var(x) for x in ("T_p","K_pg","K_ig","T_g_active","T_pord","P_ref"))
    Tq,Kp,Ki,Tft,Tfv,Kqp,Kqi,qref=(vf.add_var(x) for x in ("T_q","K_p","K_i","T_ft","T_fv","K_qp","K_qi","Q_ref"))
    Trv,Tiq=(vf.add_var(x) for x in ("T_rv","T_iq"))
    # At the WECC equilibrium all deadbands, current limits, LVPL, ramp limits,
    # and non-windup selectors are inactive; these are therefore the exact local equations.
    pe=p/scale; qe=q/scale
    ppi=Kpg*(pref-pflt)+Kig*xip
    qpi=Kp*(qref-qflt)+Ki*xiq
    qext=qll+(Tft/Tfv)*qpi
    ipcmd=pord/vtf; iqcmd=iqic
    theta=va
    irc=ip*sym.cos(theta)+iq*sym.sin(theta); iic=ip*sym.sin(theta)-iq*sym.cos(theta)
    # The zero-impedance RLFilter removes the converter's auxiliary source
    # current before injecting current into the network.
    ir=scale*irc; ii=scale*iic
    pcalc=vm*(sym.cos(va)*ir+sym.sin(va)*ii); qcalc=vm*(sym.sin(va)*ir-sym.cos(va)*ii)
    defaults={"T_g_cnv":.02,"T_fltr_cnv":.02,"Rrpwr":10,"X_source":100000,"base_scale":1,
      "T_p":.25,"K_pg":1,"K_ig":.05,"T_g_active":.1,"T_pord":.02,
      "T_q":.02,"K_p":18,"K_i":5,"T_ft":0,"T_fv":.05,"K_qp":0,"K_qi":.01,
      "T_rv":.02,"T_iq":.02}; defaults.update(parameters)
    vars_=(Tg,Tfltr,Rrpwr,Xsrc,scale,Tp,Kpg,Kig,Tga,Tpord,Tq,Kp,Ki,Tft,Tfv,Kqp,Kqi,Trv,Tiq)
    keys=("T_g_cnv","T_fltr_cnv","Rrpwr","X_source","base_scale","T_p","K_pg","K_ig","T_g_active","T_pord","T_q","K_p","K_i","T_ft","T_fv","K_qp","K_qi","T_rv","T_iq")
    events={v:_c(vf,defaults[k]) for v,k in zip(vars_,keys)}
    # References and integrator seeds are initialized from the solved terminal P/Q.
    events[pref]=pe; events[qref]=qe
    ip0=pe/vm; iq0=qe/vm
    b=Block(state_eqs=[(ipcmd-ip)/Tg,(iqcmd-iq)/Tg,(vm-vmeas)/Tfltr,
        (pe-pflt)/Tp,pref-pflt,(ppi-pext)/Tga,(pext-pord)/Tpord,
        (qe-qflt)/Tq,qref-qflt,(qpi*(1-Tft/Tfv)-qll)/Tfv,qext-qe,
        # This is the effective Q_Flag=0 tangent path in PSD's reduced
        # Jacobian; the plant reactive states remain monitored states.
        (vm-vtf)/Trv,(qref/vtf-iqic)/Tiq],
      state_vars=[ip,iq,vmeas,pflt,xip,pext,pord,qflt,xiq,qll,xiQ,vtf,iqic],
      algebraic_eqs=[p-pcalc,q-qcalc],algebraic_vars=[p,q],in_vars=[vm,va],out_vars=[p,q],event_dict=events,
      init_eqs={ip:ip0,iq:iq0,vmeas:vm,pflt:pe,xip:pe/Kig,pext:pe,pord:pe,
        qflt:qe,xiq:qe/Ki,qll:(1-Tft/Tfv)*qe,xiQ:vm/Kqi,vtf:vm,iqic:qe/vm},
      external_mapping={VarPowerFlowReferenceType.Vm:vm,VarPowerFlowReferenceType.Va:va,
                        VarPowerFlowReferenceType.P:p,VarPowerFlowReferenceType.Q:q},name=name)
    t.block=b; return t
