# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Phase-selective EMT templates for shunt R/L/C devices."""

from typing import Dict, List, Tuple

from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Utils.Symbolic.block import Expr, Var
from VeraGridEngine.enumerations import DeviceType, ParamPowerFlowRefferenceType, VarPowerFlowRefferenceType


def _get_active_phases(phA: bool, phB: bool, phC: bool) -> List[str]:
    """Return the enabled phase labels in strict A-B-C order.

    :param phA: True when phase A is active.
    :param phB: True when phase B is active.
    :param phC: True when phase C is active.
    :return: Ordered list with the active phase labels.
    :raises ValueError: If no phase is enabled.
    """
    # The EMT assembler expects deterministic ordering because all variable,
    # equation, and mapping indices are consumed positionally downstream.
    active_phases: List[str] = list()

    if phA:
        active_phases.append("A")
    else:
        active_phases = active_phases

    if phB:
        active_phases.append("B")
    else:
        active_phases = active_phases

    if phC:
        active_phases.append("C")
    else:
        active_phases = active_phases

    # An empty phase set cannot be assembled into a coherent EMT block because
    # there would be no unknowns or equations to bind to a bus.
    if len(active_phases) == 0:
        raise ValueError("At least one phase must be enabled for an EMT shunt template")
    else:
        return active_phases


def _get_phase_count_name(base_name: str, phase_count: int, requested_name: str | None) -> str:
    """Resolve a template name whose suffix matches the active phase count.

    :param base_name: Base prefix without the phase-count suffix.
    :param phase_count: Number of active phases.
    :param requested_name: Optional caller-provided name.
    :return: Name with a ``1ph``, ``2ph`` or ``3ph`` suffix.
    """
    # The template name is part of the broader EMT workflow because it feeds the
    # generated symbolic variable names and device-level metadata.
    suffix: str = f"_{phase_count}ph"

    if requested_name is None:
        resolved_name: str = base_name + suffix
    else:
        resolved_name = requested_name

        if resolved_name.endswith("_1ph"):
            resolved_name = resolved_name[:-4] + suffix
        else:
            if resolved_name.endswith("_2ph"):
                resolved_name = resolved_name[:-4] + suffix
            else:
                if resolved_name.endswith("_3ph"):
                    resolved_name = resolved_name[:-4] + suffix
                else:
                    resolved_name = resolved_name + suffix

    return resolved_name


def _get_voltage_reference(phase_label: str) -> VarPowerFlowRefferenceType:
    """Return the EMT voltage reference enum for one phase.

    :param phase_label: Phase label ``A``, ``B`` or ``C``.
    :return: Matching external voltage reference enum.
    """
    if phase_label == "A":
        reference: VarPowerFlowRefferenceType = VarPowerFlowRefferenceType.v_A
    else:
        if phase_label == "B":
            reference = VarPowerFlowRefferenceType.v_B
        else:
            if phase_label == "C":
                reference = VarPowerFlowRefferenceType.v_C
            else:
                raise ValueError(f"Unsupported phase label '{phase_label}'")

    return reference


def _get_current_reference(phase_label: str) -> VarPowerFlowRefferenceType:
    """Return the EMT injected-current reference enum for one phase.

    :param phase_label: Phase label ``A``, ``B`` or ``C``.
    :return: Matching external current reference enum.
    """
    if phase_label == "A":
        reference: VarPowerFlowRefferenceType = VarPowerFlowRefferenceType.i_A
    else:
        if phase_label == "B":
            reference = VarPowerFlowRefferenceType.i_B
        else:
            if phase_label == "C":
                reference = VarPowerFlowRefferenceType.i_C
            else:
                raise ValueError(f"Unsupported phase label '{phase_label}'")

    return reference


def _get_pl0_reference(phase_label: str) -> ParamPowerFlowRefferenceType:
    """Return the active-power parameter reference for one phase.

    :param phase_label: Phase label ``A``, ``B`` or ``C``.
    :return: Matching API parameter enum.
    """
    if phase_label == "A":
        reference: ParamPowerFlowRefferenceType = ParamPowerFlowRefferenceType.Pl0_A
    else:
        if phase_label == "B":
            reference = ParamPowerFlowRefferenceType.Pl0_B
        else:
            if phase_label == "C":
                reference = ParamPowerFlowRefferenceType.Pl0_C
            else:
                raise ValueError(f"Unsupported phase label '{phase_label}'")

    return reference


def _get_ql0_reference(phase_label: str) -> ParamPowerFlowRefferenceType:
    """Return the reactive-power parameter reference for one phase.

    :param phase_label: Phase label ``A``, ``B`` or ``C``.
    :return: Matching API parameter enum.
    """
    if phase_label == "A":
        reference: ParamPowerFlowRefferenceType = ParamPowerFlowRefferenceType.Ql0_A
    else:
        if phase_label == "B":
            reference = ParamPowerFlowRefferenceType.Ql0_B
        else:
            if phase_label == "C":
                reference = ParamPowerFlowRefferenceType.Ql0_C
            else:
                raise ValueError(f"Unsupported phase label '{phase_label}'")

    return reference


def _build_external_mapping(
    voltage_vars: Dict[str, Var],
    current_vars: Dict[str, Var],
) -> Dict[VarPowerFlowRefferenceType, Var | None]:
    """Build a full external mapping with inactive phases set to ``None``.

    :param voltage_vars: Active terminal voltages keyed by phase label.
    :param current_vars: Active injected currents keyed by phase label.
    :return: Full EMT external mapping for the shunt template.
    """
    # The EMT connection workflow uses a fixed enum contract, so inactive phases
    # must still appear explicitly with ``None`` entries.
    mapping: Dict[VarPowerFlowRefferenceType, Var | None] = dict({
        VarPowerFlowRefferenceType.v_N: None,
        VarPowerFlowRefferenceType.v_A: voltage_vars.get("A", None),
        VarPowerFlowRefferenceType.v_B: voltage_vars.get("B", None),
        VarPowerFlowRefferenceType.v_C: voltage_vars.get("C", None),
        VarPowerFlowRefferenceType.P: None,
        VarPowerFlowRefferenceType.Q: None,
        VarPowerFlowRefferenceType.P_N: None,
        VarPowerFlowRefferenceType.Q_N: None,
        VarPowerFlowRefferenceType.P_A: None,
        VarPowerFlowRefferenceType.Q_A: None,
        VarPowerFlowRefferenceType.P_B: None,
        VarPowerFlowRefferenceType.Q_B: None,
        VarPowerFlowRefferenceType.P_C: None,
        VarPowerFlowRefferenceType.Q_C: None,
        VarPowerFlowRefferenceType.i_N: None,
        VarPowerFlowRefferenceType.i_A: current_vars.get("A", None),
        VarPowerFlowRefferenceType.i_B: current_vars.get("B", None),
        VarPowerFlowRefferenceType.i_C: current_vars.get("C", None),
        VarPowerFlowRefferenceType.phi_v: None,
        VarPowerFlowRefferenceType.phi: None,
        VarPowerFlowRefferenceType.Vpk: None,
        VarPowerFlowRefferenceType.Ipk: None,
        VarPowerFlowRefferenceType.d_v_N: None,
        VarPowerFlowRefferenceType.d_v_A: None,
        VarPowerFlowRefferenceType.d_v_B: None,
        VarPowerFlowRefferenceType.d_v_C: None,
    })

    return mapping


def _build_resistor_api_mapping(pl0_vars: Dict[str, Var]) -> Dict[ParamPowerFlowRefferenceType, Var | None]:
    """Build the API mapping for an EMT shunt resistor.

    :param pl0_vars: Active per-phase active-power variables.
    :return: API mapping dictionary.
    """
    # Only active phases publish parameter variables so the generated metadata
    # remains dimensionally aligned with the equations created above.
    mapping: Dict[ParamPowerFlowRefferenceType, Var | None] = dict({
        ParamPowerFlowRefferenceType.omega_base: None,
        ParamPowerFlowRefferenceType.Pl0_A: pl0_vars.get("A", None),
        ParamPowerFlowRefferenceType.Pl0_B: pl0_vars.get("B", None),
        ParamPowerFlowRefferenceType.Pl0_C: pl0_vars.get("C", None),
        ParamPowerFlowRefferenceType.Ql0_A: None,
        ParamPowerFlowRefferenceType.Ql0_B: None,
        ParamPowerFlowRefferenceType.Ql0_C: None,
    })

    return mapping


def _build_reactive_api_mapping(
    omega_base_var: Var,
    ql0_vars: Dict[str, Var],
) -> Dict[ParamPowerFlowRefferenceType, Var | None]:
    """Build the API mapping for an EMT shunt inductor or capacitor.

    :param omega_base_var: Shared base-frequency variable.
    :param ql0_vars: Active per-phase reactive-power variables.
    :return: API mapping dictionary.
    """
    # The EMT initializer writes base frequency and per-phase reactive power into
    # these enum slots before the symbolic expressions are evaluated.
    mapping: Dict[ParamPowerFlowRefferenceType, Var | None] = dict({
        ParamPowerFlowRefferenceType.omega_base: omega_base_var,
        ParamPowerFlowRefferenceType.Pl0_A: None,
        ParamPowerFlowRefferenceType.Pl0_B: None,
        ParamPowerFlowRefferenceType.Pl0_C: None,
        ParamPowerFlowRefferenceType.Ql0_A: ql0_vars.get("A", None),
        ParamPowerFlowRefferenceType.Ql0_B: ql0_vars.get("B", None),
        ParamPowerFlowRefferenceType.Ql0_C: ql0_vars.get("C", None),
    })

    return mapping


def get_shunt_r_emt_template(
    vf: VarFactory,
    phA: bool = True,
    phB: bool = True,
    phC: bool = True,
    name: str = "R_shunt",
) -> EmtModelTemplate:
    """Build a phase-selective shunt resistor EMT template.

    :param vf: EMT variable factory.
    :param phA: Bool. True if the load has phase A, else False.
    :param phB: Bool. True if the load has phase B, else False.
    :param phC: Bool. True if the load has phase C, else False.
    :param name: Optional symbolic model name.
    :return: EMT shunt resistor template sized to the active phases.
    """
    # The template must derive every symbolic structure from the active phase set
    # so EmtProblem can remain unchanged and consume a coherent block directly.
    active_phases: List[str] = _get_active_phases(phA=phA, phB=phB, phC=phC)
    phase_count: int = len(active_phases)
    resolved_name: str = _get_phase_count_name("Shunt_R", phase_count, name)
    if name == "R_shunt":
        event_name: str = _get_phase_count_name("Shunt_R", phase_count, None)
    else:
        event_name = resolved_name

    templ: EmtModelTemplate = EmtModelTemplate()
    templ.tpe = DeviceType.LoadDevice
    templ.name = resolved_name
    templ.block.name = resolved_name

    # Create only the active terminal voltage variables because inactive phases
    # must not produce extra equations or unused symbolic dimensions.
    in_vars: List[Var] = list()
    voltage_vars: Dict[str, Var] = dict()
    resistance_vars: Dict[str, Var] = dict()
    pl0_vars: Dict[str, Var] = dict()
    current_vars: Dict[str, Var] = dict()
    algebraic_eqs: List[Expr] = list()

    # The nominal voltage is shared across the active phases exactly as in the
    # previous 3-phase model, so the balanced 3-phase case keeps the same form.
    vnom_var: Var = vf.add_var("Vnom_" + event_name)
    templ.block.event_dict[vnom_var] = vf.add_const(1.0)

    for phase_label in active_phases:
        # Each active phase gets its own voltage input and electrical parameters.
        voltage_var: Var = vf.add_var(
            name=f"v_{phase_label}_{resolved_name}",
            reference=_get_voltage_reference(phase_label),
        )
        in_vars.append(voltage_var)
        voltage_vars[phase_label] = voltage_var

        resistance_var: Var = vf.add_var(f"R_{phase_label}_{event_name}")
        templ.block.event_dict[resistance_var] = vf.add_const(None)
        resistance_vars[phase_label] = resistance_var

        pl0_var: Var = vf.add_var(f"Pl0_{phase_label}_{resolved_name}")
        templ.block.parameters[pl0_var] = vf.add_const(None)
        pl0_vars[phase_label] = pl0_var

        # The event dictionary holds the algebraic resistance definition so EMT
        # events can still alter the effective resistor without core changes.
        templ.block.event_dict[resistance_var] = vnom_var ** 2 / pl0_var

        current_var: Var = vf.add_var(
            name=f"i_{phase_label}_{resolved_name}",
            reference=_get_current_reference(phase_label),
        )
        current_vars[phase_label] = current_var
        algebraic_eqs.append(current_var + voltage_var / resistance_var)

    # Publish the size-consistent symbolic structures in active-phase order.
    algebraic_vars: List[Var] = list(current_vars[phase_label] for phase_label in active_phases)
    templ.block.in_vars = in_vars
    templ.block.algebraic_vars = algebraic_vars
    templ.block.algebraic_eqs = algebraic_eqs
    templ.block.out_vars = list(current_vars[phase_label] for phase_label in active_phases)
    templ.block.external_mapping = _build_external_mapping(voltage_vars=voltage_vars, current_vars=current_vars)
    templ.block.api_obj_mapping = _build_resistor_api_mapping(pl0_vars=pl0_vars)

    return templ


def get_shunt_l_emt_template(
    vf: VarFactory,
    phA: bool,
    phB: bool,
    phC: bool,
    name: str = "L_shunt",
) -> EmtModelTemplate:
    """Build a phase-selective shunt inductor EMT template.

    :param vf: EMT variable factory.
    :param phA: True when phase A is active.
    :param phB: True when phase B is active.
    :param phC: True when phase C is active.
    :param name: Optional symbolic model name.
    :return: Configured inductor EMT template.
    """
    # The inductor state dimension must follow the filtered phase list so the
    # derivative vectors assembled by the solver stay compact and ordered.
    active_phases: List[str] = _get_active_phases(phA=phA, phB=phB, phC=phC)
    phase_count: int = len(active_phases)
    resolved_name: str = _get_phase_count_name("Shunt_L", phase_count, name)

    templ: EmtModelTemplate = EmtModelTemplate()
    templ.tpe = DeviceType.LoadDevice
    templ.name = resolved_name
    templ.block.name = resolved_name

    in_vars: List[Var] = list()
    state_vars: List[Var] = list()
    diff_vars: List[Var] = list()
    state_eqs: List[Expr] = list()
    voltage_vars: Dict[str, Var] = dict()
    current_vars: Dict[str, Var] = dict()
    inductance_vars: Dict[str, Var] = dict()
    ql0_vars: Dict[str, Var] = dict()

    # The base-frequency and nominal-voltage variables remain shared scalars,
    # matching the previous template contract seen by the EMT initializer.
    omega_base_var: Var = vf.add_var("w_base_" + resolved_name)
    vnom_var: Var = vf.add_var("Vnom_" + resolved_name)
    templ.block.event_dict[vnom_var] = vf.add_const(1.0)

    for phase_label in active_phases:
        # Each active phase gets one terminal input, one current state, and one
        # inductance computed from the same API-level reactive-power contract.
        voltage_var: Var = vf.add_var(
            name=f"v_{phase_label}_{resolved_name}",
            reference=_get_voltage_reference(phase_label),
        )
        in_vars.append(voltage_var)
        voltage_vars[phase_label] = voltage_var

        inductance_var: Var = vf.add_var(f"L_{phase_label}_{resolved_name}")
        inductance_vars[phase_label] = inductance_var

        ql0_var: Var = vf.add_var(f"Ql0_{phase_label}_{resolved_name}")
        ql0_vars[phase_label] = ql0_var
        templ.block.event_dict[inductance_var] = vnom_var ** 2 / (ql0_var * omega_base_var)

        current_var: Var = vf.add_var(f"i_{phase_label}_{resolved_name}")
        current_vars[phase_label] = current_var
        state_vars.append(current_var)

        diff_var: Var = vf.add_diff_var(name=f"d_i_{phase_label}_{resolved_name}", base_var=current_var)
        diff_vars.append(diff_var)
        templ.block.diff_init_eqs[diff_var] = vf.add_const(0.0)

        # The differential law is unchanged per phase; only the number and order
        # of replicated phase equations now depend on the active phase mask.
        state_eqs.append(-voltage_var / inductance_var)

    templ.block.in_vars = in_vars
    templ.block.state_vars = state_vars
    templ.block.diff_vars = diff_vars
    templ.block.state_eqs = state_eqs
    templ.block.out_vars = list(current_vars[phase_label] for phase_label in active_phases)
    templ.block.external_mapping = _build_external_mapping(voltage_vars=voltage_vars, current_vars=current_vars)
    templ.block.api_obj_mapping = _build_reactive_api_mapping(omega_base_var=omega_base_var, ql0_vars=ql0_vars)

    return templ


def get_shunt_c_emt_template(
    vf: VarFactory,
    phA: bool,
    phB: bool,
    phC: bool,
    name: str = "C_shunt",
) -> EmtModelTemplate:
    """Build a phase-selective shunt capacitor EMT template.

    :param vf: EMT variable factory.
    :param phA: True when phase A is active.
    :param phB: True when phase B is active.
    :param phC: True when phase C is active.
    :param name: Optional symbolic model name.
    :return: Configured capacitor EMT template.
    """
    # The capacitor uses one state per active phase and two algebraic equations
    # per phase, so all lists must be sized from the same ordered phase subset.
    active_phases: List[str] = _get_active_phases(phA=phA, phB=phB, phC=phC)
    phase_count: int = len(active_phases)
    resolved_name: str = _get_phase_count_name("Shunt_C", phase_count, name)

    templ: EmtModelTemplate = EmtModelTemplate()
    templ.tpe = DeviceType.LoadDevice
    templ.name = resolved_name
    templ.block.name = resolved_name

    in_vars: List[Var] = list()
    state_vars: List[Var] = list()
    diff_vars: List[Var] = list()
    algebraic_vars: List[Var] = list()
    algebraic_eqs: List[Expr] = list()
    voltage_vars: Dict[str, Var] = dict()
    current_vars: Dict[str, Var] = dict()
    capacitance_vars: Dict[str, Var] = dict()
    ql0_vars: Dict[str, Var] = dict()

    # The shared scalar parameters keep the same EMT API contract while the
    # replicated state and algebraic structures shrink with the phase mask.
    omega_base_var: Var = vf.add_var("w_base_" + resolved_name)
    vnom_var: Var = vf.add_var("Vnom_" + resolved_name)
    templ.block.event_dict[vnom_var] = vf.add_const(1.0)

    for phase_label in active_phases:
        # Each active phase gets one bus voltage input, one capacitor voltage
        # state, one state derivative, and one injected current algebraic output.
        voltage_var: Var = vf.add_var(
            name=f"v_{phase_label}_{resolved_name}",
            reference=_get_voltage_reference(phase_label),
        )
        in_vars.append(voltage_var)
        voltage_vars[phase_label] = voltage_var

        capacitance_var: Var = vf.add_var(f"C_{phase_label}_{resolved_name}")
        capacitance_vars[phase_label] = capacitance_var

        ql0_var: Var = vf.add_var(f"Ql0_{phase_label}_{resolved_name}")
        ql0_vars[phase_label] = ql0_var
        templ.block.event_dict[capacitance_var] = ql0_var / (vnom_var ** 2 * omega_base_var)

        current_var: Var = vf.add_var(f"i_{phase_label}_{resolved_name}")
        current_vars[phase_label] = current_var
        algebraic_vars.append(current_var)

        capacitor_voltage_var: Var = vf.add_var(f"vCap{phase_label}_{resolved_name}")
        state_vars.append(capacitor_voltage_var)

        capacitor_voltage_diff_var: Var = vf.add_diff_var(
            name=f"dvCap{phase_label}_{resolved_name}",
            base_var=capacitor_voltage_var,
        )
        diff_vars.append(capacitor_voltage_diff_var)
        templ.block.diff_init_eqs[capacitor_voltage_diff_var] = vf.add_const(0.0)

        # The algebraic closure remains identical to the existing model: bind the
        # capacitor state to the bus voltage and derive current from dv/dt.
        algebraic_eqs.append(capacitor_voltage_var - voltage_var)
        algebraic_eqs.append(current_var + capacitance_var * capacitor_voltage_diff_var)

    templ.block.in_vars = in_vars
    templ.block.state_vars = state_vars
    templ.block.diff_vars = diff_vars
    templ.block.algebraic_vars = algebraic_vars
    templ.block.algebraic_eqs = algebraic_eqs
    templ.block.out_vars = list(current_vars[phase_label] for phase_label in active_phases)
    templ.block.external_mapping = _build_external_mapping(voltage_vars=voltage_vars, current_vars=current_vars)
    templ.block.api_obj_mapping = _build_reactive_api_mapping(omega_base_var=omega_base_var, ql0_vars=ql0_vars)

    return templ
