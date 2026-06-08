# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from typing import Dict, List

import numpy as np

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Simulations.EMT.problems.emt_problem_template import EmtProblemTemplate
from VeraGridEngine.Templates.Emt.vsc_gfm_emt import get_gfm_emt_template
from VeraGridEngine.Utils.Symbolic.block import find_name_in_block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Var
from VeraGridEngine.enumerations import DeviceType, VarPowerFlowReferenceType


class GenericEmtProblem(EmtProblemTemplate):
    """
    Minimal EMT problem used by the GFM-EMT structural test
    """

    __slots__ = []


def _build_pf_consistent_bindings(name: str) -> Dict[str, float]:
    """
    Build a self-consistent steady-state operating point at ``t = 0``.

    The phase quantities are reconstructed from a positive-sequence
    operating point (peak phasors), so the EMT init equations and the
    instantaneous P / Q formulas match by construction.

    :param name: Suffix used by the template.
    :return: Mapping ``variable_name -> value`` covering every variable
        referenced by the init / algebraic / state equations.
    """
    omega_base: float = 2.0 * np.pi * 50.0
    R_s: float = 0.01
    X_s: float = 0.1
    Kdp: float = 0.05
    Kdq: float = 0.05
    tau_omega: float = 0.05
    tau_v: float = 0.05

    # Positive-sequence PF references that the EMT bridge populates and
    # that drive every init expression in the model.
    Vpk: float = np.sqrt(2.0) * 1.0
    Ipk: float = np.sqrt(2.0) * 0.4
    phi_v: float = 0.0
    phi: float = 0.0
    v_dc: float = 2.0

    two_pi_over_3: float = 2.0 * np.pi / 3.0

    # Per-phase samples at t = 0 from the model's analytical sin-conv
    # formulas: v(t) = Vpk*sin(omega*t + phi_v), i(t) = Ipk*sin(omega*t
    # + phi_v + phi). ``phi`` is the bridge convention phi_I - phi_V so
    # that ``I_branch_phasor = conj(S/V)``.
    theta_i: float = phi_v + phi
    v_A: float = Vpk * np.sin(phi_v)
    v_B: float = Vpk * np.sin(phi_v - two_pi_over_3)
    v_C: float = Vpk * np.sin(phi_v + two_pi_over_3)
    i_A: float = Ipk * np.sin(theta_i)
    i_B: float = Ipk * np.sin(theta_i - two_pi_over_3)
    i_C: float = Ipk * np.sin(theta_i + two_pi_over_3)

    # Internal EMF computed analytically from the PF-positive-sequence
    # phasor relation ``E = V - Z * I_branch``.
    V_re: float = Vpk * np.cos(phi_v)
    V_im: float = Vpk * np.sin(phi_v)
    I_re: float = Ipk * np.cos(theta_i)
    I_im: float = Ipk * np.sin(theta_i)
    ZI_re: float = R_s * I_re - X_s * I_im
    ZI_im: float = R_s * I_im + X_s * I_re
    E_re: float = V_re - ZI_re
    E_im: float = V_im - ZI_im
    Epk_init: float = float(np.sqrt(E_re * E_re + E_im * E_im))
    theta: float = float(np.arctan2(E_im, E_re))
    e_A: float = Epk_init * np.sin(theta)
    e_B: float = Epk_init * np.sin(theta - two_pi_over_3)
    e_C: float = Epk_init * np.sin(theta + two_pi_over_3)

    # Average 3-ph active / reactive power for balanced sinusoidal
    # steady state. Signs match the runtime ``Pe_expr`` and ``Qe_expr``:
    # ``Pe = -(3/2)·Vpk·Ipk·cos(phi)`` and ``Qe = +(3/2)·Vpk·Ipk·sin(phi)``.
    Pe: float = -1.5 * Vpk * Ipk * np.cos(phi)
    Qe: float = 1.5 * Vpk * Ipk * np.sin(phi)

    return {
        f"v_A_{name}": v_A,
        f"v_B_{name}": v_B,
        f"v_C_{name}": v_C,
        f"v_dc_{name}": v_dc,
        f"i_A_{name}": i_A,
        f"i_B_{name}": i_B,
        f"i_C_{name}": i_C,
        f"theta_{name}": theta,
        f"e_A_{name}": e_A,
        f"e_B_{name}": e_B,
        f"e_C_{name}": e_C,
        f"Pe_{name}": Pe,
        f"Qe_{name}": Qe,
        f"i_dc_{name}": -Pe / v_dc,
        f"omega_{name}": 1.0,
        f"Epk_{name}": Epk_init,
        f"omega_base_{name}": omega_base,
        f"R_s_{name}": R_s,
        f"X_s_{name}": X_s,
        f"Kdp_{name}": Kdp,
        f"Kdq_{name}": Kdq,
        f"tau_omega_{name}": tau_omega,
        f"tau_v_{name}": tau_v,
        f"omega_ref_{name}": 1.0,
        f"Qf_{name}": 0.0,
        f"Vpk_ref_{name}": Vpk,
        f"phi_v_ref_{name}": phi_v,
        f"Ipk_ref_{name}": Ipk,
        f"phi_ref_{name}": phi,
        f"P_ref_{name}": Pe,
        f"Q_ref_{name}": Qe,
        f"V_ref_{name}": Epk_init,
    }


def test_vsc_gfm_emt_template_exposes_expected_structure() -> None:
    """
    Build the EMT GFM template and check the structural surface a VSC
    device needs to consume (DeviceType, in / out vars, named states,
    algebraic vars).

    :return: None.
    """
    vf: VarFactory = VarFactory()
    templ = get_gfm_emt_template(vf=vf, name="G1")

    assert templ.tpe == DeviceType.VscDevice
    assert [var.name for var in templ.block.in_vars] == [
        "v_A_G1",
        "v_B_G1",
        "v_C_G1",
        "v_dc_G1",
    ]
    assert [var.name for var in templ.block.out_vars] == [
        "i_A_G1",
        "i_B_G1",
        "i_C_G1",
        "i_dc_G1",
    ]
    assert [var.name for var in templ.block.state_vars] == [
        "i_A_G1",
        "i_B_G1",
        "i_C_G1",
        "theta_G1",
        "omega_G1",
        "Epk_G1",
    ]
    expected_algebraic: List[str] = [
        "e_A_G1",
        "e_B_G1",
        "e_C_G1",
        "Pe_G1",
        "Qe_G1",
        "i_dc_G1",
    ]
    assert [var.name for var in templ.block.algebraic_vars] == expected_algebraic

    for net_var in ["v_A_G1", "v_B_G1", "v_C_G1", "i_A_G1", "i_B_G1", "i_C_G1", "v_dc_G1"]:
        assert find_name_in_block(net_var, templ.block) is not None

    assert templ.block.external_mapping[VarPowerFlowReferenceType.Vdc].name == "v_dc_G1"
    assert templ.block.external_mapping[VarPowerFlowReferenceType.Qf].name == "Qf_G1"


def test_vsc_gfm_emt_template_can_be_loaded_into_generic_problem() -> None:
    """
    Verify the template plugs into the generic EMT problem template
    without errors and exposes the expected runtime parameters.

    :return: None.
    """
    vf: VarFactory = VarFactory()
    templ = get_gfm_emt_template(vf=vf, name="VSC")
    static_parameter_values_mapping: Dict[Var, Const] = dict()
    problem = GenericEmtProblem(
        sys_block=templ.block,
        glob_time=vf.add_var("t_gfm_emt_case"),
        static_parameter_values_mapping=static_parameter_values_mapping,
    )
    runtime_parameter_names = [var.name for var in problem.get_variable_parameters()]

    for expected in ["omega_base_VSC", "R_s_VSC", "X_s_VSC", "Kdp_VSC", "Kdq_VSC"]:
        assert expected in runtime_parameter_names


def test_vsc_gfm_emt_template_init_residual_is_small() -> None:
    """
    Substitute a PF-consistent steady-state operating point into every
    variable of the template and check that the residual of every
    algebraic equation is essentially zero.

    :return: None.
    """
    vf: VarFactory = VarFactory()
    templ = get_gfm_emt_template(vf=vf, name="G1")
    bindings: Dict[str, float] = _build_pf_consistent_bindings(name="G1")

    for idx, eq in enumerate(templ.block.algebraic_eqs):
        residual: float = float(eq.eval(**bindings))
        assert abs(residual) < 1.0e-9, (
            f"algebraic_eq[{idx}] residual {residual:.3e} too large at the PF init point"
        )

    for var, init_expr in templ.block.init_eqs.items():
        init_value: float = float(init_expr.eval(**bindings))
        binding_value: float = bindings[var.name]
        assert abs(init_value - binding_value) < 1.0e-9, (
            f"init_eqs[{var.name}] gives {init_value:.6e} but binding is {binding_value:.6e}"
        )

    d_theta_var = next(v for v in templ.block.diff_vars if v.name == "d_theta_G1")
    omega_base_val: float = bindings["omega_base_G1"]
    assert abs(float(templ.block.diff_init_eqs[d_theta_var].eval(**bindings)) - omega_base_val) < 1.0e-9
