# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Independent reactor equations and accepted-step blocking/reconnection behavior."""
import math
import numpy as np
import pytest
from VeraGridEngine.IO.dgs.dynamic_models.dgs_adapter_block_from_native_dgs import (
    build_dgs_elmgenstat_voltage_source_block, build_dgs_elmgenstat_block)
from VeraGridEngine.IO.dgs.dynamic_models.dgs_genstat_protection import apply_genstat_voltage_protection
from VeraGridEngine.Utils.procedural_logic import ProceduralExpressionMode
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from tests.DynamicCatalog._catalog_functional_support import FunctionalRuntimeProblem


@pytest.mark.parametrize('base,rating,uk,loss', [(100.,25.,10.,50.), (50.,200.,15.,0.)])
@pytest.mark.parametrize('angle', [.0,.7,-1.2])
def test_voltage_source_matches_complex_reactor_equation_and_initialization(base,rating,uk,loss,angle):
    b = build_dgs_elmgenstat_voltage_source_block(base,rating,uk,loss)
    v = .93*complex(math.cos(angle), math.sin(angle))
    e = v + complex(.03,.06)
    r = loss/(1000*rating)
    z = complex(r,math.sqrt((uk/100)**2-r*r))
    current = (e-v)/z
    power = v*current.conjugate()
    outputs = [power.real*rating/base,power.imag*rating/base,power.real,power.imag,
               v.real,v.imag,current.real,current.imag]
    values={q.uid:value for q,value in zip(b.in_vars,[.93,angle,e.real,e.imag])}
    values.update({q.uid:value for q,value in zip(b.out_vars,outputs)})
    assert max(abs(eq.eval_uid(values)) for eq in b.algebraic_eqs)<1e-12
    assert b.init_eqs[b.in_vars[2]].eval_uid(values)==pytest.approx(e.real)
    assert b.init_eqs[b.in_vars[3]].eval_uid(values)==pytest.approx(e.imag)


@pytest.mark.parametrize('uk,loss', [(0.,0.),(-1.,0.),(1.,1000.),(float('nan'),0.)])
def test_voltage_source_rejects_undefined_series_reactor(uk,loss):
    with pytest.raises(ValueError):build_dgs_elmgenstat_voltage_source_block(100.,25.,uk,loss)


@pytest.mark.parametrize('mode', [ProceduralExpressionMode.Compiled,ProceduralExpressionMode.Interpreted])
@pytest.mark.parametrize('voltage_source',[False,True])
def test_blocking_hysteresis_restart_delay_and_timer_cancellation(mode,voltage_source):
    b=(build_dgs_elmgenstat_voltage_source_block(100.,25.,10.,0.) if voltage_source
       else build_dgs_elmgenstat_block(100.,25.))
    apply_genstat_voltage_protection(b,.2,.3,.1)
    from VeraGridEngine.Simulations.Rms.problems.rms_problem_dae import RmsProblemDae
    layout=FunctionalRuntimeProblem(b,Var('time'))
    problem=RmsProblemDae.__new__(RmsProblemDae)
    problem.sys_block=b
    problem._glob_time=layout.glob_time
    problem._uid2idx_vars=layout.uid2idx_vars
    problem._uid2idx_event_params=layout.uid2idx_event_params
    problem._uid2idx_params={}
    problem._parameters_values=[]
    problem._variable_parameters=list(b.mode_dict)
    problem._procedural_expression_compiler=None
    x=np.zeros(len(problem.uid2idx_vars));params=np.zeros(len(problem.uid2idx_event_params))
    for logic in b.procedural_logic:logic.bind(problem,expression_mode=mode)
    # Recovery must remain above .3 for .1 s; interrupted recovery restarts timing.
    for time,voltage,blocked in [(0.,1.,0.),(.1,.1,1.),(.2,.25,1.),(.3,.4,1.),
                                 (.35,.25,1.),(.4,.4,1.),(.49,.4,1.),(.501,.4,0.),(.6,.1,1.)]:
        x[problem.uid2idx_vars[b.in_vars[0].uid]]=voltage
        for logic in b.procedural_logic:logic.update(time,x,params)
        assert params[b.procedural_logic[1].output_idx]==blocked
    # Blocked current and power equations must impose zero, not disappear.
    values={v.uid:0. for v in [*b.in_vars,*b.out_vars]}
    values.update({v.uid:params[index] for v,index in [(v,problem.uid2idx_event_params[v.uid]) for v in b.mode_dict]})
    for index in [0,1,6,7]:assert b.algebraic_eqs[index].eval_uid(values)==0.


def test_native_protected_exports_preserve_parameters_and_assign_templates():
    import json,hashlib
    from pathlib import Path
    from VeraGridEngine.IO.dgs.dgs_circuit import DgsCircuit
    from VeraGridEngine.IO.dgs.dgs_to_veragrid import dgs_to_circuit
    from VeraGridEngine.enumerations import DynamicSimulationMode
    folder=Path(__file__).resolve().parents[2]/'data/grids/DGS/native_genstat_protection_pf2024'
    for record in json.loads((folder/'manifest.json').read_text())['files']:
        path=folder/record['file']
        assert hashlib.sha256(path.read_bytes()).hexdigest()==record['sha256']
        circuit=DgsCircuit();circuit.parse_dgs(str(path));source=circuit.elmgenstats[0]
        assert source.uk==pytest.approx(10.) and source.Pcu==0.
        assert source.uonthr==pytest.approx(.3) and source.Tondelay==pytest.approx(.1)
        grid=dgs_to_circuit(str(path),use_dynamic_information=True,dynamic_simulation_mode=DynamicSimulationMode.RMS)
        assert len(grid.static_generators)==37
        for device in grid.static_generators:
            assert device.active and device.rms_template is not None
            assert len(device.rms_template.block.procedural_logic)==(2 if source.umin else 0)


def test_protection_persists_and_clones_with_canonical_mode_uids():
    from tests.symbolic_block_roundtrip import roundtrip_block
    b=build_dgs_elmgenstat_voltage_source_block(100.,25.,10.,0.)
    apply_genstat_voltage_protection(b,.2,.3,.1)
    from VeraGridEngine.Utils.procedural_logic import ProceduralLogicCodec
    restored=roundtrip_block(b, procedural_logic_codec=ProceduralLogicCodec())
    assert len(restored.procedural_logic)==2
    assert {logic.output_var_uid for logic in restored.procedural_logic}=={v.uid for v in restored.mode_dict}


@pytest.mark.parametrize('model',[1,2])
def test_blocking_and_restart_agree_with_native_fault_trace(model):
    import json
    from pathlib import Path
    from VeraGridEngine.Simulations.Rms.problems.rms_problem_dae import RmsProblemDae
    folder=Path(__file__).resolve().parents[2]/'data/grids/DGS/native_genstat_protection_pf2024'
    native=json.loads((folder/'dynamic_reference.json').read_text())[str(model)]
    assert native['load_flow_code']==native['initialization_code']==native['simulation_code']==0
    block=(build_dgs_elmgenstat_block(100.,25.) if model==1
           else build_dgs_elmgenstat_voltage_source_block(100.,25.,10.,0.))
    apply_genstat_voltage_protection(block,.2,.3,.1)
    layout=FunctionalRuntimeProblem(block,Var('time'))
    problem=RmsProblemDae.__new__(RmsProblemDae)
    problem.sys_block=block;problem._glob_time=layout.glob_time
    problem._uid2idx_vars=layout.uid2idx_vars;problem._uid2idx_event_params=layout.uid2idx_event_params
    problem._uid2idx_params={};problem._parameters_values=[];problem._variable_parameters=list(block.mode_dict)
    problem._procedural_expression_compiler=None
    for logic in block.procedural_logic:logic.bind(problem)
    x=np.zeros(len(problem.uid2idx_vars));parameters=np.zeros(len(problem.uid2idx_event_params))
    disagreements=[]
    for time,power,reactive,voltage,current in native['samples']:
        x[problem.uid2idx_vars[block.in_vars[0].uid]]=voltage
        for logic in block.procedural_logic:logic.update(time,x,parameters)
        blocked=parameters[block.procedural_logic[1].output_idx]>.5
        expected_blocked=current<1e-8
        if blocked!=expected_blocked:disagreements.append(time)
    # PF and sampled procedural event localization may differ by one 1 ms step.
    assert all(min(abs(t-edge) for edge in [.05,.1,.15,.17,.27])<=.001 for t in disagreements)
    assert parameters[block.procedural_logic[1].output_idx]==0.


def test_controlled_voltage_source_selects_voltage_commands_for_static_host():
    from VeraGridEngine.IO.dgs.dgs_circuit import DgsCircuit
    from VeraGridEngine.IO.dgs.dgs_objects import ElmGenstat
    from VeraGridEngine.IO.dgs.dgs_to_blocks import ElmCompInstanceEntry
    from VeraGridEngine.IO.dgs.dynamic_models.dgs_native_model_workflow import (
        NativeDgsEquipmentPlan, NativeDgsEquipmentKind, construct_native_dgs_equipment)
    from VeraGridEngine.Devices.Injections.static_generator import StaticGenerator
    circuit=DgsCircuit();source=ElmGenstat()
    source.ID='native';source.sgn=25.;source.iSimModel=2;source.uk=10.;source.Pcu=0.
    source.umin=.2;source.uonthr=.3;source.Tondelay=.1;circuit.elmgenstats.append(source)
    entry=ElmCompInstanceEntry('slot','equipment','native','source','ElmGenstat',0,None,None,
                              connected_inputs=['u1r_in','u1i_in'])
    plan=NativeDgsEquipmentPlan(NativeDgsEquipmentKind.StaticGenerator,entry)
    block=construct_native_dgs_equipment(plan,StaticGenerator(),circuit,100.,50.)
    assert [v.name for v in block.in_vars]==['Vm','Va','u1r_in','u1i_in']
    assert len(block.procedural_logic)==2
