"""Scratch VeraGrid RMS component models used by the PowerSystems WECC-240 case."""

from __future__ import annotations

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.enumerations import DeviceType, VarPowerFlowReferenceType
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.block_helpers import to_explicit
import VeraGridEngine.Utils.Symbolic.symbolic as sym


def _c(vf: VarFactory, value: float):
    return vf.add_const(float(value))


def get_round_rotor_quadratic_template(vf: VarFactory, parameters: dict, name="RoundRotorQuadratic") -> RmsModelTemplate:
    """PowerSimulationsDynamics GENROU/RoundRotorQuadratic machine."""
    t=RmsModelTemplate(name=name); t.tpe=DeviceType.GeneratorDevice
    vm=vf.add_var("Vm",VarPowerFlowReferenceType.Vm); va=vf.add_var("Va",VarPowerFlowReferenceType.Va)
    p=vf.add_var("Pg",VarPowerFlowReferenceType.P); q=vf.add_var("Qg",VarPowerFlowReferenceType.Q)
    delta=vf.add_var("delta"); omega=vf.add_var("omega"); field=vf.add_var("Vf")
    eq=vf.add_var("eq_p"); ed=vf.add_var("ed_p"); pkd=vf.add_var("psi_kd"); pkq=vf.add_var("psi_kq")
    torque=vf.add_var("electrical_torque")
    names=("R","Td0_p","Td0_pp","Tq0_p","Tq0_pp","Xd","Xq","Xd_p","Xq_p","Xd_pp","Xl",
           "gamma_d1","gamma_q1","gamma_d2","gamma_q2","gamma_qd","sat_A","sat_B","base_scale")
    R,Tdp,Tdpp,Tqp,Tqpp,Xd,Xq,Xdp,Xqp,Xdpp,Xl,gd1,gq1,gd2,gq2,gqd,sA,sB,scale=(vf.add_var(x) for x in names)
    vr=vm*sym.cos(va); vi=vm*sym.sin(va)
    vd=vr*sym.sin(delta)-vi*sym.cos(delta); vq=vr*sym.cos(delta)+vi*sym.sin(delta)
    psq=gq1*ed+(1-gq1)*pkq; psd=gd1*eq+gd2*(Xdp-Xl)*pkd
    den=R*R+Xdpp*Xdpp
    idv=(-R*(vd-psq)+Xdpp*(-vq+psd))/den
    iqv=(Xdpp*(vd-psq)+R*(-vq+psd))/den
    mag=sym.sqrt(psd*psd+psq*psq); sat=sB*(mag-sA)*(mag-sA)/mag
    xad=eq+(Xd-Xdp)*(gd1*idv-gd2*pkd+gd2*eq)+sat*psd
    xaq=ed+(Xq-Xqp)*(gq2*ed-gq2*pkq-gq1*iqv)+sat*psq*gqd
    te=idv*(vd+R*idv)+iqv*(vq+R*iqv)
    ir=scale*(idv*sym.sin(delta)+iqv*sym.cos(delta)); ii=scale*(-idv*sym.cos(delta)+iqv*sym.sin(delta))
    # Closed-form seed used by PSD before its optional nonlinear refinement.
    ir0=(p*vr+q*vi)/(vm*vm)/scale; ii0=(p*vi-q*vr)/(vm*vm)/scale
    psr=vr+R*ir0-Xdpp*ii0; psi=vi+R*ii0+Xdpp*ir0; psm=sym.sqrt(psr*psr+psi*psi)
    sat0=sB*(psm-sA)*(psm-sA)/psm; iang=sym.atan2(ii0,ir0); pang=sym.atan2(psi,psr)
    a=psm*(sat0*gqd+1); bb=(Xdpp-Xq)*sym.sqrt(ir0*ir0+ii0*ii0)
    d0=pang+sym.atan(bb*sym.cos(pang-iang)/(bb*sym.sin(pang-iang)-a))
    vd0=vr*sym.sin(d0)-vi*sym.cos(d0); vq0=vr*sym.cos(d0)+vi*sym.sin(d0)
    id0=ir0*sym.sin(d0)-ii0*sym.cos(d0); iq0=ir0*sym.cos(d0)+ii0*sym.sin(d0)
    psq0=vd0-R*id0-Xdpp*iq0; psd0=vq0+Xdpp*id0+R*iq0
    vf0=id0*(Xd-Xdpp)+psd0*(sat0+1)
    eq0=id0*(Xdp-Xd)-sat0*psd0+vf0; ed0=iq0*(Xq-Xqp)-sat0*gqd*psq0
    pkd0=-id0*(Xd-Xl)-sat0*psd0+vf0; pkq0=iq0*(Xq-Xl)-sat0*gqd*psq0
    defaults={"R":0,"Td0_p":6,"Td0_pp":.5,"Tq0_p":1,"Tq0_pp":.05,"Xd":1.4,"Xq":1.35,
              "Xd_p":.3,"Xq_p":.6,"Xd_pp":.2,"Xl":.1,"gamma_d1":.5,"gamma_q1":.2,
              "gamma_d2":2.5,"gamma_q2":1.6,"gamma_qd":.9615384615,"sat_A":.9333333333,
              "sat_B":6.75,"base_scale":1}
    defaults.update(parameters)
    events={v:_c(vf,defaults[n]) for v,n in zip((R,Tdp,Tdpp,Tqp,Tqpp,Xd,Xq,Xdp,Xqp,Xdpp,Xl,gd1,gq1,gd2,gq2,gqd,sA,sB,scale),names)}
    block=Block(state_eqs=[(field-xad)/Tdp,-xaq/Tqp,(-pkd+eq-(Xdp-Xl)*idv)/Tdpp,
                            (-pkq+ed+(Xqp-Xl)*iqv)/Tqpp],state_vars=[eq,ed,pkd,pkq],
        algebraic_eqs=[torque-te,p-vm*(sym.cos(va)*ir+sym.sin(va)*ii),q-vm*(sym.sin(va)*ir-sym.cos(va)*ii)],
        algebraic_vars=[torque,p,q],in_vars=[vm,va,delta,omega,field],out_vars=[p,q,torque],event_dict=events,
        init_eqs={delta:d0,omega:_c(vf,1),field:vf0,eq:eq0,ed:ed0,pkd:pkd0,pkq:pkq0,torque:p/scale},
        external_mapping={VarPowerFlowReferenceType.Vm:vm,VarPowerFlowReferenceType.Va:va,
                          VarPowerFlowReferenceType.P:p,VarPowerFlowReferenceType.Q:q},name=name)
    t.block.children.append(block); return t


def get_sexs_template(vf: VarFactory, parameters: dict, name="SEXS") -> RmsModelTemplate:
    """Two-state simplified excitation system, including its lead-lag state."""
    t=RmsModelTemplate(name=name); t.tpe=DeviceType.GeneratorDevice
    vm=vf.add_var("Vm_terminal"); vpss=vf.add_var("V_pss"); field=vf.add_var("Vf"); vr=vf.add_var("Vr")
    ratio,Tb,Te,K,vmin,vmax,vref=(vf.add_var(x) for x in ("Ta_Tb","Tb","Te","K","Vmin","Vmax","V_ref"))
    vin=vref+vpss-vm; vll=vr+ratio*vin
    dvr=(1-ratio)*vin-vr; raw=K*vll-field
    # WECC equilibria lie inside the limiter, making this expression identical
    # to PSD's non-windup block and its local Jacobian.
    b=Block(state_eqs=[raw/Te,dvr/Tb],state_vars=[field,vr],in_vars=[vm,vpss],out_vars=[field],
      event_dict={ratio:_c(vf,parameters.get("Ta_Tb",.1)),Tb:_c(vf,parameters.get("Tb",10)),Te:_c(vf,parameters.get("Te",.1)),
                  K:_c(vf,parameters.get("K",100)),vmin:_c(vf,parameters.get("V_min",0)),vmax:_c(vf,parameters.get("V_max",3)),
                  vref:vm+field/K-vpss},init_eqs={vr:(1-ratio)*(vref+vpss-vm)},name=name)
    t.block.children.append(b); return t


def get_wecc_governor_template(vf: VarFactory, kind: str, parameters: dict, name=None) -> RmsModelTemplate:
    """GasTG, SteamTurbineGov1, or HydroTurbineGov."""
    name=name or kind; t=RmsModelTemplate(name=name); t.tpe=DeviceType.GeneratorDevice
    w=vf.add_var("omega"); tm=vf.add_var("mechanical_torque"); pref=vf.add_var("P_ref")
    if kind=="GasTG":
        x1,x2,x3=(vf.add_var(f"x_g{i}") for i in range(1,4)); R,T1,T2,T3,D,AT,KT=(vf.add_var(x) for x in ("R","T1","T2","T3","D_turb","AT","Kt"))
        xin=sym.min(pref-(w-1)/R,AT+KT*(AT-x3)); pm=x2-D*(w-1)
        ev={R:_c(vf,parameters.get("R",.05)),T1:_c(vf,parameters.get("T1",.3)),T2:_c(vf,parameters.get("T2",.3)),T3:_c(vf,parameters.get("T3",3)),D:_c(vf,parameters.get("D_turb",0)),AT:_c(vf,parameters.get("AT",1)),KT:_c(vf,parameters.get("Kt",2)),pref:tm}
        b=Block(state_eqs=[(xin-x1)/T1,(x1-x2)/T2,(x2-x3)/T3],state_vars=[x1,x2,x3],algebraic_eqs=[tm-pm/w],algebraic_vars=[tm],in_vars=[w],out_vars=[tm],event_dict=ev,init_eqs={x1:tm,x2:tm,x3:tm},name=name)
    elif kind=="SteamTurbineGov1":
        x1,x2=vf.add_var("x_g1"),vf.add_var("x_g2"); R,T1,T2,T3,D=(vf.add_var(x) for x in ("R","T1","T2","T3","D_T")); y=x2+(T2/T3)*x1; pm=y-D*(w-1)
        ev={R:_c(vf,parameters.get("R",.05)),T1:_c(vf,parameters.get("T1",.1)),T2:_c(vf,parameters.get("T2",.2)),T3:_c(vf,parameters.get("T3",.5)),D:_c(vf,parameters.get("D_T",0)),pref:R*tm}
        b=Block(state_eqs=[((pref-(w-1))/R-x1)/T1,(x1*(1-T2/T3)-x2)/T3],state_vars=[x1,x2],algebraic_eqs=[tm-pm/w],algebraic_vars=[tm],in_vars=[w],out_vars=[tm],event_dict=ev,init_eqs={x1:tm,x2:tm*(1-T2/T3)},name=name)
    elif kind=="HydroTurbineGov":
        x1,x2,x3,x4=(vf.add_var(f"x_g{i}") for i in range(1,5)); R,r,Tr,Tf,Tg,Tw,At,Dt,qnl=(vf.add_var(x) for x in ("R","r","Tr","Tf","Tg","Tw","At","D_T","q_nl"))
        c=x1/r+x2/(r*Tr); h=(x4/x3)*(x4/x3); pm=((x4-qnl)*h*At-Dt*(w-1)*x3)/w
        ev={R:_c(vf,parameters.get("R",.05)),r:_c(vf,parameters.get("r",.05)),Tr:_c(vf,parameters.get("Tr",5)),Tf:_c(vf,parameters.get("Tf",.05)),Tg:_c(vf,parameters.get("Tg",.5)),Tw:_c(vf,parameters.get("Tw",1)),At:_c(vf,parameters.get("At",1)),Dt:_c(vf,parameters.get("D_T",0)),qnl:_c(vf,parameters.get("q_nl",0)),pref:R*(qnl+tm/At)}
        gate=qnl+tm/At
        b=Block(state_eqs=[(pref-(w-1)-R*c-x1)/Tf,x1,(c-x3)/Tg,(1-h)/Tw],state_vars=[x1,x2,x3,x4],algebraic_eqs=[tm-pm],algebraic_vars=[tm],in_vars=[w],out_vars=[tm],event_dict=ev,init_eqs={x1:_c(vf,0),x2:r*Tr*gate,x3:gate,x4:gate},name=name)
    else: raise ValueError(f"unsupported WECC governor {kind}")
    t.block.children.append(b); return t


def get_ieeest_wecc_template(vf: VarFactory, parameters: dict, name="IEEEST") -> RmsModelTemplate:
    """WECC IEEEST specialization with the A4=T4=0 algebraic states eliminated."""
    t=RmsModelTemplate(name=name); t.tpe=DeviceType.GeneratorDevice
    w=vf.add_var("omega"); out=vf.add_var("V_pss")
    x2,x3,x4,x5,x7=(vf.add_var(n) for n in ("x_p2","x_p3","x_p4","x_p5","x_p7"))
    A1,A2,A3,A5,A6,T1,T2,Ks,T5,T6=(vf.add_var(n) for n in ("A1","A2","A3","A5","A6","T1","T2","Ks","T5","T6"))
    u=w-1
    # With A3=A4=0, the descriptor reduction removes x_p1 and retains x_p2
    # as a zero-dynamics state.
    # T4=0 imposes x_p6=y_LL1.  The remaining five states are exactly the
    # finite part of Julia's seven-state descriptor realization.
    # Julia removes the structurally empty x_p1 algebraic row/column from its
    # reduced Jacobian.  The retained x_p2 row consequently has zero dynamics.
    yf=(A6/A2)*x2+(A5-A1*A6/A2)*x3+(1-A6/A2)*x4
    y1=x5+(T1/T2)*yf
    y=x7+Ks*(T5/T6)*y1
    ev={A1:_c(vf,parameters.get("A1",1.013)),A2:_c(vf,parameters.get("A2",.013)),
        A3:_c(vf,parameters.get("A3",0.0)),A5:_c(vf,parameters.get("A5",1.013)),
        A6:_c(vf,parameters.get("A6",.113)),T1:_c(vf,parameters.get("T1",7)),
        T2:_c(vf,parameters.get("T2",.02)),Ks:_c(vf,parameters.get("Ks",3)),
        T5:_c(vf,parameters.get("T5",1.65)),T6:_c(vf,parameters.get("T6",1.65))}
    b=Block(state_eqs=[_c(vf,0),(x2-A1*x3-x4)/A2,x3,((1-T1/T2)*yf-x5)/T2,
                        (-(Ks*(T5/T6)*y1+x7))/T6],state_vars=[x2,x3,x4,x5,x7],
        algebraic_eqs=[out-y],algebraic_vars=[out],in_vars=[w],out_vars=[out],event_dict=ev,
        init_eqs={x2:_c(vf,0),x3:_c(vf,0),x4:_c(vf,0),x5:_c(vf,0),x7:_c(vf,0),out:_c(vf,0)},name=name)
    t.block.children.append(b); return t


def get_wecc_generator_template(vf: VarFactory, machine_parameters: dict, shaft_parameters: dict,
                                avr_parameters: dict, governor_kind: str, governor_parameters: dict,
                                pss_kind="PSSFixed", pss_parameters=None, name="WECC generator") -> RmsModelTemplate:
    """Complete WECC synchronous generator with a Vm/Va/P/Q root interface."""
    machine=get_round_rotor_quadratic_template(vf,machine_parameters,f"{name} machine").block.children[0]
    sexs=get_sexs_template(vf,avr_parameters,f"{name} SEXS").block.children[0]
    gov=get_wecc_governor_template(vf,governor_kind,governor_parameters,f"{name} {governor_kind}").block.children[0]
    delta=vf.add_var("delta"); omega=vf.add_var("omega"); tm=vf.add_var("mechanical_torque"); te=vf.add_var("electrical_torque")
    H=vf.add_var("H"); D=vf.add_var("D"); wb=vf.add_var("omega_base")
    shaft=Block(state_eqs=[wb*(omega-1),(tm-te-D*(omega-1))/(2*H)],state_vars=[delta,omega],
        in_vars=[tm,te],out_vars=[delta,omega],event_dict={H:_c(vf,shaft_parameters.get("H",3)),D:_c(vf,shaft_parameters.get("D",0)),wb:_c(vf,2*3.141592653589793*60)},
        init_eqs={omega:_c(vf,1)},name=f"{name} SingleMass")
    # Machine ports: Vm, Va, delta, omega, Vf. Outputs: P, Q, electrical torque.
    vf.add_connection(machine.in_vars[2],shaft.out_vars[0]); vf.add_connection(machine.in_vars[3],shaft.out_vars[1])
    vf.add_connection(shaft.in_vars[1],machine.out_vars[2]); vf.add_connection(gov.in_vars[0],shaft.out_vars[1]); vf.add_connection(shaft.in_vars[0],gov.out_vars[0])
    gov.init_eqs[gov.out_vars[0]]=machine.out_vars[2]
    vf.add_connection(sexs.in_vars[0],machine.in_vars[0]); vf.add_connection(machine.in_vars[4],sexs.out_vars[0])
    children=[machine,shaft,gov]
    if pss_kind=="IEEEST":
        pss=get_ieeest_wecc_template(vf,pss_parameters or {},f"{name} IEEEST").block.children[0]
        vf.add_connection(pss.in_vars[0],shaft.out_vars[1]); vf.add_connection(sexs.in_vars[1],pss.out_vars[0]); children.append(pss)
    elif pss_kind=="PSSFixed":
        sexs.event_dict[sexs.in_vars[1]]=_c(vf,0); sexs.in_vars=[sexs.in_vars[0]]
    else: raise ValueError(f"unsupported WECC PSS {pss_kind}")
    children.append(sexs)
    t=RmsModelTemplate(name=name); t.tpe=DeviceType.GeneratorDevice; t.block.children.extend(children)
    t.block.external_mapping={VarPowerFlowReferenceType.Vm:machine.in_vars[0],VarPowerFlowReferenceType.Va:machine.in_vars[1],
        VarPowerFlowReferenceType.P:machine.out_vars[0],VarPowerFlowReferenceType.Q:machine.out_vars[1]}
    t.block.in_vars=machine.in_vars[:2]; t.block.out_vars=machine.out_vars[:2]; t.block.name=name
    t.block=to_explicit(t.block,vf); return t
