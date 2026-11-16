"""Populate the native WECC-240 RAW/DYR case with scratch VeraGrid RMS models."""
from __future__ import annotations
from collections import defaultdict
from pathlib import Path
import csv, math, re, shlex
import numpy as np
import VeraGridEngine.api as gce
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.enumerations import DeviceType, VarPowerFlowReferenceType
from VeraGridEngine.Simulations.PowerFlow.power_flow_driver import PowerFlowDriver
from VeraGridEngine.Simulations.SmallSignalStabilityRms.small_signal_driver import SmallSignalStabilityRmsDriver
from VeraGridEngine.Simulations.SmallSignalStabilityRms.small_signal_options import RmsSmallSignalStabilityOptions
from VeraGridEngine.Templates.Rms.line.line_rms_template import get_line_rms_template
from VeraGridEngine.Templates.Rms.buses.shunt_template import get_shunt_template
from VeraGridEngine.Templates.Rms.transformers.transformer_rms_template import get_transformer2w_rms
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Templates.Rms.buses.bus_rms_template import initialize_bus_rms
from VeraGridEngine.Utils.Symbolic.templates_common_functions import set_rms_model
from run_veragrid_ieee9_powersystems_models import build_power_flow_options, build_rms_options
from wecc240_generators import get_wecc_generator_template
from wecc240_inverter import get_wecc_renewable_inverter_template

DATA=Path("/home/pablo/.julia/artifacts/6a6d544ec747fffa6471cf84d7ecce0effbf5c4d/PowerSystemsTestData-4.0.6/psid_tests/data_tests")
RAW=DATA/"240busWECC_2018_PSS32_fixed_shunts.raw"; DYR=DATA/"240busWECC_2018_PSS.dyr"

def read_dyr(path: Path):
    """Read native PSS/E records; this is input binding, not a Julia model exporter."""
    records=defaultdict(dict)
    for text in path.read_text(encoding="utf-8").split("/"):
        text=re.sub(r"(?m)^\s*@.*$","",text).replace(","," ")
        tokens=shlex.split(text,comments=False,posix=True)
        if len(tokens)<3: continue
        try: bus=int(tokens[0])
        except ValueError: continue
        model=tokens[1].upper(); unit=tokens[2].strip("'\"")
        try: values=[float(x) for x in tokens[3:]]
        except ValueError: continue
        records[(bus,unit)][model]=values
    return records

def saturation_coefficients(se1,se12):
    if se1<=0 or se12<=0: return 0.0,0.0
    root_b=(math.sqrt(1.2*se12)-math.sqrt(se1))/.2
    return 1-math.sqrt(se1)/root_b,root_b*root_b

def generator_parameters(gen, rec):
    g=rec["GENROU"]; xd,xq,xdp,xqp,xdpp,xl=g[6:12]; sa,sb=saturation_coefficients(g[12],g[13])
    machine={"R":0,"Td0_p":g[0],"Td0_pp":g[1],"Tq0_p":g[2],"Tq0_pp":g[3],"Xd":xd,"Xq":xq,
      "Xd_p":xdp,"Xq_p":xqp,"Xd_pp":xdpp,"Xl":xl,"gamma_d1":(xdpp-xl)/(xdp-xl),
      "gamma_q1":(xdpp-xl)/(xqp-xl),"gamma_d2":(xdp-xdpp)/(xdp-xl)**2,
      "gamma_q2":(xqp-xdpp)/(xqp-xl)**2,"gamma_qd":(xq-xl)/(xd-xl),"sat_A":sa,"sat_B":sb,
      "base_scale":gen.Snom/100.0}
    shaft={"H":g[4],"D":g[5]}; s=rec["SEXS"]
    avr={"Ta_Tb":s[0],"Tb":s[1],"K":s[2],"Te":s[3],"V_min":s[4],"V_max":s[5]}
    if "GAST" in rec:
        x=rec["GAST"]; kind="GasTG"; gov={"R":x[0],"T1":x[1],"T2":x[2],"T3":x[3],"AT":x[4],"Kt":x[5],"D_turb":x[8]}
    elif "TGOV1" in rec:
        x=rec["TGOV1"]; kind="SteamTurbineGov1"; gov={"R":x[0],"T1":x[1],"T2":x[4],"T3":x[5],"D_T":x[6]}
    else:
        x=rec["HYGOV"]; kind="HydroTurbineGov"; gov={"R":x[0],"r":x[1],"Tr":x[2],"Tf":x[3],"Tg":x[4],"Tw":x[8],"At":x[9],"D_T":x[10],"q_nl":x[11]}
    pss_kind="IEEEST" if "IEEEST" in rec else "PSSFixed"; pss={}
    if pss_kind=="IEEEST":
        x=rec["IEEEST"]; keys=("A1","A2","A3","A4","A5","A6","T1","T2","T3","T4","T5","T6","Ks")
        # DYR positions 1-2 are input-code and remote-bus flags.
        pss=dict(zip(keys,x[2:15]))
    return machine,shaft,avr,kind,gov,pss_kind,pss

def inverter_parameters(gen,rec):
    a=rec["REGCA1"]; e=rec["REECB1"]; p=rec["REPCA1"]
    return {"T_g_cnv":a[1],"Rrpwr":a[2],"T_fltr_cnv":a[10],"X_source":100000.0,"base_scale":gen.Snom/100.0,
      "T_p":p[24],"K_pg":p[22],"K_ig":p[23],"T_g_active":p[31],"T_pord":e[29],
      "T_q":p[7],"K_p":p[8],"K_i":p[9],"T_ft":p[10],"T_fv":p[11],"K_qp":e[19],"K_qi":e[20],
      "T_rv":e[7],"T_iq":e[29]}

def constant_impedance_load(vf,name,conductance,susceptance):
    t=RmsModelTemplate(name=name); t.tpe=DeviceType.LoadDevice
    vm=vf.add_var("Vm",VarPowerFlowReferenceType.Vm); va=vf.add_var("Va",VarPowerFlowReferenceType.Va)
    p=vf.add_var("Pl",VarPowerFlowReferenceType.P); q=vf.add_var("Ql",VarPowerFlowReferenceType.Q)
    # Names deliberately avoid API property matching: these values must be
    # derived from the complete solved ZIP load, not only its raw P/Q fields.
    g=vf.add_var("zload_conductance"); b=vf.add_var("zload_susceptance")
    # Injection convention: consumption enters the bus balance negatively.
    t.block=Block(algebraic_eqs=[p+g*vm*vm,q+b*vm*vm],algebraic_vars=[p,q],in_vars=[vm,va],out_vars=[p,q],
      event_dict={g:vf.add_const(conductance),b:vf.add_const(susceptance)},init_eqs={p:-g*vm*vm,q:-b*vm*vm},
      external_mapping={VarPowerFlowReferenceType.Vm:vm,VarPowerFlowReferenceType.Va:va,VarPowerFlowReferenceType.P:p,VarPowerFlowReferenceType.Q:q},name=name)
    return t

def seed_rms_branch_flows(grid, pf_results):
    """Seed branch powers from the exact RMS equations and solved voltages."""
    bus_index=grid.get_bus_index_dict()
    sf=[]; st=[]
    for branch in grid.get_branches_iter(add_vsc=False,add_hvdc=False,add_switch=True):
        if not branch.active:
            sf.append(0.0j); st.append(0.0j)
            continue
        vf=pf_results.voltage[bus_index[branch.bus_from]]
        vt=pf_results.voltage[bus_index[branch.bus_to]]
        y=1/complex(branch.R,branch.X)
        if branch.device_type==DeviceType.Transformer2WDevice:
            vtap_f,vtap_t=branch.get_virtual_taps(); m=branch.tap_module; phi=branch.tap_phase
            ysh=complex(branch.G,branch.B)/2
            i_f=(y+ysh)*vf/(m*vtap_f)**2-y*vt/(m*vtap_f*vtap_t)*np.exp(1j*phi)
            i_t=(y+ysh)*vt/vtap_t**2-y*vf/(m*vtap_f*vtap_t)*np.exp(-1j*phi)
        else:
            i_f=(vf-vt)*y+1j*branch.B*vf/2
            i_t=(vt-vf)*y+1j*branch.B*vt/2
        sf.append(vf*np.conj(i_f)); st.append(vt*np.conj(i_t))
    # RmsProblemDae converts the power-flow result arrays by Sbase on input.
    pf_results.Sf=np.asarray(sf,dtype=complex)*grid.Sbase
    pf_results.St=np.asarray(st,dtype=complex)*grid.Sbase

def normalize_wecc_static_models(grid):
    """Bind VeraGrid's imported static devices to PowerFlows.jl semantics."""
    for shunt in list(grid.controllable_shunts):
        grid.add_shunt(shunt.bus,gce.Shunt(name=shunt.name,G=shunt.G,B=shunt.B,active=shunt.active))
        grid.delete_controllable_shunt(shunt)
    for gen in grid.generators:
        gen.Vset=gen.bus.Vm0
    # PowerSystems resolves the RAW ZIP terms at the stored operating voltage
    # and imports the result as a constant-power load. Preserve that contract
    # when Q-limit enforcement moves the solved voltage away from Vm0.
    for load in grid.loads:
        vm0=float(load.bus.Vm0)
        load.P=float(load.P+load.Ir*vm0+load.G*vm0*vm0)
        load.Q=float(load.Q+load.Ii*vm0-load.B*vm0*vm0)
        load.Ir=load.Ii=load.G=load.B=0.0

def build_grid():
    grid=gce.open_file(str(RAW)); records=read_dyr(DYR)
    # PowerFlows.jl represents the imported WECC switched shunts at their
    # already-resolved RAW operating step.  Bind the same fixed admittance in
    # VeraGrid instead of asking the PF to solve a continuous shunt control.
    normalize_wecc_static_models(grid)
    for bus in grid.buses: initialize_bus_rms(bus,grid.var_factory)
    for i,line in enumerate(grid.lines):
        model=get_line_rms_template(grid.var_factory,f"wecc_line_{i}").block
        den=line.R*line.R+line.X*line.X
        explicit={"g":line.R/den,"b":-line.X/den,"bsh":line.B}
        for block in model.get_all_blocks():
            for parameter in list(block.parameters):
                if parameter.name in explicit:
                    block.parameters[parameter]=grid.var_factory.add_const(explicit[parameter.name])
            for event in list(block.event_dict):
                if event.name=="u":
                    block.event_dict[event]=grid.var_factory.add_const(1.0 if line.active else 0.0)
        # Bind the native RAW branch values directly.  The generic parameter
        # mapper applies the static-network scaling convention, while these
        # RMS equations and the solved voltages/flows are all system per-unit.
        model.api_obj_mapping={}
        set_rms_model(line,model,grid.var_factory)
    for i,tr in enumerate(grid.transformers2w):
        model=get_transformer2w_rms(grid.var_factory).block
        set_rms_model(tr,model,grid.var_factory)
    for i,shunt in enumerate(grid.shunts):
        model=get_shunt_template(grid.var_factory,f"wecc_shunt_{i}",phasor=False).block
        set_rms_model(shunt,model,grid.var_factory)
    missing=[]
    for gen in grid.generators:
        if not gen.active:
            continue
        key=(int(gen.bus.code),gen.name.rsplit("_",1)[-1]); rec=records.get(key)
        if not rec: missing.append(gen.name); continue
        if "GENROU" in rec:
            args=generator_parameters(gen,rec); model=get_wecc_generator_template(grid.var_factory,*args,name=f"WECC {gen.name}")
        else: model=get_wecc_renewable_inverter_template(grid.var_factory,inverter_parameters(gen,rec),f"WECC {gen.name}")
        set_rms_model(gen,model.block,grid.var_factory)
    if missing: raise RuntimeError(f"missing DYR records for {missing}")
    return grid

def build_prepared_grid():
    grid=build_grid(); print(f"grid: {len(grid.buses)} buses, {len(grid.generators)} generators")
    build_prepared_grid.static_load_pq = {
        load.name: (float(load.P), float(load.Q)) for load in grid.loads
    }
    pf_options=build_power_flow_options(); pf_options.retry_with_other_methods=True; pf_options.max_iter=100
    pf_options.control_Q=True
    pf=PowerFlowDriver(grid,pf_options); pf.run(); print(f"power flow converged: {pf.results.converged}")
    if not pf.results.converged: raise RuntimeError("WECC 240 power flow did not converge")
    seed_rms_branch_flows(grid,pf.results)
    bus_index=grid.get_bus_index_dict()
    for i,load in enumerate(grid.loads):
        vm=abs(pf.results.voltage[bus_index[load.bus]])
        # RAW ZIP coefficients are stored in MW/MVAr, unlike the already
        # per-unit solved branch and generator arrays used by this case.
        gp=(load.P+load.Ir*vm+load.G*vm*vm)/grid.Sbase/(vm*vm)
        bq=(load.Q+load.Ii*vm-load.B*vm*vm)/grid.Sbase/(vm*vm)
        # Seed the mapped P/Q variables with the complete solved ZIP injection;
        # the scratch RMS load then preserves it as constant impedance.
        load.P=-gp*vm*vm; load.Q=-bq*vm*vm
        load.Ir=load.Ii=load.G=load.B=0.0
        set_rms_model(load,constant_impedance_load(grid.var_factory,f"wecc_load_{i}",gp,bq).block,grid.var_factory)
    return grid

def main():
    grid=build_prepared_grid()
    pf_options=build_power_flow_options(); pf_options.retry_with_other_methods=True; pf_options.max_iter=100
    pf_options.control_Q=True
    pf=PowerFlowDriver(grid,pf_options); pf.run()
    driver=SmallSignalStabilityRmsDriver(grid=grid,rms_options=build_rms_options(),sss_options=RmsSmallSignalStabilityOptions(ss_assessment_time=0),pf_results=pf.results)
    owners={v.uid:d.name for d in [*grid.lines,*grid.transformers2w,*grid.loads,*grid.generators]
            for v in [*d.rms_model.external_mapping.values(),*d.rms_model.state_vars] if v is not None}
    equation_owners={v.uid:d.name for d in [*grid.lines,*grid.transformers2w,*grid.loads,*grid.shunts,*grid.generators]
                     for block in d.rms_model.get_all_blocks() for v in block.algebraic_vars}
    x0=driver.problem.get_x0(); dx=np.zeros_like(x0); sr=np.asarray(driver.problem.rhs_state(x0,dx)); ar=np.asarray(driver.problem.rhs_algebraic(x0,dx))
    for label,devices in (("line",grid.lines),("transformer",grid.transformers2w),("load",grid.loads),("shunt",grid.shunts),("generator",grid.generators)):
        vals=[]
        for d in devices:
            for ref,v in d.rms_model.external_mapping.items():
                if ref in {VarPowerFlowReferenceType.P,VarPowerFlowReferenceType.Q,VarPowerFlowReferenceType.Pf,VarPowerFlowReferenceType.Qf,VarPowerFlowReferenceType.Pt,VarPowerFlowReferenceType.Qt} and v is not None:
                    vals.append((abs(x0[driver.problem._uid2idx_vars[v.uid]]),d.name,ref.value,x0[driver.problem._uid2idx_vars[v.uid]]))
        print(f"largest {label} RMS powers: {sorted(vals,reverse=True)[:3]}")
    print(f"states={len(sr)} state residual={np.max(np.abs(sr)):.6g} algebraic residual={np.max(np.abs(ar)):.6g}")
    for i in np.argsort(np.nan_to_num(np.abs(sr),nan=np.inf))[-12:][::-1]:
        if abs(sr[i])>1e-6:
            v=driver.problem._state_vars[i]; print(f"  state {owners.get(v.uid,'?')} {v.name}: x0={x0[i]:+.6g} residual={sr[i]:+.6g} equation={driver.problem._state_eqs[i]}")
    for i in np.argsort(np.nan_to_num(np.abs(ar),nan=np.inf))[-12:][::-1]:
        if abs(ar[i])>1e-6:
            v=driver.problem._algebraic_vars[i]; j=driver.problem._uid2idx_vars[v.uid]
            eq=driver.problem._algebraic_eqs[i]; eq_owner=next((equation_owners[x.uid] for x in eq.get_vars() if x.uid in equation_owners),"?")
            print(f"  algebraic {eq_owner} {v.name}: x0={x0[j]:+.6g} residual={ar[i]:+.6g} equation={eq}")
    if not np.all(np.isfinite(sr)) or not np.all(np.isfinite(ar)):
        print("non-finite initialization residual; eigenvalue solve skipped")
        return
    driver.run(); eig=np.asarray(driver.results.eigenvalues,dtype=complex).reshape(-1)
    out=Path("results/wecc_240/veragrid_small_signal_eigenvalues.csv"); out.parent.mkdir(parents=True,exist_ok=True)
    with out.open("w",newline="") as f: w=csv.writer(f); w.writerow(("real","imag")); w.writerows((z.real,z.imag) for z in eig)
    with Path("/home/pablo/Desktop/eroots/power systems julia/results/wecc_240/small_signal_eigenvalues.csv").open() as f: ref=np.array([complex(float(r["real"]),float(r["imag"])) for r in csv.DictReader(f)])
    d=np.abs(eig[:,None]-ref[None,:]); print(f"eigenvalues VeraGrid={len(eig)} Julia={len(ref)} median={np.median(d.min(1)):.6g} max={d.min(1).max():.6g}")

if __name__=="__main__": main()
