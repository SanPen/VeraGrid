# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
import math
import numpy as np
from typing import Dict, List, Set, Tuple, TypeVar
from VeraGridEngine.enumerations import (
    ExternalGridMode,
    SwitchGraphicType,
    TapChangerTypes,
    TapModuleControl,
    WindingType,
    ShuntControlMode,
    ConverterControlType,
    ConverterFaultControlType,
    GeneratorType
)
import VeraGridEngine.Devices as dev
from VeraGridEngine.Devices.Branches.wire import Wire
from VeraGridEngine.Devices.Branches.overhead_line_type import OverheadLineType, WireInTower
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.dgs.dgs_circuit import DgsCircuit
from VeraGridEngine.IO.dgs.dgs_objects import *

TDgsObject = TypeVar("TDgsObject")


def _is_element_closed_by_cubicle_switches(
    element_id: str,
    cubics_by_objid: Dict[str, List[StaCubic]],
    switch_by_cubic_id: Dict[str, StaSwitch],
) -> bool:
    cbs = cubics_by_objid.get(_ref_id(element_id), [])
    if not cbs:
        return True  # no cubicles found -> keep legacy behavior
    found_switch = False
    for cb in cbs:
        cb_id = _ref_id(cb.ID)
        if not cb_id:
            continue
        sw = switch_by_cubic_id.get(cb_id)
        if sw is None:
            continue
        found_switch = True
        if int(sw.on_off) == 0:
            return False
    # if no StaSwitch rows for those cubicles, keep backward-compatible behavior
    return True if not found_switch else True


def _get_tr3_winding_closed_states(
    tr3_id: str,
    cubics_by_objid: Dict[str, List[StaCubic]],
    switch_by_cubic_id: Dict[str, StaSwitch],
    bus_by_term_id: Dict[str, dev.Bus],
    bus_hv: dev.Bus,
    bus_mv: dev.Bus,
    bus_lv: dev.Bus,
) -> tuple[bool, bool, bool]:
    hv_closed = True
    mv_closed = True
    lv_closed = True
    for cb in cubics_by_objid.get(_ref_id(tr3_id), []):
        cb_id = _ref_id(cb.ID)
        term_id = _ref_id(cb.fold_id)
        if not cb_id or not term_id:
            continue
        sw = switch_by_cubic_id.get(cb_id)
        if sw is None:
            continue  # no StaSwitch => keep default True
        is_closed = int(sw.on_off) != 0
        bus = bus_by_term_id.get(term_id)
        if bus is bus_hv:
            hv_closed = hv_closed and is_closed
        elif bus is bus_mv:
            mv_closed = mv_closed and is_closed
        elif bus is bus_lv:
            lv_closed = lv_closed and is_closed
    return hv_closed, mv_closed, lv_closed


def _ref_id(x: str | None) -> str | None:
    """
    Extract the referenced object ID from PowerFactory/DGS pointer strings.
    DGS pointers may contain a path separated by backslashes. We keep only the last token.
    """
    if x is None:
        return None
    s = str(x)
    if "\\" in s:
        return s.split("\\")[-1]
    else:
        return s


def _stacubic_obj_bus_sort_key(cubic: StaCubic) -> int:
    """Return StaCubic ``obj_bus`` as integer sort key."""
    return int(cubic.obj_bus)


def _bus_vnom_sort_key(bus: dev.Bus) -> float:
    """Return bus nominal voltage sort key."""
    return float(bus.Vnom)


def _resolve_pointer_dict_value(key: str | None, mapping: Dict[str, TDgsObject]) -> TDgsObject | None:
    """Resolve a DGS pointer key using both raw and normalized forms."""
    if key is None:
        return None
    value = mapping.get(key, None)
    if value is not None:
        return value
    normalized_key = _ref_id(key)
    if normalized_key is not None:
        return mapping.get(normalized_key, None)
    else:
        return None


def _get_non_empty_name(name: str | None, default_value: str) -> str:
    """Return a non-empty name string."""
    if name is not None and str(name).strip() != "":
        return str(name)
    else:
        return default_value


def _get_parallel_device_count(count: int) -> int:
    """
    Return the number of explicit VeraGrid devices to create.

    :param count: DGS parallel-unit count
    :return: Number of explicit devices to instantiate
    """
    if count > 1:
        return int(count)
    else:
        return 1


def _get_parallel_device_name(base_name: str, parallel_index: int, parallel_count: int) -> str:
    """
    Build the explicit device name for a parallel-unit copy.

    :param base_name: Base DGS device name
    :param parallel_index: Zero-based copy index
    :param parallel_count: Total number of parallel copies
    :return: Explicit device name
    """
    if parallel_count <= 1:
        return base_name
    else:
        return f"{base_name} ({parallel_index + 1})"


def _get_parallel_device_idtag(base_id: str | None, parallel_index: int, parallel_count: int) -> str | None:
    """
    Build the explicit idtag for a parallel-unit copy.

    :param base_id: Base DGS identifier
    :param parallel_index: Zero-based copy index
    :param parallel_count: Total number of parallel copies
    :return: Explicit idtag or ``None``
    """
    if base_id is None or base_id == "":
        return None
    else:
        if parallel_count <= 1:
            return base_id
        else:
            return f"{base_id}:{parallel_index + 1}"


def _get_transformer_tap_changer_type(typtr2: TypTr2) -> TapChangerTypes:
    """Infer the VeraGrid tap-changer type from PowerFactory magnitude and phase data."""
    if int(typtr2.itapch) == 0:
        return TapChangerTypes.NoRegulation
    else:
        pass

    phase_deg = float(typtr2.phitr)
    phase_mod = math.fmod(abs(phase_deg), 180.0)
    if abs(phase_mod) < 1e-9:
        return TapChangerTypes.VoltageRegulation
    else:
        if abs(phase_mod - 90.0) < 1e-6:
            return TapChangerTypes.Asymmetrical
        else:
            return TapChangerTypes.Symmetrical


def _get_safe_tap_value(value: float, fallback_value: float) -> float:
    """
    Return a strictly positive finite tap value.

    VeraGrid branch tap modules cannot be zero or negative because they are
    used in denominators during branch admittance assembly.

    :param value: Candidate imported tap value
    :param fallback_value: Safe fallback value from the discrete tap changer
    :return: Positive finite tap value
    """
    minimum_positive_value: float = 1e-6
    fallback: float = float(fallback_value)
    if not math.isfinite(fallback) or fallback <= 0.0:
        fallback = 1.0
    else:
        pass

    candidate: float = float(value)
    if not math.isfinite(candidate):
        return fallback
    else:
        pass

    if candidate <= 0.0:
        return fallback
    else:
        pass

    if candidate < minimum_positive_value:
        return minimum_positive_value
    else:
        return candidate


def _sanitize_tap_window(
        tap_value: float,
        tap_min_value: float,
        tap_max_value: float,
        fallback_tap_value: float,
        fallback_tap_min_value: float,
        fallback_tap_max_value: float,
) -> Tuple[float, float, float]:
    """
    Normalize a tap module and its range into a valid positive interval.

    :param tap_value: Imported current tap module
    :param tap_min_value: Imported minimum tap module
    :param tap_max_value: Imported maximum tap module
    :param fallback_tap_value: Fallback current tap module from the tap changer
    :param fallback_tap_min_value: Fallback minimum tap module from the tap changer
    :param fallback_tap_max_value: Fallback maximum tap module from the tap changer
    :return: Sanitized current, minimum and maximum tap modules
    """
    safe_tap_min: float = _get_safe_tap_value(tap_min_value, fallback_tap_min_value)
    safe_tap_max: float = _get_safe_tap_value(tap_max_value, fallback_tap_max_value)

    if safe_tap_min > safe_tap_max:
        original_minimum: float = safe_tap_min
        safe_tap_min = safe_tap_max
        safe_tap_max = original_minimum
    else:
        pass

    safe_tap: float = _get_safe_tap_value(tap_value, fallback_tap_value)
    if safe_tap < safe_tap_min:
        safe_tap = safe_tap_min
    else:
        pass

    if safe_tap > safe_tap_max:
        safe_tap = safe_tap_max
    else:
        pass

    return safe_tap, safe_tap_min, safe_tap_max


def _apply_branch_tap_state(
        branch: dev.Transformer2W,
        tap_value: float,
        tap_phase: float,
        tap_min_value: float,
        tap_max_value: float,
        tap_phase_min: float,
        tap_phase_max: float,
) -> None:
    """
    Apply a full tap state to a VeraGrid transformer-like branch.

    :param branch: Target transformer or winding
    :param tap_value: Current tap module
    :param tap_phase: Current tap phase
    :param tap_min_value: Minimum tap module
    :param tap_max_value: Maximum tap module
    :param tap_phase_min: Minimum tap phase
    :param tap_phase_max: Maximum tap phase
    :return: None
    """
    branch.tap_module = float(tap_value)
    branch.tap_phase = float(tap_phase)
    branch.tap_module_min = float(tap_min_value)
    branch.tap_module_max = float(tap_max_value)
    branch.tap_phase_min = float(tap_phase_min)
    branch.tap_phase_max = float(tap_phase_max)


def _get_switch_impedance_in_pu(r_ohm: float, x_ohm: float, vnom_kv: float, sbase_mva: float) -> Tuple[float, float]:
    """Convert switch impedance from ohms to per-unit."""
    if vnom_kv <= 0.0 or sbase_mva <= 0.0:
        return 1e-20, 1e-20
    else:
        pass

    zbase_ohm = (vnom_kv * vnom_kv) / sbase_mva
    if zbase_ohm <= 0.0:
        return 1e-20, 1e-20
    else:
        pass

    r_pu = float(r_ohm) / zbase_ohm
    x_pu = float(x_ohm) / zbase_ohm

    return r_pu, x_pu


def _line_section_index_sort_key(section: ElmLnesec) -> float:
    """Return the section ordering index as float."""
    return float(section.index)


def _get_unique_name_mapping(lines: List[ElmLne], use_characteristic_name: bool) -> Dict[str, str]:
    """Build a line-name mapping only for names that are unique in the DGS."""
    counts: Dict[str, int] = dict()
    values: Dict[str, str] = dict()
    for line in lines:
        if use_characteristic_name:
            name = str(line.chr_name)
        else:
            name = str(line.loc_name)
        if name == "":
            continue
        counts[name] = counts.get(name, 0) + 1
        values[name] = _ref_id(line.ID) or line.ID

    mapping: Dict[str, str] = dict()
    for name, count in counts.items():
        if count == 1:
            mapping[name] = values[name]
        else:
            pass
    return mapping


def _resolve_line_section_owner_id(section: ElmLnesec,
                                   line_ids: Set[str],
                                   folder_parent: Dict[str, str],
                                   line_id_by_loc_name: Dict[str, str],
                                   line_id_by_chr_name: Dict[str, str]) -> str:
    """Resolve the owning line of a section using folder ancestry and unique-name fallback."""
    current = _ref_id(section.fold_id) or str(section.fold_id)
    if current != "":
        for _ in range(25):
            if current in line_ids:
                return current
            parent_ptr = folder_parent.get(current, "")
            if parent_ptr == "":
                break
            current = _ref_id(parent_ptr) or parent_ptr
    else:
        pass

    if section.loc_name != "":
        owner_line_id = line_id_by_loc_name.get(section.loc_name, "")
        if owner_line_id != "":
            return owner_line_id
        else:
            pass
    else:
        pass

    if section.chr_name != "":
        return line_id_by_chr_name.get(section.chr_name, "")
    else:
        return ""


def get_terminal_ids(element_id: str, cubics_by_objid: Dict[str, List[StaCubic]]) -> List[str]:
    """
    Get the connected terminal IDs (ElmTerm.ID) for a given branch/injection element ID
    using the StaCubic.fold_id -> ElmTerm.ID mapping.
    """
    cbs: List[StaCubic] = list()
    cbs_raw: List[StaCubic] = cubics_by_objid.get(_ref_id(element_id), list())
    for cubic in cbs_raw:
        fold_id = _ref_id(cubic.fold_id)
        if fold_id is not None and fold_id != "":
            cbs.append(cubic)
        else:
            pass

    if len(cbs) == 2:
        cbs = sorted(cbs, key=_stacubic_obj_bus_sort_key)
    else:
        pass

    terminal_ids: List[str] = list()
    for cubic in cbs:
        fold_id = _ref_id(cubic.fold_id)
        if fold_id is not None and fold_id != "":
            terminal_ids.append(fold_id)
        else:
            pass

    return terminal_ids


def get_branch_buses(elm_id: str,
                     stacubic_dict: Dict[str, List[int]],
                     buses: List[dev.Bus],
                     cubics_by_objid: Dict[str, List[StaCubic]],
                     bus_by_term_id: Dict[str, dev.Bus]) -> Tuple[dev.Bus, dev.Bus]:
    """
    Function to get the buses from a branch element
    :param elm_id:
    :param stacubic_dict:
    :param buses:
    :param cubics_by_objid:
    :param bus_by_term_id:
    :return:
    """
    # Prefer robust mapping using StaCubic.fold_id -> ElmTerm.ID -> Bus
    term_ids = get_terminal_ids(element_id=elm_id, cubics_by_objid=cubics_by_objid)
    if len(term_ids) == 2:
        return bus_by_term_id[term_ids[0]], bus_by_term_id[term_ids[1]]

    # Legacy fallback (index-based), kept for backward compatibility
    elm_id_ref = _ref_id(elm_id)
    bus_ids = stacubic_dict.get(elm_id_ref, None)
    if bus_ids is None:
        raise ValueError(f"No buses for the line {elm_id}")

    if len(bus_ids) != 2:
        raise ValueError(f"Not exactly 2 buses for the line {elm_id}")

    bus_from = buses[bus_ids[0]]
    bus_to = buses[bus_ids[1]]

    return bus_from, bus_to


def get_injection_bus(elm_id: str,
                      stacubic_dict: Dict[str, List[int]],
                      buses: List[dev.Bus],
                      cubics_by_objid: Dict[str, List[StaCubic]],
                      bus_by_term_id: Dict[str, dev.Bus]) -> dev.Bus:
    """
    Function to get the bus from a injection element
    :param elm_id:
    :param stacubic_dict:
    :param buses:
    :param cubics_by_objid:
    :param bus_by_term_id:
    :return:
    """
    # Prefer robust mapping using StaCubic.fold_id -> ElmTerm.ID -> Bus
    term_ids = get_terminal_ids(element_id=elm_id, cubics_by_objid=cubics_by_objid)
    if len(term_ids) == 1:
        return bus_by_term_id[term_ids[0]]

    # Legacy fallback (index-based), kept for backward compatibility
    elm_id_ref = _ref_id(elm_id)
    bus_ids = stacubic_dict.get(elm_id_ref, None)
    if bus_ids is None or len(bus_ids) == 0:
        raise ValueError(f"No buses for the element {elm_id}")

    if len(bus_ids) != 1:
        raise ValueError(f"Not exactly 1 bus for the element {elm_id}")

    return buses[bus_ids[0]]


def convert_dgs_to_bus(elmterm: ElmTerm,
                       pos_by_objid: Dict[str, Tuple[float, float]]) -> dev.Bus:
    """
    Convert ElmTerm to Bus
    :param elmterm: ElmTerm
    :param pos_by_objid: dictionary of graphical positions
    :return: Bus
    """
    tid = _ref_id(elmterm.ID)
    x, y = pos_by_objid.get(tid, (0.0, 0.0))
    bus = dev.Bus(
        name=elmterm.loc_name or f"Bus_{tid}",
        Vnom=float(elmterm.uknom),
        vmin=0.9,
        vmax=1.1,
        xpos=float(x) * 5,
        ypos=float(-y) * 5,
        active=(int(elmterm.outserv or 0) == 0),
    )

    if float(elmterm.vtarget) > 0.0:
        bus.Vm0 = float(elmterm.vtarget)
    else:
        pass

    return bus


def convert_dgs_to_sequence_line(typlne: TypLne) -> dev.SequenceLineType:
    """
    Convert a TypLne to SequenceLineType
    :param typlne: TypLne
    :return: SequenceLineType
    """
    elm = dev.SequenceLineType(
        name=typlne.loc_name,
        R=typlne.rline,
        X=typlne.xline,
        B=typlne.bline,
        CnF=typlne.cline * 1000,
        R0=typlne.rline0,
        X0=typlne.xline0,
        B0=typlne.bline0,
        CnF0=typlne.cline0 * 1000,
        Vnom=typlne.uline,
        Imax=typlne.sline,
        use_conductance=typlne.cline != 0.0
    )

    return elm


def _bundle_offsets(n_sub: int, spacing_m: float) -> List[Tuple[float, float]]:
    """Generate bundle offsets (dx, dy) in meters for a bundle of subconductors.

    The arrangement is assumed to be evenly spaced on a circle, such that the
    distance between adjacent subconductors is approximately ``spacing_m``.

    Notes
    -----
    - This is a geometric approximation used when PowerFactory provides only
      ``ncsub`` (number of subconductors) and ``dsubc`` (bundle spacing).
    - If ``n_sub <= 1`` or ``spacing_m <= 0``, a single conductor at (0, 0) is returned.
    """
    if n_sub <= 1:
        default_offsets: List[Tuple[float, float]] = list()
        default_offsets.append((0.0, 0.0))
        return default_offsets
    else:
        pass
    if spacing_m <= 0.0:
        default_offsets = list()
        default_offsets.append((0.0, 0.0))
        return default_offsets
    else:
        pass

    # Radius of the circumcircle for a regular n-gon with side length = spacing.
    # r = s / (2*sin(pi/n))
    radius = spacing_m / (2.0 * math.sin(math.pi / float(n_sub)))

    offsets: List[Tuple[float, float]] = list()
    for k in range(n_sub):
        ang = 2.0 * math.pi * float(k) / float(n_sub)
        dx = radius * math.cos(ang)
        dy = radius * math.sin(ang)
        offsets.append((dx, dy))

    return offsets


def convert_dgs_to_wire(typcon: TypCon) -> Wire:
    """Convert a PowerFactory TypCon into a VeraGrid Wire."""
    tid = _ref_id(typcon.ID)
    if typcon.loc_name is not None and str(typcon.loc_name).strip() != "":
        name = typcon.loc_name
    else:
        name = f"Wire_{tid}"

    # PowerFactory: diatub may be 0/empty for non-tubular conductors.
    diatub = float(typcon.diatub)

    # Conductor Model (Solid or Tubular)
    if typcon.iModel == 1:
        is_tube = True
    else:
        is_tube = False

    # Keep a compact but informative stranding label.
    stranding = f"ncsub={int(typcon.ncsub)}, dsubc={float(typcon.dsubc)}"

    wire = Wire(
        name=name,
        idtag=tid,
        r=float(typcon.rpha),
        max_current=float(typcon.sline),
        stranding=stranding,
        material=str(typcon.mlei),
        diameter=float(typcon.diaco),
        diameter_internal=diatub,
        is_tube=is_tube,
        code=str(typcon.loc_name),
    )

    return wire


def _convert_gearth_us_per_cm_to_resistivity_ohm_m(gearth_us_per_cm: float) -> float:
    """Convert PowerFactory earth conductivity (uS/cm) to resistivity (Ohm*m)."""
    # uS/cm -> S/m: 1 uS = 1e-6 S; 1/cm = 100/m
    conductivity_s_per_m = float(gearth_us_per_cm) * 1e-4
    if conductivity_s_per_m <= 0.0:
        return 100.0
    return 1.0 / conductivity_s_per_m


def convert_dgs_to_overhead_line_type(
        typtow: TypTow,
        typcon_by_id: Dict[str, TypCon],
        wire_by_id: Dict[str, Wire],
        default_frequency_hz: float,
) -> OverheadLineType:
    """Convert a PowerFactory TypTow into a VeraGrid OverheadLineType.

    This conversion builds the wire geometry (positions) and assigns Wire templates.
    It supports multi-circuit towers by defining phases 1..3 for circuit 1,
    4..6 for circuit 2, etc (as required by VeraGrid's OverheadLineType).
    """
    tid = _ref_id(typtow.ID)
    if typtow.loc_name is not None and str(typtow.loc_name).strip() != "":
        name = typtow.loc_name
    else:
        name = f"Tower_{tid}"

    # Frequency / earth parameters
    if typtow.frnom is not None and float(typtow.frnom) > 0.0:
        freq = float(typtow.frnom)
    else:
        freq = float(default_frequency_hz)
    earth_res = _convert_gearth_us_per_cm_to_resistivity_ohm_m(float(typtow.gearth))

    # Determine nominal voltage from referenced conductor types.
    v_candidates: List[float] = list()
    for ptr in typtow.pcond_c:
        if ptr is None:
            continue
        cid = _ref_id(ptr)
        tc = typcon_by_id.get(cid)
        if tc is not None:
            v_candidates.append(float(tc.uline))
    for ptr in typtow.pcond_e:
        if ptr is None:
            continue
        cid = _ref_id(ptr)
        tc = typcon_by_id.get(cid)
        if tc is not None:
            v_candidates.append(float(tc.uline))

    if len(v_candidates) > 0:
        vnom = max(v_candidates)
    else:
        vnom = 0.0

    ohl_type = OverheadLineType(
        name=name,
        idtag=tid,
        Vnom=vnom,
        earth_resistivity=earth_res,
        frequency=freq,
    )

    # Earth wires (phase 0)
    for ew_idx, ptr in enumerate(typtow.pcond_e):
        if ptr is None:
            continue
        cid = _ref_id(ptr)
        wire = wire_by_id.get(cid)
        tc = typcon_by_id.get(cid)
        if wire is None or tc is None:
            continue
        if ew_idx < len(typtow.xy_e) and len(typtow.xy_e[ew_idx]) >= 2:
            x0 = float(typtow.xy_e[ew_idx][0])
            y0 = float(typtow.xy_e[ew_idx][1])
        else:
            x0 = 0.0
            y0 = 0.0

        offsets = _bundle_offsets(n_sub=int(tc.ncsub), spacing_m=float(tc.dsubc))
        for dx, dy in offsets:
            ohl_type.wires_in_tower.append(WireInTower(wire=wire, xpos=x0 + dx, ypos=y0 + dy, phase=0))

    # Phase wires per circuit
    # Expected xy_c row format: [xA, xB, xC, yA, yB, yC]
    for c_idx, ptr in enumerate(typtow.pcond_c):
        if ptr is None:
            continue
        cid = _ref_id(ptr)
        wire = wire_by_id.get(cid)
        tc = typcon_by_id.get(cid)
        if wire is None or tc is None:
            continue

        if c_idx < len(typtow.xy_c) and len(typtow.xy_c[c_idx]) >= 6:
            row = typtow.xy_c[c_idx]
            xA, xB, xC = float(row[0]), float(row[1]), float(row[2])
            yA, yB, yC = float(row[3]), float(row[4]), float(row[5])
        else:
            xA, xB, xC = 0.0, 0.0, 0.0
            yA, yB, yC = 0.0, 0.0, 0.0

        offsets = _bundle_offsets(n_sub=int(tc.ncsub), spacing_m=float(tc.dsubc))

        base_phase = 3 * int(c_idx)  # circuit 0 -> 0, circuit 1 -> 3, ...
        for dx, dy in offsets:
            ohl_type.wires_in_tower.append(WireInTower(wire=wire, xpos=xA + dx, ypos=yA + dy, phase=base_phase + 1))
            ohl_type.wires_in_tower.append(WireInTower(wire=wire, xpos=xB + dx, ypos=yB + dy, phase=base_phase + 2))
            ohl_type.wires_in_tower.append(WireInTower(wire=wire, xpos=xC + dx, ypos=yC + dy, phase=base_phase + 3))

    return ohl_type


def _convert_pf_tr2_connection(code: str) -> WindingType | None:
    """
    Convert a PowerFactory 2-character transformer connection code to VeraGrid WindingType.
    If the code is unknown, return None and let defaults apply.
    """
    if code is None:
        return None

    c = str(code).strip().upper()
    if c == "":
        return None

    # Common PowerFactory 2-char winding codes in DGS: Y, YN, D, Z, ZN
    conversion_dict: Dict[str, WindingType] = {
        "D": WindingType.Delta,
        "Y": WindingType.NeutralStar,
        "YN": WindingType.GroundedStar,
        "Z": WindingType.ZigZag,
        "ZN": WindingType.ZigZag,
    }

    if c in conversion_dict:
        return conversion_dict[c]
    elif c.startswith("Y"):
        # Defensive fallback: any "Y*" treated as star (prefer grounded if it contains N)
        if "N" in c:
            return WindingType.GroundedStar
        return WindingType.NeutralStar
    else:
        return None


def convert_dgs_to_transformer_type(typtr2: TypTr2) -> dev.TransformerType:
    """
    Convert a TypTr2 to TransformerType
    :param typtr2: TypTr2
    :return: TransformerType
    """
    tpe = dev.TransformerType(hv_nominal_voltage=float(typtr2.utrn_h),
                              lv_nominal_voltage=float(typtr2.utrn_l),
                              nominal_power=float(typtr2.strn),
                              copper_losses=float(typtr2.pcutr),
                              iron_losses=float(typtr2.pfe),
                              no_load_current=float(typtr2.curmg),
                              short_circuit_voltage=float(typtr2.uktr),
                              gr_hv1=0.5,
                              gx_hv1=0.5,
                              total_positions=max(1, int(typtr2.ntpmx) - int(typtr2.ntpmn) + 1),
                              neutral_position=max(0, int(typtr2.nntap0) - int(typtr2.ntpmn)),
                              dV=float(typtr2.dutap) / 100.0,
                              asymmetry_angle=float(typtr2.phitr),
                              tc_type=_get_transformer_tap_changer_type(typtr2=typtr2),
                              name=typtr2.loc_name)

    conn_hv = _convert_pf_tr2_connection(typtr2.tr2cn_h)
    conn_lv = _convert_pf_tr2_connection(typtr2.tr2cn_l)

    if conn_hv is not None:
        tpe.conn_hv = conn_hv

    if conn_lv is not None:
        tpe.conn_lv = conn_lv
    else:
        pass

    vector_group_number = int(round(float(typtr2.nt2ag))) % 12
    tpe.vector_group_number = vector_group_number

    return tpe


def _order_hv_lv(bus_a: dev.Bus, bus_b: dev.Bus, logger: Logger, tr_name: str) -> Tuple[dev.Bus, dev.Bus]:
    """
    Order two buses as (HV, LV) based on nominal voltage.
    If voltages are equal or undefined, keep the original order and warn.
    """
    va = float(bus_a.Vnom)
    vb = float(bus_b.Vnom)

    if va == 0.0 or vb == 0.0:
        logger.add_warning(f"Transformer '{tr_name}': one or both buses have Vnom=0.0 (va={va}, vb={vb}).")
        return bus_a, bus_b

    if va > vb:
        return bus_a, bus_b
    if vb > va:
        return bus_b, bus_a

    # Equal-Vnom transformers: HV/LV is ambiguous.
    # Use deterministic lexical ordering by bus name to keep import orientation stable.
    name_a: str = str(bus_a.name or "").strip()
    name_b: str = str(bus_b.name or "").strip()

    if name_a != "" and name_b != "":
        if name_a <= name_b:
            logger.add_warning(
                f"Transformer '{tr_name}': HV/LV ambiguous (equal Vnom={va}). Ordered lexically by bus name."
            )
            return bus_a, bus_b
        else:
            logger.add_warning(
                f"Transformer '{tr_name}': HV/LV ambiguous (equal Vnom={va}). Ordered lexically by bus name."
            )
            return bus_b, bus_a
    else:
        pass

    logger.add_warning(f"Transformer '{tr_name}': HV/LV ambiguous (equal Vnom={va}). Keeping original order.")
    return bus_a, bus_b


def _order_hv_mv_lv(bus_a: dev.Bus, bus_b: dev.Bus, bus_c: dev.Bus, logger: Logger, tr_name: str) -> Tuple[
    dev.Bus, dev.Bus, dev.Bus]:
    """
    Order three buses as (HV, MV, LV) based on nominal voltage.
    If voltages are equal or undefined, keep a stable order and warn.
    """
    va = float(bus_a.Vnom)
    vb = float(bus_b.Vnom)
    vc = float(bus_c.Vnom)

    if va == 0.0 or vb == 0.0 or vc == 0.0:

        logger.add_warning(
            f"one or more buses have Vnom=0.0",
            device=tr_name,
            device_class="Transformer3W",
            value=f"(va={va}, vb={vb}, vc={vc})"
        )

        return bus_a, bus_b, bus_c

    buses: List[dev.Bus] = list()
    buses.append(bus_a)
    buses.append(bus_b)
    buses.append(bus_c)
    buses_sorted: List[dev.Bus] = sorted(buses, key=_bus_vnom_sort_key, reverse=True)

    v0 = float(buses_sorted[0].Vnom)
    v1 = float(buses_sorted[1].Vnom)
    v2 = float(buses_sorted[2].Vnom)

    if v0 == v1 or v1 == v2:
        logger.add_warning(
            f"HV/MV/LV ambiguous, keeping Vnom-based ordering ",
            device=tr_name,
            device_class="Transformer3W",
            value=f"(va={va}, vb={vb}, vc={vc})"
        )

    return buses_sorted[0], buses_sorted[1], buses_sorted[2]


def _apply_tr3_winding_connection_data(
        winding: dev.Winding,
        pf_connection_code: str,
        pf_vector_group_angle: float,
) -> None:
    """Apply PowerFactory 3W winding connection data to an inner VeraGrid winding."""
    external_connection = _convert_pf_tr2_connection(code=pf_connection_code)
    if external_connection is not None:
        winding.conn_f = WindingType.GroundedStar
        winding.conn_t = external_connection
    else:
        pass

    winding.vector_group_number = int(round(float(pf_vector_group_angle))) % 12


def _apply_tr3_winding_tap_data(
        winding: dev.Winding,
        current_position: int,
        neutral_position: int,
        minimum_position: int,
        maximum_position: int,
        step_percent: float,
        phase_angle_deg: float,
) -> None:
    """Apply PowerFactory 3W tap data to an internal VeraGrid winding."""
    total_positions = int(maximum_position) - int(minimum_position) + 1
    if total_positions <= 0:
        return
    else:
        pass

    tc_type = TapChangerTypes.VoltageRegulation
    if abs(float(phase_angle_deg)) > 1e-12:
        tc_type = TapChangerTypes.Symmetrical
        if abs(abs(float(phase_angle_deg)) % 180.0 - 90.0) < 1e-6:
            tc_type = TapChangerTypes.Asymmetrical
        else:
            pass
    else:
        pass

    winding.tap_changer.total_positions = int(total_positions)
    winding.tap_changer.neutral_position = max(0, int(neutral_position) - int(minimum_position))
    winding.tap_changer.dV = float(step_percent) / 100.0
    winding.tap_changer.asymmetry_angle = float(phase_angle_deg)
    winding.tap_changer.tc_type = tc_type

    tap_position = int(current_position) - int(minimum_position)
    if tap_position < 0:
        tap_position = 0
    else:
        pass
    if tap_position >= winding.tap_changer.total_positions:
        tap_position = winding.tap_changer.total_positions - 1
    else:
        pass
    winding.tap_changer.tap_position = tap_position

    fallback_tap: float = winding.tap_changer.get_tap_module()
    fallback_tap_min: float = winding.tap_changer.get_tap_module_min()
    fallback_tap_max: float = winding.tap_changer.get_tap_module_max()

    if tc_type == TapChangerTypes.VoltageRegulation:
        step = float(step_percent) / 100.0
        tap = 1.0 + (int(current_position) - int(neutral_position)) * step
        tap_min = 1.0 + (int(minimum_position) - int(neutral_position)) * step
        tap_max = 1.0 + (int(maximum_position) - int(neutral_position)) * step

        tap, tap_min, tap_max = _sanitize_tap_window(
            tap_value=tap,
            tap_min_value=tap_min,
            tap_max_value=tap_max,
            fallback_tap_value=fallback_tap,
            fallback_tap_min_value=fallback_tap_min,
            fallback_tap_max_value=fallback_tap_max,
        )

        _apply_branch_tap_state(
            branch=winding,
            tap_value=tap,
            tap_phase=0.0,
            tap_min_value=tap_min,
            tap_max_value=tap_max,
            tap_phase_min=0.0,
            tap_phase_max=0.0,
        )
    else:
        tap_value, tap_min_value, tap_max_value = _sanitize_tap_window(
            tap_value=fallback_tap,
            tap_min_value=fallback_tap_min,
            tap_max_value=fallback_tap_max,
            fallback_tap_value=fallback_tap,
            fallback_tap_min_value=fallback_tap_min,
            fallback_tap_max_value=fallback_tap_max,
        )

        _apply_branch_tap_state(
            branch=winding,
            tap_value=tap_value,
            tap_phase=winding.tap_changer.get_tap_phase(),
            tap_min_value=tap_min_value,
            tap_max_value=tap_max_value,
            tap_phase_min=winding.tap_changer.get_tap_phase_min(),
            tap_phase_max=winding.tap_changer.get_tap_phase_max(),
        )


def convert_dgs_to_transformer(tr2: ElmTr2,
                               buses: List[dev.Bus],
                               stacubic_dict: Dict[str, List[int]],
                               templates_dict: Dict[str, dev.TransformerType],
                               typtr2_dict: Dict[str, TypTr2],
                               freq: float,
                               baseMVA: float,
                               logger: Logger,
                               cubics_by_objid: Dict[str, List[StaCubic]],
                               bus_by_term_id: Dict[str, dev.Bus],
                               switch_by_cubic_id: Dict[str, StaSwitch],
                               parallel_index: int = 0,
                               parallel_count: int = 1) -> dev.Transformer2W:
    """
    Convert ElmTr2 to Transformer2W
    :param tr2: ElmTr2
    :param buses:
    :param stacubic_dict:
    :param templates_dict:
    :param typtr2_dict: Dictionary of TypTr2 objects indexed by ID (raw PF data)
    :param freq:
    :param baseMVA:
    :param logger:
    :param cubics_by_objid:
    :param bus_by_term_id:
    :return: Transformer2W
    """
    template = templates_dict.get(tr2.typ_id, None)
    if template is None:
        template = templates_dict.get(_ref_id(tr2.typ_id), None)

    if template is None:
        raise ValueError(f"No template for the transformer {tr2.ID}")

    # Resolve the raw TypTr2 (needed to parse tap settings: step/min/max/neutral)
    typtr2_raw = _resolve_pointer_dict_value(key=tr2.typ_id, mapping=typtr2_dict)
    if typtr2_raw is None:
        raise ValueError(f"No raw TypTr2 data for the transformer {tr2.ID}")
    else:
        pass

    # Check connectivity through robust StaCubic.fold_id mapping first (preferred)
    term_ids = get_terminal_ids(element_id=tr2.ID, cubics_by_objid=cubics_by_objid)
    if len(term_ids) != 2:
        # Fall back to legacy check only if terminal mapping is not available
        bus_ids = stacubic_dict.get(_ref_id(tr2.ID), None)
        if bus_ids is None:
            raise ValueError(f"No buses for the transformer {tr2.ID}")

        if len(bus_ids) != 2:
            raise ValueError(f"Not exactly 2 buses for the transformer {tr2.ID}")

    bus_from, bus_to = get_branch_buses(elm_id=tr2.ID,
                                        stacubic_dict=stacubic_dict,
                                        buses=buses,
                                        cubics_by_objid=cubics_by_objid,
                                        bus_by_term_id=bus_by_term_id)

    cbs = cubics_by_objid.get(_ref_id(tr2.ID), [])
    has_dgs_from_to = (len(cbs) == 2) and ({int(cb.obj_bus) for cb in cbs} == {0, 1})

    if has_dgs_from_to:
        bus_vg_from, bus_vg_to = bus_from, bus_to
    else:
        bus_vg_from, bus_vg_to = _order_hv_lv(bus_a=bus_from, bus_b=bus_to, logger=logger, tr_name=tr2.loc_name)

    transformer_name = _get_non_empty_name(tr2.loc_name, f"Transformer_{_ref_id(tr2.ID)}")
    transformer_name = _get_parallel_device_name(transformer_name, parallel_index, parallel_count)
    transformer_idtag = _get_parallel_device_idtag(_ref_id(tr2.ID), parallel_index, parallel_count)

    trafo = dev.Transformer2W(bus_from=bus_vg_from,
                              bus_to=bus_vg_to,
                              name=transformer_name,
                              idtag=transformer_idtag,
                              active=not tr2.outserv and _is_element_closed_by_cubicle_switches(element_id=tr2.ID,
                                                                                                  cubics_by_objid=cubics_by_objid,
                                                                                                  switch_by_cubic_id=switch_by_cubic_id),)

    trafo.apply_template(obj=template, Sbase=baseMVA, logger=logger)
    trafo.vector_group_number = int(round(float(typtr2_raw.nt2ag))) % 12
    trafo.rate = float(trafo.rate) * float(tr2.ratfac)

    #   - TypTr2.dutap   : tap step in percent (%)
    #   - TypTr2.nntap0  : neutral position (integer)
    #   - TypTr2.ntpmn   : minimum position (integer)
    #   - TypTr2.ntpmx   : maximum position (integer)
    #   - TypTr2.tap_side: side where the tap-changer is located (typically 0=HV, 1=LV)
    #   - ElmTr2.nntap   : current position (integer)

    if int(typtr2_raw.itapch) != 0 and trafo.tap_changer.total_positions > 0:
        tap_position = int(tr2.nntap) - int(typtr2_raw.ntpmn)
        if tap_position < 0:
            tap_position = 0
        else:
            pass
        if tap_position >= trafo.tap_changer.total_positions:
            tap_position = trafo.tap_changer.total_positions - 1
        else:
            pass

        trafo.tap_changer.tap_position = tap_position

        fallback_tap: float = trafo.tap_changer.get_tap_module()
        fallback_tap_min: float = trafo.tap_changer.get_tap_module_min()
        fallback_tap_max: float = trafo.tap_changer.get_tap_module_max()

        tc_type = _get_transformer_tap_changer_type(typtr2=typtr2_raw)
        if tc_type == TapChangerTypes.VoltageRegulation:
            step: float = float(typtr2_raw.dutap) / 100.0
            neutral_position: int = int(typtr2_raw.nntap0)
            current_position: int = int(tr2.nntap)

            tap: float = 1.0 + (current_position - neutral_position) * step
            tap_min: float = 1.0 + (int(typtr2_raw.ntpmn) - neutral_position) * step
            tap_max: float = 1.0 + (int(typtr2_raw.ntpmx) - neutral_position) * step

            if tap_min > tap_max:
                old_tap_min = tap_min
                tap_min = tap_max
                tap_max = old_tap_min
            else:
                pass

            hv_bus: dev.Bus
            lv_bus: dev.Bus
            if float(bus_vg_from.Vnom) >= float(bus_vg_to.Vnom):
                hv_bus = bus_vg_from
                lv_bus = bus_vg_to
            else:
                hv_bus = bus_vg_to
                lv_bus = bus_vg_from

            if int(typtr2_raw.tap_side) == 0:
                tap_on_bus = hv_bus
            else:
                tap_on_bus = lv_bus

            if tap_on_bus is not bus_vg_from:
                tap = 1.0 / tap
                tap_min_inverted = 1.0 / tap_min
                tap_max_inverted = 1.0 / tap_max
                tap_min = min(tap_min_inverted, tap_max_inverted)
                tap_max = max(tap_min_inverted, tap_max_inverted)
            else:
                pass

            tap, tap_min, tap_max = _sanitize_tap_window(
                tap_value=tap,
                tap_min_value=tap_min,
                tap_max_value=tap_max,
                fallback_tap_value=fallback_tap,
                fallback_tap_min_value=fallback_tap_min,
                fallback_tap_max_value=fallback_tap_max,
            )

            _apply_branch_tap_state(
                branch=trafo,
                tap_value=tap,
                tap_phase=0.0,
                tap_min_value=tap_min,
                tap_max_value=tap_max,
                tap_phase_min=0.0,
                tap_phase_max=0.0,
            )
        else:
            tap_value, tap_min_value, tap_max_value = _sanitize_tap_window(
                tap_value=fallback_tap,
                tap_min_value=fallback_tap_min,
                tap_max_value=fallback_tap_max,
                fallback_tap_value=fallback_tap,
                fallback_tap_min_value=fallback_tap_min,
                fallback_tap_max_value=fallback_tap_max,
            )

            _apply_branch_tap_state(
                branch=trafo,
                tap_value=tap_value,
                tap_phase=trafo.tap_changer.get_tap_phase(),
                tap_min_value=tap_min_value,
                tap_max_value=tap_max_value,
                tap_phase_min=trafo.tap_changer.get_tap_phase_min(),
                tap_phase_max=trafo.tap_changer.get_tap_phase_max(),
            )
    else:
        pass

    if int(tr2.ntrcn) != 0:
        trafo.tap_module_control_mode = TapModuleControl.Vm
        if float(tr2.usetp) > 0.0:
            trafo.vset = float(tr2.usetp)
        else:
            pass
    else:
        pass

    if float(typtr2_raw.uk0tr) > 0.0:
        nominal_power = float(typtr2_raw.strn)
        if nominal_power > 0.0:
            z0_pu = (float(typtr2_raw.uk0tr) / 100.0) * (float(baseMVA) / nominal_power)
            r0_pu = (float(typtr2_raw.ur0tr) / 100.0) * (float(baseMVA) / nominal_power)
            x0_sq = max(0.0, z0_pu * z0_pu - r0_pu * r0_pu)
            trafo.R0 = r0_pu
            trafo.X0 = math.sqrt(x0_sq)
        else:
            pass
    else:
        pass

    trafo.R2 = trafo.R
    trafo.X2 = trafo.X
    # ---------------------------------------------------------------

    trafo.fix_inconsistencies(logger=logger, maximum_difference=0.1)

    return trafo


def convert_dgs_to_transformer3w(tr3: ElmTr3,
                                 buses: List[dev.Bus],
                                 stacubic_dict: Dict[str, List[int]],
                                 templates_dict: Dict[str, TypTr3],
                                 baseMVA: float,
                                 logger: Logger,
                                 cubics_by_objid: Dict[str, List[StaCubic]],
                                 bus_by_term_id: Dict[str, dev.Bus],
                                 switch_by_cubic_id: Dict[str, StaSwitch],
                                 parallel_index: int = 0,
                                 parallel_count: int = 1) -> dev.Transformer3W:
    """
    Convert ElmTr3 to Transformer3W using TypTr3 as template for design values.
    """
    template = _resolve_pointer_dict_value(key=tr3.typ_id, mapping=templates_dict)
    if template is None:
        raise ValueError(f"No TypTr3 data for transformer {tr3.ID}")
    else:
        pass

    # Check connectivity through robust StaCubic.fold_id mapping first (preferred)
    term_ids = get_terminal_ids(element_id=tr3.ID, cubics_by_objid=cubics_by_objid)
    if len(term_ids) == 3:
        bus_a = bus_by_term_id[term_ids[0]]
        bus_b = bus_by_term_id[term_ids[1]]
        bus_c = bus_by_term_id[term_ids[2]]
    else:
        bus_ids = stacubic_dict[_ref_id(tr3.ID)]
        bus_a = buses[bus_ids[0]]
        bus_b = buses[bus_ids[1]]
        bus_c = buses[bus_ids[2]]

    bus_hv, bus_mv, bus_lv = _order_hv_mv_lv(bus_a=bus_a,
                                             bus_b=bus_b,
                                             bus_c=bus_c,
                                             logger=logger,
                                             tr_name=tr3.loc_name)

    # Graphic position not working right now
    x = (float(bus_hv.x) + float(bus_mv.x) + float(bus_lv.x)) / 3.0
    y = (float(bus_hv.y) + float(bus_mv.y) + float(bus_lv.y)) / 3.0

    transformer_name = _get_non_empty_name(tr3.loc_name, f"Transformer3W_{_ref_id(tr3.ID)}")
    transformer_name = _get_parallel_device_name(transformer_name, parallel_index, parallel_count)
    transformer_idtag = _get_parallel_device_idtag(_ref_id(tr3.ID), parallel_index, parallel_count)

    trafo3w = dev.Transformer3W(name=transformer_name,
                                idtag=transformer_idtag,
                                bus1=bus_hv,
                                bus2=bus_mv,
                                bus3=bus_lv,
                                active=not tr3.outserv,
                                x=x,
                                y=y)

    trafo3w.fill_from_design_values(
        V1=float(template.utrn3_h),
        V2=float(template.utrn3_m),
        V3=float(template.utrn3_l),
        Sn1=float(template.strn3_h),
        Sn2=float(template.strn3_m),
        Sn3=float(template.strn3_l),
        Pcu12=float(template.pcut3_h),
        Pcu23=float(template.pcut3_m),
        Pcu31=float(template.pcut3_l),
        Vsc12=float(template.uktr3_h),
        Vsc23=float(template.uktr3_m),
        Vsc31=float(template.uktr3_l),
        Pfe=float(template.pfe),
        I0=float(template.curm3),
        Sbase=float(baseMVA),
    )

    _apply_tr3_winding_tap_data(
        winding=trafo3w.winding1,
        current_position=int(tr3.n3tap_h),
        neutral_position=int(template.n3tp0_h),
        minimum_position=int(template.n3tmn_h),
        maximum_position=int(template.n3tmx_h),
        step_percent=float(template.du3tp_h),
        phase_angle_deg=float(template.ph3tr_h)
    )
    _apply_tr3_winding_tap_data(
        winding=trafo3w.winding2,
        current_position=int(tr3.n3tap_m),
        neutral_position=int(template.n3tp0_m),
        minimum_position=int(template.n3tmn_m),
        maximum_position=int(template.n3tmx_m),
        step_percent=float(template.du3tp_m),
        phase_angle_deg=float(template.ph3tr_m)
    )
    _apply_tr3_winding_tap_data(
        winding=trafo3w.winding3,
        current_position=int(tr3.n3tap_l),
        neutral_position=int(template.n3tp0_l),
        minimum_position=int(template.n3tmn_l),
        maximum_position=int(template.n3tmx_l),
        step_percent=float(template.du3tp_l),
        phase_angle_deg=float(template.ph3tr_l)
    )

    _apply_tr3_winding_connection_data(
        winding=trafo3w.winding1,
        pf_connection_code=str(template.tr3cn_h),
        pf_vector_group_angle=float(template.nt3ag_h)
    )
    _apply_tr3_winding_connection_data(
        winding=trafo3w.winding2,
        pf_connection_code=str(template.tr3cn_m),
        pf_vector_group_angle=float(template.nt3ag_m)
    )
    _apply_tr3_winding_connection_data(
        winding=trafo3w.winding3,
        pf_connection_code=str(template.tr3cn_l),
        pf_vector_group_angle=float(template.nt3ag_l)
    )

    hv_closed, mv_closed, lv_closed = _get_tr3_winding_closed_states(
        tr3_id=tr3.ID,
        cubics_by_objid=cubics_by_objid,
        switch_by_cubic_id=switch_by_cubic_id,
        bus_by_term_id=bus_by_term_id,
        bus_hv=bus_hv,
        bus_mv=bus_mv,
        bus_lv=bus_lv,
    )
    trafo3w.winding1.active = hv_closed
    trafo3w.winding2.active = mv_closed
    trafo3w.winding3.active = lv_closed

    return trafo3w


def build_switch_by_cubic_id(staswitchs: List[StaSwitch]) -> Dict[str, StaSwitch]:
    """
    Build a dictionary mapping StaCubic.ID -> StaSwitch.
    In DGS/PowerFactory, StaSwitch.fold_id points to the StaCubic that owns the switch.
    :param staswitchs: List of StaSwitch objects from DGS
    :return: Dictionary where key is Cubic ID and value is the Switch object
    """
    d: Dict[str, StaSwitch] = dict()
    for sw in staswitchs:
        cubic_id: str | None = _ref_id(sw.fold_id)
        if cubic_id is None or cubic_id == "":
            continue
        d[cubic_id] = sw
    return d


def convert_dgs_to_switches_from_elmcoup(elmcoups: List[ElmCoup],
                                         cubics_by_objid: Dict[str, List[StaCubic]],
                                         bus_by_term_id: Dict[str, dev.Bus],
                                         switch_by_cubic_id: Dict[str, StaSwitch],
                                         typ_switch_by_id: Dict[str, TypSwitch],
                                         sbase_mva: float,
                                         logger: Logger) -> List[dev.Switch]:
    """
    Create VeraGrid Switch devices from ElmCoup.

    :param elmcoups: List of ElmCoup objects from DGS
    :param cubics_by_objid: Dictionary mapping Element ID -> List of StaCubic cubicles
    :param bus_by_term_id: Dictionary mapping ElmTerm.ID -> VeraGrid Bus
    :param switch_by_cubic_id: Dictionary mapping StaCubic.ID -> StaSwitch (via StaSwitch.fold_id)
    :param logger: Logger instance to report warnings
    :return: List of VeraGrid Switch objects
    """
    switches: List[dev.Switch] = list()

    for coup in elmcoups:
        coup_id: str | None = _ref_id(coup.ID)
        if coup_id is None or coup_id == "":
            continue

        # Resolve connectivity
        term_ids_raw: List[str] = get_terminal_ids(element_id=coup_id, cubics_by_objid=cubics_by_objid)

        # Deduplicate terminals while preserving order
        term_ids: List[str] = list()
        for tid in term_ids_raw:
            if tid not in term_ids:
                term_ids.append(tid)

        if len(term_ids) != 2:
            logger.add_warning(
                f"Not exactly 2 terminals.",
                device=coup.ID,
                device_class="ElmCoup",
                value=str(len(term_ids)),
                expected_value="2"
            )
            continue

        bus_from: dev.Bus = bus_by_term_id[term_ids[0]]
        bus_to: dev.Bus = bus_by_term_id[term_ids[1]]

        # Skip degenerate cases
        if bus_from is bus_to:
            logger.add_warning(
                f"Both ends connect to the same bus.",
                device=coup.ID,
                device_class="ElmCoup"
            )
            continue

        # ElmCoup.on_off is the authoritative electrical state
        is_closed: bool = (int(coup.on_off) != 0)

        # Validation using StaSwitch on each cubicle
        # (StaSwitch.on_off may represent a cubicle-end representation, not the physical device state)
        cubics: List[StaCubic] = cubics_by_objid.get(coup_id, list())
        for cb in cubics:
            cb_id: str | None = _ref_id(cb.ID)
            if cb_id is None or cb_id == "":
                continue

            stasw: StaSwitch | None = switch_by_cubic_id.get(cb_id, None)
            if stasw is None:
                continue

            stasw_closed: bool = (int(stasw.on_off) != 0)
            if stasw_closed != is_closed:
                logger.add_warning(
                    f"state differs from StaSwitch. Using ElmCoup.on_off as truth.",
                    device=coup.ID,
                    device_class="ElmCoup",
                    value=int(coup.on_off),
                    expected_value=int(stasw.on_off)
                )

        graphic_type: SwitchGraphicType = _convert_pf_switch_graphic_type(iuse=0, ausage=coup.aUsage)
        typ_switch = _resolve_pointer_dict_value(key=coup.typ_id, mapping=typ_switch_by_id)
        rated_current = 0.0
        switch_r = 1e-20
        switch_x = 1e-20

        if typ_switch is not None:
            rated_current = max(float(typ_switch.InomA), float(typ_switch.InomB))
            bus_vnom = max(float(bus_from.Vnom), float(bus_to.Vnom))
            switch_r, switch_x = _get_switch_impedance_in_pu(
                r_ohm=float(typ_switch.Ron),
                x_ohm=float(typ_switch.Xon),
                vnom_kv=bus_vnom,
                sbase_mva=sbase_mva
            )
        else:
            pass

        sw = dev.Switch(
            bus_from=bus_from,
            bus_to=bus_to,
            name=coup.loc_name or f"ElmCoup_{coup_id}",
            idtag=coup_id,
            code=coup.typ_id,
            r=switch_r,
            x=switch_x,
            active=is_closed,
            normal_open=not is_closed,
            retained=False,
            rated_current=rated_current,
            graphic_type=graphic_type
        )

        switches.append(sw)

    return switches


def _convert_pf_switch_graphic_type(iuse: int, ausage: str) -> SwitchGraphicType:
    """
    Convert PowerFactory/DGS switch usage fields to a VeraGrid SwitchGraphicType.

    This mapping uses SwitchGraphicType.__members__ to avoid referencing enum values
    that may not exist in a given VeraGrid version.
    """
    usage = str(ausage).strip().upper()

    usage_to_member: Dict[str, str] = {
        "CB": "CircuitBreaker",
        "BREAKER": "CircuitBreaker",
        "CBK": "CircuitBreaker",
        "DIS": "Disconnector",
        "DISCONNECTOR": "Disconnector",
        "LBS": "LoadBreakSwitch",
        "LOADBREAKSWITCH": "LoadBreakSwitch",
        "FUSE": "Fuse",
    }

    member_name = usage_to_member.get(usage, None)
    if member_name is not None and member_name in SwitchGraphicType.__members__:
        return SwitchGraphicType.__members__[member_name]

    iuse_to_member: Dict[int, str] = {
        0: "CircuitBreaker",
        1: "Disconnector",
        2: "LoadBreakSwitch",
        3: "Fuse",
    }

    member_name = iuse_to_member.get(int(iuse), "CircuitBreaker")
    if member_name in SwitchGraphicType.__members__:
        return SwitchGraphicType.__members__[member_name]

    return SwitchGraphicType.CircuitBreaker


def convert_dgs_to_switch(stasw: StaSwitch,
                          buses: List[dev.Bus],
                          stacubic_dict: Dict[str, List[int]],
                          logger: Logger,
                          cubics_by_objid: Dict[str, List[StaCubic]],
                          bus_by_term_id: Dict[str, dev.Bus]) -> dev.Switch | None:
    """
    Convert a PowerFactory/DGS StaSwitch into a VeraGrid Switch.

    Connectivity is resolved via StaCubic:
      StaCubic.obj_id == StaSwitch.ID
      StaCubic.fold_id == ElmTerm.ID
    """
    term_ids: List[str] = get_terminal_ids(element_id=stasw.ID, cubics_by_objid=cubics_by_objid)
    if len(term_ids) != 2:
        logger.add_warning(
            f"not connected to exactly 2 terminals.",
            device=f"'{stasw.loc_name}' (ID={stasw.ID})",
            device_class="StaSwitch",
        )
        return None

    bus_from = bus_by_term_id[term_ids[0]]
    bus_to = bus_by_term_id[term_ids[1]]

    # PowerFactory/DGS state: on_off (int)
    # We interpret on_off != 0 as "closed/connected" (active switch).
    is_closed: bool = (int(stasw.on_off) != 0)
    normal_open: bool = not is_closed

    graphic_type: SwitchGraphicType = _convert_pf_switch_graphic_type(iuse=stasw.iUse,
                                                                      ausage=stasw.aUsage)

    sw = dev.Switch(bus_from=bus_from,
                    bus_to=bus_to,
                    name=stasw.loc_name,
                    idtag=stasw.ID,
                    code=stasw.typ_id,
                    active=is_closed,
                    normal_open=normal_open,
                    retained=False,
                    rated_current=0.0,
                    graphic_type=graphic_type)

    return sw


def convert_dgs_to_line(
        lne: ElmLne,
        buses: List[dev.Bus],
        stacubic_dict: Dict[str, List[int]],
        templates_dict: Dict[str, dev.SequenceLineType],
        overhead_line_type_dict: Dict[str, OverheadLineType],
        line_type_by_line_id: Dict[str, str],
        line_sections_by_line_id: Dict[str, List[ElmLnesec]],
        tower_template_by_line_id: Dict[str, OverheadLineType],
        freq: float,
        baseMVA: float,
        logger: Logger,
        cubics_by_objid: Dict[str, List[StaCubic]],
        bus_by_term_id: Dict[str, dev.Bus],
        parallel_index: int = 0,
        parallel_count: int = 1
) -> dev.Line:
    """
    Convert a PowerFactory/DGS ElmLne into a VeraGrid Line.

    Template resolution order
    -------------------------
    1) Use ElmLne.typ_id if present.
    2) If missing/empty, use ``line_type_by_line_id`` (built from ElmLnesec / IntFolder hierarchy).
    3) First try TypLne -> SequenceLineType, otherwise try TypTow -> OverheadLineType.

    Notes
    -----
    - Connectivity is resolved via StaCubic.fold_id -> ElmTerm.ID (preferred), with a legacy index-based fallback.
    - This function must not reference the DGS container (dgs_grid). All required mappings are passed in.
    """



    # ------------------------------------------------------------
    # Connectivity via StaCubic.fold_id -> ElmTerm.ID (preferred)
    # ------------------------------------------------------------
    term_ids = get_terminal_ids(element_id=lne.ID, cubics_by_objid=cubics_by_objid)
    if len(term_ids) != 2:
        bus_ids = stacubic_dict.get(_ref_id(lne.ID), None)
        if bus_ids is None:
            raise ValueError(f"No buses for the line {lne.ID}")
        if len(bus_ids) != 2:
            raise ValueError(f"Not exactly 2 buses for the line {lne.ID}")

    bus_from, bus_to = get_branch_buses(
        elm_id=lne.ID,
        stacubic_dict=stacubic_dict,
        buses=buses,
        cubics_by_objid=cubics_by_objid,
        bus_by_term_id=bus_by_term_id
    )

    line_name = _get_non_empty_name(lne.loc_name, f"Line_{_ref_id(lne.ID)}")
    line_name = _get_parallel_device_name(line_name, parallel_index, parallel_count)
    line_idtag = _get_parallel_device_idtag(_ref_id(lne.ID), parallel_index, parallel_count)

    line = dev.Line(
        bus_from=bus_from,
        bus_to=bus_to,
        name=line_name,
        idtag=line_idtag,
        active=not lne.outserv,
        length=lne.dline
    )

    line_key = _ref_id(lne.ID)
    if line_key is None or line_key == "":
        line_key = str(lne.ID)
    else:
        pass
    owned_sections = line_sections_by_line_id.get(line_key, list())
    if len(owned_sections) > 0:
        sections_length = 0.0
        for section in owned_sections:
            sections_length += float(section.dline)
        if sections_length > 0.0:
            line.length = sections_length
        else:
            pass
    else:
        pass

    # ------------------------------------------------------------
    # Apply the resolved template
    # ------------------------------------------------------------

    # ------------------------------------------------------------
    # Resolve typ_id (some PF exports store the type in ElmLnesec instead of ElmLne).
    # If the line is part of an ElmTow (tower coupling), it may legitimately have no typ_id.
    # In that case, we defer the template to the tower mapping.
    # ------------------------------------------------------------
    typ_id: str | None = lne.typ_id
    if typ_id is None or typ_id == "":
        # Try raw line ID and normalized pointer ID
        typ_id = line_type_by_line_id.get(lne.ID, None)
        if typ_id is None or typ_id == "":
            lid = _ref_id(lne.ID)
            if lid is not None and lid != "":
                typ_id = line_type_by_line_id.get(lid, None)

    # Tower-derived template (ElmTow -> TypTow). This is used only when typ_id is missing.
    tower_template: OverheadLineType | None = None
    if typ_id is None or typ_id == "":
        tower_template = tower_template_by_line_id.get(lne.ID, None)
        if tower_template is None:
            lid = _ref_id(lne.ID)
            if lid is not None and lid != "":
                tower_template = tower_template_by_line_id.get(lid, None)

    # ------------------------------------------------------------
    # Resolve the line template (TypLne or TypTow)
    # ------------------------------------------------------------
    seq_template: dev.SequenceLineType | None = None
    ohl_template: OverheadLineType | None = None

    if typ_id is not None and typ_id != "":
        seq_template = templates_dict.get(typ_id, None)
        if seq_template is None:
            tid = _ref_id(typ_id)
            if tid is not None and tid != "":
                seq_template = templates_dict.get(tid, None)

        if seq_template is None:
            ohl_template = overhead_line_type_dict.get(typ_id, None)
            if ohl_template is None:
                tid = _ref_id(typ_id)
                if tid is not None and tid != "":
                    ohl_template = overhead_line_type_dict.get(tid, None)
    else:
        # typ_id is missing: rely on tower coupling template
        ohl_template = tower_template

    applied_template = False
    if len(owned_sections) > 0:
        section_r = 0.0
        section_x = 0.0
        section_b = 0.0
        section_r0 = 0.0
        section_x0 = 0.0
        section_b0 = 0.0
        section_rate: float | None = None
        section_template_found = False
        bus_vnom = line.get_max_bus_nominal_voltage()

        ordered_sections = sorted(owned_sections, key=_line_section_index_sort_key)
        for section in ordered_sections:
            seq_section_template = _resolve_pointer_dict_value(key=section.typ_id, mapping=templates_dict)
            ohl_section_template = _resolve_pointer_dict_value(key=section.typ_id, mapping=overhead_line_type_dict)

            if seq_section_template is not None:
                section_template_found = True
                values = seq_section_template.get_values(
                    Sbase=baseMVA,
                    freq=freq,
                    length=float(section.dline),
                    line_Vnom=bus_vnom,
                    decimals_rounding=16  # basically not rounding
                )
                section_r += float(values[0])
                section_x += float(values[1])
                section_b += float(values[2])
                section_r0 += float(values[3])
                section_x0 += float(values[4])
                section_b0 += float(values[5])
                current_rate = float(values[6])
            elif ohl_section_template is not None:
                if not ohl_section_template.is_computed():
                    ohl_section_template.compute()
                else:
                    pass
                section_template_found = True
                values = ohl_section_template.get_values(
                    Sbase=baseMVA,
                    length=float(section.dline),
                    circuit_index=1,
                    Vnom=bus_vnom
                )
                section_r += float(values[0])
                section_x += float(values[1])
                section_b += float(values[2])
                section_r0 += float(values[3])
                section_x0 += float(values[4])
                section_b0 += float(values[5])
                current_rate = float(values[6])
            else:
                current_rate = 0.0
                logger.add_warning(
                    "Line section type not found.",
                    device=section.loc_name,
                    device_class="ElmLnesec",
                    value=str(section.typ_id)
                )

            current_rate = current_rate * float(section.fline)
            if section_rate is None:
                section_rate = current_rate
            else:
                if current_rate > 0.0:
                    section_rate = min(section_rate, current_rate)
                else:
                    pass

        if section_template_found:
            line.R = section_r
            line.X = section_x
            line.B = section_b
            line.R0 = section_r0
            line.X0 = section_x0
            line.B0 = section_b0
            if section_rate is not None:
                line.rate = section_rate
            else:
                pass
            applied_template = True
        else:
            applied_template = False
    elif seq_template is not None:
        line.apply_template(obj=seq_template, Sbase=baseMVA, freq=freq, logger=logger)
        applied_template = True
    elif ohl_template is not None:
        # OverheadLineType uses a 1-based circuit index. Default to circuit 1 here.
        line.set_circuit_idx(val=1, obj=ohl_template)
        line.apply_template(obj=ohl_template, Sbase=baseMVA, freq=freq, logger=logger)
        applied_template = True
    else:
        pass

    if applied_template:
        line.rate = float(line.rate) * float(lne.fline)
    else:
        pass

    return line


def convert_dgs_common_impedance_to_series_reactance(
        element: ElmZpu,
        buses: List[dev.Bus],
        bus_by_terminal_id: Dict[str, dev.Bus],
        stacubic_dict: Dict[str, List[int]],
        cubics_by_obj_id: Dict[str, List[StaCubic]],
        logger: Logger,
        Sbase_vg: float
) -> dev.SeriesReactance:
    """
    Convert a PowerFactory DGS common impedance element into a VeraGrid Line device.

    Supported DGS elements:
    - ElmZpu (Common Impedance)

    The connectivity is resolved through StaCubic terminals, exactly like lines/transformers.
    """

    # Resolve buses via StaCubic.fold_id -> ElmTerm.ID -> Bus (same approach as lines/transformers)
    term_ids: List[str] = get_terminal_ids(element_id=element.ID, cubics_by_objid=cubics_by_obj_id)
    if len(term_ids) != 2:
        raise ValueError(
            f"ElmZpu '{element.loc_name}' (ID={element.ID}) is not connected to exactly 2 terminals.")

    bus_from, bus_to = get_branch_buses(
        elm_id=element.ID,
        stacubic_dict=stacubic_dict,
        buses=buses,
        cubics_by_objid=cubics_by_obj_id,
        bus_by_term_id=bus_by_terminal_id
    )

    name: str = element.loc_name

    r1 = element.r_pu * Sbase_vg / element.Sn
    x1 = element.x_pu * Sbase_vg / element.Sn

    sr = dev.SeriesReactance(
        bus_from=bus_from,
        bus_to=bus_to,
        name=name,
        idtag=_ref_id(element.ID),
        active=not element.outserv,
        r=r1,
        x=x1,
        rate=element.Sn
    )

    return sr


def convert_dgs_series_capacitor_to_reactance(
        element: ElmScap,
        buses: List[dev.Bus],
        bus_by_terminal_id: Dict[str, dev.Bus],
        stacubic_dict: Dict[str, List[int]],
        cubics_by_obj_id: Dict[str, List[StaCubic]],
        logger: Logger,
        sbase_mva: float = 100.0
) -> dev.SeriesReactance:
    """
    Convert a PowerFactory DGS series capacitor element into a VeraGrid SeriesReactance device.

    Supported DGS elements:
    - ElmScap (Series Capacitor)

    The connectivity is resolved through StaCubic terminals, exactly like lines/transformers.
    """

    # Resolve buses via StaCubic.fold_id -> ElmTerm.ID -> Bus (same approach as lines/transformers)
    term_ids: List[str] = get_terminal_ids(element_id=element.ID, cubics_by_objid=cubics_by_obj_id)
    if len(term_ids) != 2:
        raise ValueError(
            f"ElmSind '{element.loc_name}' (ID={element.ID}) is not connected to exactly 2 terminals.")

    bus_from, bus_to = get_branch_buses(
        elm_id=element.ID,
        stacubic_dict=stacubic_dict,
        buses=buses,
        cubics_by_objid=cubics_by_obj_id,
        bus_by_term_id=bus_by_terminal_id
    )

    name: str = element.loc_name

    # Rated power calculation [MVA]
    Ur = element.ucn
    Ir = element.Curn
    Sr = np.sqrt(3) * Ur * Ir

    # Series capacitive reactance [pu]
    Zbase = Ur**2 / sbase_mva
    x = -1 * element.xcap / Zbase

    series_reactance = dev.SeriesReactance(
        bus_from=bus_from,
        bus_to=bus_to,
        name=name,
        idtag=_ref_id(element.ID),
        active=not element.outserv,
        r=0.0,
        x=x,
        rate=Sr
    )

    return series_reactance


def convert_dgs_to_series_reactance(
        element: ElmSind,
        buses: List[dev.Bus],
        bus_by_terminal_id: Dict[str, dev.Bus],
        stacubic_dict: Dict[str, List[int]],
        cubics_by_obj_id: Dict[str, List[StaCubic]],
        typsind_dict: Dict[str, TypSind],
        logger: Logger,
        sbase_mva: float = 100.0
) -> dev.SeriesReactance:
    """
    Convert a PowerFactory DGS series impedance element into a VeraGrid SeriesReactance device.

    Supported DGS elements:
    - ElmSind (Series reactor / series reactance)

    The connectivity is resolved through StaCubic terminals, exactly like lines/transformers.
    """

    # Resolve buses via StaCubic.fold_id -> ElmTerm.ID -> Bus (same approach as lines/transformers)
    term_ids: List[str] = get_terminal_ids(element_id=element.ID, cubics_by_objid=cubics_by_obj_id)
    if len(term_ids) != 2:
        raise ValueError(
            f"ElmSind '{element.loc_name}' (ID={element.ID}) is not connected to exactly 2 terminals.")

    bus_from, bus_to = get_branch_buses(
        elm_id=element.ID,
        stacubic_dict=stacubic_dict,
        buses=buses,
        cubics_by_objid=cubics_by_obj_id,
        bus_by_term_id=bus_by_terminal_id
    )

    name: str = element.loc_name

    # Initialize sequence impedances (p.u.)
    r_pu: float = 1e-20
    x_pu: float = 1e-20
    r0_pu: float = 1e-20
    x0_pu: float = 1e-20
    r2_pu: float = 1e-20
    x2_pu: float = 1e-20

    # --- ElmSind: series reactor / series reactance

    # Prefer the type/template if present (PowerFactory "Type" pattern)
    typ_id: str | None = _ref_id(element.typ_id)
    if typ_id == "":
        typ_id = None

    src: ElmSind | TypSind = element
    if typ_id is not None and typ_id in typsind_dict:
        src = typsind_dict[typ_id]

    # PowerFactory ElmSind (as exported in test_export_v5.dgs):
    # - ucn: rated voltage (kV)
    # - Sn : rated power (MVA)
    # - uk : short-circuit voltage (%), gives |Z| in p.u. on device base (Sn, ucn)
    # - Pcu: copper losses (kW) at rated current, gives R in p.u. on device base
    sn_mva: float = float(src.Sn)
    uk_pu_dev: float = float(src.uk) / 100.0
    p_cu_mw: float = float(src.Pcu) / 1000.0

    r_pu_dev: float = p_cu_mw / sn_mva
    z_pu_dev: float = uk_pu_dev
    x_pu_dev: float = math.sqrt(max(0.0, z_pu_dev * z_pu_dev - r_pu_dev * r_pu_dev))

    # Convert from device base (Sn, ucn) to system base (sbase_mva, Vbase)
    v_dev_kv: float = float(src.ucn)
    v_base_kv: float = float(max(float(bus_from.Vnom), float(bus_to.Vnom)))
    v_ratio: float = v_dev_kv / v_base_kv

    scale: float = (sbase_mva / sn_mva) * (v_ratio * v_ratio)

    r_pu = r_pu_dev * scale
    x_pu = x_pu_dev * scale

    # If no explicit sequence data is exported, keep them consistent with positive sequence
    r0_pu = r_pu
    x0_pu = x_pu
    r2_pu = r_pu
    x2_pu = x_pu

    series_reactance = dev.SeriesReactance(
        bus_from=bus_from,
        bus_to=bus_to,
        name=name,
        idtag=_ref_id(element.ID),
        active=not element.outserv,
        r=r_pu,
        x=x_pu,
        r0=r0_pu,
        x0=x0_pu,
        r2=r2_pu,
        x2=x2_pu,
        rate=sn_mva
    )

    return series_reactance


def _get_scale_factor(scale0: float, logger: Logger, name: str) -> float:
    """
    Interpret PowerFactory/DGS load scaling factor.
    """
    s = scale0
    if s == 0.0:
        return 1.0

    # Heuristic: values > 10 are very likely percentages (e.g., 100 = 100%)
    if s > 10.0:
        logger.add_warning(
            f"looks like percent.",
            device=name,
            device_class="ElmLod",
            value=s,
        )
        return s / 100.0

    return s


def _extract_load_pq(elmlod: ElmLod, logger: Logger) -> Tuple[float, float]:
    """
    Extract (P, Q) in MW/MVAr from an ElmLod.
    """
    name = elmlod.loc_name or _ref_id(elmlod.ID) or "Load"

    # Primary: direct P/Q
    p = elmlod.plini
    q = elmlod.qlini

    # Fallback: S + cos(phi)
    if p == 0.0 and q == 0.0:
        s = elmlod.slini
        cosphi = elmlod.coslini

        if s != 0.0 and cosphi != 0.0:
            cosphi = max(min(cosphi, 1.0), -1.0)
            p = s * cosphi
            sinphi = math.sqrt(max(0.0, 1.0 - cosphi * cosphi))
            q = s * sinphi
            logger.add_warning(
                f"P/Q not provided, derived from slini/coslini.",
                device=name,
                device_class="ElmLod",
                value=q,
            )

    # Apply scaling
    scale = _get_scale_factor(scale0=elmlod.scale0, logger=logger, name=name)
    p *= scale
    q *= scale

    return p, q


def convert_dgs_ward_equivalent_to_load(elmvac: ElmVac,
                                        stacubic_dict: Dict[str, List[int]],
                                        buses: List[dev.Bus],
                                        logger: Logger,
                                        cubics_by_objid: Dict[str, List[StaCubic]],
                                        bus_by_term_id: Dict[str, dev.Bus]) -> Tuple[dev.Bus, dev.Load]:
    """
    Convert ElmVac to VeraGrid Load.
    """
    bus = get_injection_bus(elm_id=elmvac.ID,
                            stacubic_dict=stacubic_dict,
                            buses=buses,
                            cubics_by_objid=cubics_by_objid,
                            bus_by_term_id=bus_by_term_id)

    name: str = elmvac.loc_name

    constant_p = elmvac.Pload - elmvac.Pgen # Net constant P active power [MW]
    constant_q = elmvac.Qload - elmvac.Qgen # Net constant Q reactive power [Mvar]
    constant_g = elmvac.Pzload # Constant Z active power [MW]
    constant_b = -1 * elmvac.Qzload # Constant Z reactive power [Mvar]

    load = dev.Load(
        name=name,
        idtag=_ref_id(elmvac.ID),
        P=constant_p,
        Q=constant_q,
        G=constant_g,
        B=constant_b,
        active=not bool(elmvac.outserv)
    )

    return bus, load


def convert_dgs_to_load(elmlod: ElmLod,
                        stacubic_dict: Dict[str, List[int]],
                        buses: List[dev.Bus],
                        logger: Logger,
                        cubics_by_objid: Dict[str, List[StaCubic]],
                        bus_by_term_id: Dict[str, dev.Bus]) -> Tuple[dev.Bus, dev.Load]:
    """
    Convert ElmLod to VeraGrid Load.
    """
    bus = get_injection_bus(elm_id=elmlod.ID,
                            stacubic_dict=stacubic_dict,
                            buses=buses,
                            cubics_by_objid=cubics_by_objid,
                            bus_by_term_id=bus_by_term_id)

    p_mw, q_mvar = _extract_load_pq(elmlod=elmlod, logger=logger)

    load = dev.Load(
        name=elmlod.loc_name or f"Load_{_ref_id(elmlod.ID)}",
        P=p_mw,
        Q=q_mvar,
        active=not bool(elmlod.outserv)
    )

    return bus, load


def convert_dgs_staticgen_to_gen(elmgenstat: ElmGenstat,
                                      stacubic_dict: Dict[str, List[int]],
                                      buses: List[dev.Bus],
                                      logger: Logger,
                                      cubics_by_objid: Dict[str, List[StaCubic]],
                                      bus_by_term_id: Dict[str, dev.Bus],
                                      parallel_index: int = 0,
                                      parallel_count: int = 1) -> Tuple[dev.Bus, dev.Generator]:
    """
    Convert ElmGenstat to VeraGrid Generator.
    """
    bus = get_injection_bus(elm_id=elmgenstat.ID,
                            stacubic_dict=stacubic_dict,
                            buses=buses,
                            cubics_by_objid=cubics_by_objid,
                            bus_by_term_id=bus_by_term_id)

    # Slack/reference machine indicator (PowerFactory exports ip_ctrl=1 on the slack generator)
    if int(elmgenstat.ip_ctrl) == 1:
        bus.is_slack = True

    generator_name = _get_non_empty_name(elmgenstat.loc_name, f"{_ref_id(elmgenstat.ID)}")
    generator_name = _get_parallel_device_name(generator_name, parallel_index, parallel_count)
    generator_idtag = _get_parallel_device_idtag(_ref_id(elmgenstat.ID), parallel_index, parallel_count)

    gen = dev.Generator(
        name=generator_name,
        idtag=generator_idtag,
        P=float(elmgenstat.pgini),
        vset=float(elmgenstat.usetp),
        Snom=float(elmgenstat.sgn),
        active=not bool(elmgenstat.outserv)
    )

    return bus, gen


def convert_dgs_staticgen_to_battery(elmgenstat: ElmGenstat,
                                     stacubic_dict: Dict[str, List[int]],
                                     buses: List[dev.Bus],
                                     logger: Logger,
                                     cubics_by_objid: Dict[str, List[StaCubic]],
                                     bus_by_term_id: Dict[str, dev.Bus],
                                     parallel_index: int = 0,
                                     parallel_count: int = 1) -> Tuple[dev.Bus, dev.Battery]:
    """
    Convert Storage ElmGenstat to VeraGrid Battery.
    """
    bus = get_injection_bus(elm_id=elmgenstat.ID,
                            stacubic_dict=stacubic_dict,
                            buses=buses,
                            cubics_by_objid=cubics_by_objid,
                            bus_by_term_id=bus_by_term_id)

    name = _get_non_empty_name(elmgenstat.loc_name, f"Storage_{_ref_id(elmgenstat.ID)}")
    name = _get_parallel_device_name(name, parallel_index, parallel_count)
    battery_idtag = _get_parallel_device_idtag(_ref_id(elmgenstat.ID), parallel_index, parallel_count)

    # Power Factor from P and Q
    P = float(elmgenstat.pgini)
    Q = float(elmgenstat.qgini)
    pf = np.cos(np.atan(Q/(P + 1e-20)))

    batttery = dev.Battery(
        name=name,
        idtag=battery_idtag,
        P=P,
        power_factor=pf,
        is_controlled=False,
        Snom=float(elmgenstat.sgn),
        active=not bool(elmgenstat.outserv)
    )

    return bus, batttery

def convert_dgs_to_static_gen(elmgenstat: ElmGenstat,
                              stacubic_dict: Dict[str, List[int]],
                              buses: List[dev.Bus],
                              logger: Logger,
                              cubics_by_objid: Dict[str, List[StaCubic]],
                              bus_by_term_id: Dict[str, dev.Bus],
                              parallel_index: int = 0,
                              parallel_count: int = 1) -> Tuple[dev.Bus, dev.StaticGenerator]:
    """
    Convert ElmGenstat to VeraGrid Static Generator.
    """
    bus = get_injection_bus(elm_id=elmgenstat.ID,
                            stacubic_dict=stacubic_dict,
                            buses=buses,
                            cubics_by_objid=cubics_by_objid,
                            bus_by_term_id=bus_by_term_id)

    # Slack/reference machine indicator (PowerFactory exports ip_ctrl=1 on the slack generator)
    if int(elmgenstat.ip_ctrl) == 1:
        bus.is_slack = True

    generator_name = _get_non_empty_name(elmgenstat.loc_name, f"StaticGen_{_ref_id(elmgenstat.ID)}")
    generator_name = _get_parallel_device_name(generator_name, parallel_index, parallel_count)
    generator_idtag = _get_parallel_device_idtag(_ref_id(elmgenstat.ID), parallel_index, parallel_count)

    stagen = dev.StaticGenerator(
        name=generator_name,
        idtag=generator_idtag,
        P=float(elmgenstat.pgini),
        Q=float(elmgenstat.qgini),
        Snom=float(elmgenstat.sgn),
        active=not bool(elmgenstat.outserv)
    )

    return bus, stagen


def convert_dgs_staticgen_to_vsc(elmgenstat: ElmGenstat,
                                 stacubic_dict: Dict[str, List[int]],
                                 buses: List[dev.Bus],
                                 logger: Logger,
                                 cubics_by_objid: Dict[str, List[StaCubic]],
                                 bus_by_term_id: Dict[str, dev.Bus],
                                 parallel_index: int = 0,
                                 parallel_count: int = 1) -> Tuple[dev.Bus, dev.VSC]:
    """
    Convert ElmGenstat to VeraGrid VSC.
    """
    ac_bus = get_injection_bus(elm_id=elmgenstat.ID,
                               stacubic_dict=stacubic_dict,
                               buses=buses,
                               cubics_by_objid=cubics_by_objid,
                               bus_by_term_id=bus_by_term_id)

    dc_bus = dev.Bus(name=f'{_ref_id(ac_bus.name)}_DC',
                     is_dc=True,
                     is_slack=True,
                     xpos=ac_bus.x,
                     ypos=ac_bus.y - 200,)

    vsc_name = _get_non_empty_name(elmgenstat.loc_name, f"VSC_{_ref_id(elmgenstat.ID)}")
    vsc_name = _get_parallel_device_name(vsc_name, parallel_index, parallel_count)
    vsc_idtag = _get_parallel_device_idtag(_ref_id(elmgenstat.ID), parallel_index, parallel_count)

    vsc = dev.VSC(
        name=vsc_name,
        idtag=vsc_idtag,
        active=not bool(elmgenstat.outserv),
        bus_from=dc_bus,
        bus_to=ac_bus,
        rate=float(elmgenstat.sgn),
        alpha1=0.0,
        alpha2=0.0,
        alpha3=0.0,
        control1=ConverterControlType.Pac,
        control2=ConverterControlType.Q_droop,
        control1_val=-1.0 * float(elmgenstat.pgini),
        control2_val=-1.0 * float(elmgenstat.qgini),
        fault_control=ConverterFaultControlType.WECC_WT_Type_4B,
        control2_droop=float(elmgenstat.ddroop),
        control2_droop_val_min=float(elmgenstat.usp_min),
        control2_droop_val_max=float(elmgenstat.usp_max),
        control2_droop_val=float(elmgenstat.usetp),
        control2_val_min=float(elmgenstat.cQ_min),
        control2_val_max=float(elmgenstat.cQ_max)
    )

    return dc_bus, vsc


def convert_dgs_external_grid_to_generator(elmxnet: ElmXnet,
                                           stacubic_dict: Dict[str, List[int]],
                                           buses: List[dev.Bus],
                                           logger: Logger,
                                           cubics_by_objid: Dict[str, List[StaCubic]],
                                           bus_by_term_id: Dict[str, dev.Bus],
                                           Sbase: float) -> Tuple[dev.Bus, dev.Generator]:
    """
    Convert ElmXnet to VeraGrid Generator.
    """
    bus = get_injection_bus(elm_id=elmxnet.ID,
                            stacubic_dict=stacubic_dict,
                            buses=buses,
                            cubics_by_objid=cubics_by_objid,
                            bus_by_term_id=bus_by_term_id)

    bustype = str(elmxnet.bustp).strip().upper()

    k = elmxnet.rntxn # R/X ratio
    Sk = elmxnet.snss # Short-circuit power Sk''
    c = elmxnet.cmax # Maximum voltage factor

    # Synchronous reactances
    xd = elmxnet.xd
    xq = elmxnet.xq
    if xd == xq:
        x = xd
    elif xd <= xq:
        x = xd
    else:
        x = xq

    Snom = x * np.sqrt(1 + k**2) * Sk / c # Nominal Power of the external grid [MVA]
    r1 = x * k * Sbase / Snom # Positive-sequence equivalent resistance [pu]
    x1 = x * Sbase / Snom # Positive-sequence equivalent reactance [pu]

    gen = dev.Generator(
        name=elmxnet.loc_name or f"Gen_{_ref_id(elmxnet.ID)}",
        active=not bool(elmxnet.outserv),
        r1=r1,
        x1=x1,
    )

    if bustype == 'SL':
        bus.is_slack = True

    elif bustype == 'PV':
        gen.Vset = elmxnet.usetp
        gen.P = elmxnet.pgini

    elif bustype == 'PQ':
        gen.P = elmxnet.pgini
        gen.power_factor = np.cos(np.atan(elmxnet.qgini / elmxnet.pgini))
    else:
        gen.P = elmxnet.pgini
        gen.power_factor = np.cos(np.atan(elmxnet.qgini / elmxnet.pgini))

    return bus, gen


def convert_dgs_to_external_grid(elmxnet: ElmXnet,
                                 stacubic_dict: Dict[str, List[int]],
                                 buses: List[dev.Bus],
                                 logger: Logger,
                                 cubics_by_objid: Dict[str, List[StaCubic]],
                                 bus_by_term_id: Dict[str, dev.Bus]) -> Tuple[dev.Bus, dev.ExternalGrid]:
    """
    Convert ElmXnet to VeraGrid External Grid.
    """
    bus = get_injection_bus(elm_id=elmxnet.ID,
                            stacubic_dict=stacubic_dict,
                            buses=buses,
                            cubics_by_objid=cubics_by_objid,
                            bus_by_term_id=bus_by_term_id)

    bustype = str(elmxnet.bustp).strip().upper()

    xgrid = dev.ExternalGrid(
        name=elmxnet.loc_name or f"Load_{_ref_id(elmxnet.ID)}",
        active=not bool(elmxnet.outserv)
    )

    if bustype == 'SL':
        bus.is_slack = True
        xgrid.mode = ExternalGridMode.VD
        xgrid.Vm = elmxnet.usetp
        xgrid.Va = math.radians(float(elmxnet.phiini))

    elif bustype == 'PV':
        xgrid.mode = ExternalGridMode.PV
        xgrid.Vm = elmxnet.usetp
        xgrid.P = elmxnet.pgini

    elif bustype == 'PQ':
        xgrid.mode = ExternalGridMode.PQ
        xgrid.P = elmxnet.pgini
        xgrid.Q = elmxnet.qgini
    else:
        xgrid.mode = ExternalGridMode.PQ
        xgrid.P = elmxnet.pgini
        xgrid.Q = elmxnet.qgini

    return bus, xgrid


def _extract_shunt_gb(elmshnt: ElmShnt, f: float, logger: Logger) -> Tuple[float, float]:
    """
    Extract (G, B) from an ElmShnt.
    VeraGrid expects:
      - G in MW @ v=1 p.u.
      - B in MVAr @ v=1 p.u. (positive capacitive, negative inductive)

    PowerFactory DGS typically provides:
      - qcapn / ncapa for capacitor steps
      - qrean for reactor MVAr
      - qtotn as total rated MVAr magnitude (often positive regardless of type)
      - shtype: 0 = R-L-C, 1 = R-L, 2 = C, 3 = R-L-C,Rp, 4 = R-L-C1-C2,Rp
    """
    name = elmshnt.loc_name or _ref_id(elmshnt.ID) or "Shunt"

    shtype: int = elmshnt.shtype
    Q: float = elmshnt.qtotn * 1e6  # Rated Reactive Power [Mvar] -> [var]
    U: float = elmshnt.ushnm * 1e3  # Rated Voltage [kV] -> [V]
    fres: float = elmshnt.fres  # Resonance Frequency [Hz]
    h = fres / f  # Tuning Order
    conn: int = elmshnt.ctech  # Connection
    quality_factor: float = elmshnt.grea  # Quality Factor

    w = 2 * np.pi * f  # Electrical angular speed [rad/s]
    if conn == 0:
        d_y = 3.0  # conn==0 -> 3PH-D
    else:
        d_y = 1.0  # 3PH-Y/YN

    if shtype == 0:  # R-L-C

        C = Q / (d_y * w * U ** 2) * (1 - 1 / h ** 2)
        L = 1 / ((h * w) ** 2 * C)
        if quality_factor == 0.0:
            R = 0.0
        else:
            R = (w * L) / quality_factor

        Z = R + 1j * (w * L - 1 / (w * C))
        S = d_y * U ** 2 / np.conj(Z)

        g_mw = np.real(S) / 1e6
        b_mvar = -np.imag(S) / 1e6

    elif shtype == 1:  # R-L

        L = d_y * U ** 2 / (w * Q)
        if quality_factor == 0.0:
            R = 0.0
        else:
            R = (w * L) / quality_factor

        Z = R + 1j * w * L
        S = d_y * U ** 2 / np.conj(Z)

        g_mw = np.real(S) / 1e6
        b_mvar = -np.imag(S) / 1e6

    elif shtype == 2:  # C

        C = Q / (d_y * w * U ** 2)
        G = w * C * elmshnt.tandc

        Y = G + 1j * w * C
        S = d_y * U ** 2 * np.conj(Y)

        g_mw = np.real(S) / 1e6
        b_mvar = -np.imag(S) / 1e6

    elif shtype == 3:  # R-L-C,Rp

        C = Q / (d_y * w * U ** 2) * (1 - 1 / h ** 2)
        L = 1 / ((h * w) ** 2 * C)
        if quality_factor == 0.0:
            R = 0.0
        else:
            R = (w * L) / quality_factor
        Rp = elmshnt.rpara

        try:
            Z = ((R + 1j * w * L) * Rp) / ((R + 1j * w * L) + Rp) + 1 / (1j * w * C)
            S = d_y * U ** 2 / np.conj(Z)

            g_mw = np.real(S) / 1e6
            b_mvar = -np.imag(S) / 1e6
        except ZeroDivisionError:
            g_mw = 0.0
            b_mvar = 0.0
            logger.add_warning(
                f"Cannot be computed because of zero division.",
                device=name,
                device_class="ElmShnt"
            )

    elif shtype == 4:  # R-L-C1-C2,Rp

        C2 = Q / (d_y * w * U ** 2)
        C1 = C2 * (h ** 2 - 1)
        L = 1 / (w ** 2 * C1)
        if quality_factor == 0.0:
            R = 0.0
        else:
            R = w * L / quality_factor
        Rp = elmshnt.rpara

        try:
            Z = ((R + 1j * w * L + 1 / (1j * w * C1)) * Rp) / ((R + 1j * w * L + 1 / (1j * w * C1)) + Rp) + 1 / (1j * w * C2)
            S = d_y * U ** 2 / np.conj(Z)

            g_mw = np.real(S) / 1e6
            b_mvar = -np.imag(S) / 1e6
        except ZeroDivisionError:
            g_mw = 0.0
            b_mvar = 0.0
            logger.add_warning(
                f"Cannot be computed because of zero division.",
                device=name,
                device_class="ElmShnt"
            )
    else:
        g_mw = 0.0
        b_mvar = 0.0
        logger.add_warning(
            f"Cannot be computed because of type not recognized.",
            device=name,
            device_class="ElmShnt",
            value=shtype
        )

    if elmshnt.ncapa == 0 and elmshnt.ncapx <= 1:
        g_mw = 0.0
        b_mvar = 0.0

    return g_mw, b_mvar


def convert_dgs_to_shunt(elmshnt: ElmShnt,
                         stacubic_dict: Dict[str, List[int]],
                         buses: List[dev.Bus],
                         logger: Logger,
                         cubics_by_objid: Dict[str, List[StaCubic]],
                         bus_by_term_id: Dict[str, dev.Bus],
                         frequency: float) -> Tuple[dev.Bus, dev.Shunt]:
    """
    Convert ElmShnt to VeraGrid fixed Shunt.
    """
    name = elmshnt.loc_name or f"Shunt_{_ref_id(elmshnt.ID)}"

    bus = get_injection_bus(elm_id=elmshnt.ID,
                            stacubic_dict=stacubic_dict,
                            buses=buses,
                            cubics_by_objid=cubics_by_objid,
                            bus_by_term_id=bus_by_term_id)

    g_mw, b_mvar = _extract_shunt_gb(elmshnt=elmshnt, f=frequency, logger=logger)

    shunt = dev.Shunt(name=name,
                      G=g_mw,
                      B=b_mvar,
                      active=(elmshnt.outserv == 0))

    return bus, shunt


def _build_elmshnt_step_model(elmshnt: ElmShnt, logger: Logger) -> Tuple[np.ndarray, int, float, float]:
    """
    Build the step model (b_steps, initial_step, Bmin, Bmax) for an ElmShnt with ncapx > 1.

    Notes
    -----
    - The ControllableShunt step setter sums step increments up to index 'step' (inclusive).
      To represent an OFF state (0 MVAr), we insert an explicit 0.0 increment as the first entry.
    - PowerFactory exports qcapn as MVAr per step at v=1 p.u. and ncapa as connected steps.
    """
    name: str = elmshnt.loc_name or _ref_id(elmshnt.ID) or "ElmShnt"
    ncapx: int = int(elmshnt.ncapx)
    q_step: float = float(elmshnt.qcapn)
    if q_step == 0.0:
        q_step = -abs(float(elmshnt.qrean))
    else:
        pass

    qtotn: float = float(elmshnt.qtotn)
    if q_step == 0.0 and qtotn != 0.0:
        q_step = qtotn / float(ncapx)
        if int(elmshnt.shtype) == 1:
            q_step = -abs(q_step)
        else:
            pass

        logger.add_warning(
            f"using q_step=qtotn/ncapx.",
            device=name,
            device_class="ElmShnt",
            value=q_step
        )
    else:
        pass

    # Step increments: [0.0, q_step, q_step, ..., q_step] with length ncapx+1
    b_steps: np.ndarray = np.concatenate((np.array([0.0], dtype=float), np.full(ncapx, q_step, dtype=float)))

    # Initial step index equals the number of connected steps (ncapa) because b_steps[0] is OFF (0 MVAr).
    initial_step: int = int(elmshnt.ncapa)
    if initial_step < 0:
        initial_step = 0
    else:
        pass
    if initial_step > ncapx:
        initial_step = ncapx
    else:
        pass

    # Bounds (MVAr @ v=1 p.u.) inferred from the step size sign
    total: float = q_step * float(ncapx)
    if total >= 0.0:
        bmin: float = 0.0
        bmax: float = total
    else:
        bmin = total
        bmax = 0.0

    return b_steps, initial_step, bmin, bmax


def convert_dgs_to_controllable_shunt_from_elmshnt(elmshnt: ElmShnt,
                                                   stacubic_dict: Dict[str, List[int]],
                                                   buses: List[dev.Bus],
                                                   logger: Logger,
                                                   cubics_by_objid: Dict[str, List[StaCubic]],
                                                   bus_by_term_id: Dict[str, dev.Bus],
                                                   frequency: float) -> Tuple[
    dev.Bus, dev.ControllableShunt]:
    """
    Convert stepped ElmShnt (ncapx > 1) to VeraGrid ControllableShunt.

    Mapping
    -------
    - Steps: ncapa (connected steps) is mapped to the initial ControllableShunt.step.
    - Reactive increments: qcapn is used as MVAr per step at v=1 p.u. (positive = capacitor, negative = reactor).
    - Voltage control: If 'iswitch' indicates controlled operation and the DGS provides 'usetp', we propagate it.
      Otherwise, the device is modeled as an operator-controllable stepped shunt (no automatic control).
    """
    name: str = elmshnt.loc_name or f"ElmShnt_{_ref_id(elmshnt.ID)}"

    bus: dev.Bus = get_injection_bus(elm_id=elmshnt.ID,
                                     stacubic_dict=stacubic_dict,
                                     buses=buses,
                                     cubics_by_objid=cubics_by_objid,
                                     bus_by_term_id=bus_by_term_id)

    if elmshnt.i_cont == 1: # Continuous

        b_steps, initial_step, bmin, bmax = _build_elmshnt_step_model(elmshnt=elmshnt, logger=logger)

        if int(elmshnt.iswitch) != 0:
            control_mode = ShuntControlMode.Discrete
        else:
            control_mode = ShuntControlMode.Locked

        vset: float = float(elmshnt.usetp)

        cshunt: dev.ControllableShunt = dev.ControllableShunt(
            name=name,
            idtag=_ref_id(elmshnt.ID),
            number_of_steps=int(len(b_steps)),
            step=int(initial_step),
            g_per_step=0.0,
            b_per_step=0.0,
            Bmin=bmin,
            Bmax=bmax,
            Gmin=0.0,
            Gmax=0.0,
            active=(elmshnt.outserv == 0),
            vset=vset,
            control_mode=control_mode,
            control_bus=bus,
        )

        # Override step arrays to match the DGS stepped-bank model (OFF + ncapx identical increments).
        cshunt.b_steps = b_steps
        cshunt.g_steps = np.zeros(len(b_steps), dtype=float)
        cshunt.active_steps = np.ones(len(b_steps), dtype=int)

        # Ensure B/G are coherent with the initial step after overriding arrays
        cshunt.step = int(initial_step)

    elif elmshnt.i_cont == 0: # Discrete

        g_mw, b_mvar = _extract_shunt_gb(elmshnt=elmshnt, f=frequency, logger=logger)

        cshunt: dev.ControllableShunt = dev.ControllableShunt(
            name=name,
            idtag=_ref_id(elmshnt.ID),
            number_of_steps=elmshnt.ncapx,
            step=elmshnt.ncapa,
            g_per_step=g_mw,
            b_per_step=b_mvar,
            active=(elmshnt.outserv == 0),
            vmax=elmshnt.usetp_mx,
            vmin=elmshnt.usetp_mn,
            control_mode=ShuntControlMode.Discrete
        )

    return bus, cshunt


def convert_dgs_svs_to_vsc(elmsvs: ElmSvs,
                           stacubic_dict: Dict[str, List[int]],
                           buses: List[dev.Bus],
                           logger: Logger,
                           cubics_by_objid: Dict[str, List[StaCubic]],
                           bus_by_term_id: Dict[str, dev.Bus]) -> Tuple[dev.Bus, dev.VSC]:
    """
    Convert ElmSvs (PowerFactory SVS/SVC) to VeraGrid VSC.

    Notes
    -----
    - Electrical connectivity is obtained via StaCubic, consistent with other injected devices.
    - If the DGS does not provide a voltage setpoint, Vset defaults to 1.0 p.u. (per project convention).
    """
    name = elmsvs.loc_name or f"ElmSvs_{_ref_id(elmsvs.ID)}"

    ac_bus = get_injection_bus(elm_id=elmsvs.ID,
                               stacubic_dict=stacubic_dict,
                               buses=buses,
                               cubics_by_objid=cubics_by_objid,
                               bus_by_term_id=bus_by_term_id)

    dc_bus = dev.Bus(name=f'{_ref_id(ac_bus.name)}_SVS_DC',
                     is_dc=True,
                     is_slack=True,
                     xpos=ac_bus.x,
                     ypos=ac_bus.y - 200, )

    vsc_name = _get_non_empty_name(elmsvs.loc_name, f"SVS_{_ref_id(elmsvs.ID)}")

    control_mode = elmsvs.i_ctrl

    if control_mode == 2: # Reactive Power Control

        control1 = ConverterControlType.Pac
        control1_val = 0.0  # Active power injection of the SVS [MW]

        control2 = ConverterControlType.Qac
        control2_val = elmsvs.qsetp  # Reactive power injection of the SVS [MVAr]

        rate = max(np.abs(elmsvs.tcrmax), np.abs(elmsvs.qmin))
        kpd = 0.0  # Droop [%]
        ysvs = 0.0  # Fixed admittance based on 1 MVA / Ub^2
        u_setpoint = 1.0  # Voltage Setpoint [pu]

    elif control_mode == 1: # Voltage Control
        if elmsvs.i_droop == 0: # No droop, just sets the voltage to the given setpoint

            control1 = ConverterControlType.Pac
            control1_val = 0.0  # Active power injection of the SVS [MW]

            control2 = ConverterControlType.Vm_ac
            control2_val = elmsvs.usetp # Voltage setpoint [pu]

            ysvs = 0.0 # Fixed admittance based on 1 MVA / Ub^2
            rate = max(np.abs(elmsvs.tcrmax), np.abs(elmsvs.qmin))
            kpd = 0.0 # Droop [%]
            u_setpoint = 1.0  # Voltage Setpoint [pu]

        else: # Droop Control

            kpd = elmsvs.ddroop # Droop [%]
            rate = elmsvs.Srated # Rated Power [MVA]
            u_setpoint = elmsvs.usetp # Voltage Setpoint [pu]


            control1 = ConverterControlType.Pac
            control1_val = 0.0  # Active power injection of the SVS [MW]

            control2 = ConverterControlType.Q_droop
            control2_val = 0.0  # Reactive power injection of the SVS [MVAr]

            ysvs = 0.0  # Fixed admittance based on 1 MVA / Ub^2

    else: # No Control
        control1 = ConverterControlType.Pac
        control2 = ConverterControlType.Qac

        # Fixed admittance based on 1 MVA / Ub^2
        ysvs = elmsvs.qmin * elmsvs.nncap + elmsvs.tcrqact + elmsvs.Qfixcap * elmsvs.nfixcap

        # SVS Range
        ymin = elmsvs.qmin * elmsvs.nxcap + elmsvs.Qfixcap * elmsvs.nfixcap
        ymax = elmsvs.tcrmax + elmsvs.Qfixcap * elmsvs.nfixcap
        ysvs = max(min(ysvs, ymax), ymin)

        control1_val = 0.0  # Active power injection of the SVS [MW]
        control2_val = np.abs(1.0 ** 2) * np.conj(ysvs)  # Reactive power injection of the SVS [MVAr]

        rate = max(np.abs(elmsvs.tcrmax), np.abs(elmsvs.qmin))
        kpd = 0.0  # Droop [%]
        u_setpoint = 1.0  # Voltage Setpoint [pu]

    vsc = dev.VSC(
        name=vsc_name,
        idtag=_ref_id(elmsvs.ID),
        active=not bool(elmsvs.outserv),
        bus_from=dc_bus,
        bus_to=ac_bus,
        rate=rate,
        alpha1=0.0,
        alpha2=0.0,
        alpha3=0.0,
        control1=control1,
        control2=control2,
        control1_val=control1_val,
        control2_val=control2_val,
        ysvs=ysvs,
        control2_droop=kpd,
        control2_droop_val=u_setpoint
    )

    return dc_bus, vsc

# def convert_dgs_to_controllable_shunt(elmsvs: ElmSvs,
#                            stacubic_dict: Dict[str, List[int]],
#                            buses: List[dev.Bus],
#                            logger: Logger,
#                            cubics_by_objid: Dict[str, List[StaCubic]],
#                            bus_by_term_id: Dict[str, dev.Bus]) -> Tuple[dev.Bus, dev.ControllableShunt]:
#     """
#     Convert ElmSvs (PowerFactory SVS/SVC) to VeraGrid ControllableShunt.
#
#     Notes
#     -----
#     - Electrical connectivity is obtained via StaCubic, consistent with other injected devices.
#     - If the DGS does not provide a voltage setpoint, Vset defaults to 1.0 p.u. (per project convention).
#     """
#     name = elmsvs.loc_name or f"ElmSvs_{_ref_id(elmsvs.ID)}"
#
#     bus = get_injection_bus(elm_id=elmsvs.ID,
#                             stacubic_dict=stacubic_dict,
#                             buses=buses,
#                             cubics_by_objid=cubics_by_objid,
#                             bus_by_term_id=bus_by_term_id)
#
#     bmin = float(elmsvs.qmin)
#     bmax = float(elmsvs.qmax)
#     vset = float(elmsvs.usetp)
#
#     # Build a small stepped model for B so the device can represent bmin / 0 / bmax when applicable
#     if bmin < 0.0 and bmax > 0.0:
#         b_steps = np.array([bmin, -bmin, bmax], dtype=float)
#         initial_step = 1
#     elif bmin == bmax:
#         b_steps = np.array([bmax], dtype=float)
#         initial_step = 0
#     else:
#         b_steps = np.array([bmin, (bmax - bmin)], dtype=float)
#         initial_step = 0
#
#     cshunt = dev.ControllableShunt(
#         name=name,
#         idtag=_ref_id(elmsvs.ID),
#         number_of_steps=int(len(b_steps)),
#         step=int(initial_step),
#         g_per_step=0.0,
#         b_per_step=0.0,
#         Bmin=bmin,
#         Bmax=bmax,
#         Gmin=0.0,
#         Gmax=0.0,
#         active=(elmsvs.outserv == 0),
#         vset=vset,
#         control_mode=ShuntControlMode.Continuous,
#         control_bus=bus
#     )
#
#     # Override step arrays to match the constructed block model
#     cshunt.b_steps = b_steps
#     cshunt.g_steps = np.zeros(len(b_steps), dtype=float)
#     cshunt.active_steps = np.ones(len(b_steps), dtype=int)
#
#     # Ensure B/G are coherent with the initial step after overriding arrays
#     cshunt.step = int(initial_step)
#
#     return bus, cshunt


def _pf_from_pq(p_mw: float, q_mvar: float, default: float = 0.8) -> float:
    """
    Compute power factor from (P, Q).
    """
    s = math.sqrt(p_mw * p_mw + q_mvar * q_mvar)
    if s <= 0.0:
        return default
    pf = abs(p_mw) / s
    return max(0.0, min(1.0, pf))


def _interpret_pu_limit(value: float,
                        baseMVA: float,
                        reference_abs: float,
                        logger: Logger,
                        name: str,
                        field: str) -> float:
    """
    Interpret a DGS limit that might be in p.u. (on Sbase) or in MW/MVAr.
    """
    v = value

    # If reference is small too, do not guess
    if abs(reference_abs) <= 5.0:
        return v

    # Heuristic: if |value| is small while reference magnitude is clearly in MW/MVAr,
    # then it is very likely a p.u. value and we scale by baseMVA.
    if abs(v) <= 5.0 and baseMVA > 0.0:

        logger.add_warning(
            f"Interpreting set point as not in p.u.",
            device=name,
            device_class="Generator",
            value=v * baseMVA
        )

        return v * baseMVA

    return v


def convert_dgs_to_generator(elmsym: ElmSym,
                             stacubic_dict: Dict[str, List[int]],
                             buses: List[dev.Bus],
                             typsym_dict: Dict[str, TypSym],
                             baseMVA: float,
                             logger: Logger,
                             cubics_by_objid: Dict[str, List[StaCubic]],
                             bus_by_term_id: Dict[str, dev.Bus],
                             parallel_index: int = 0,
                             parallel_count: int = 1) -> Tuple[dev.Bus, dev.Generator]:
    """
    Convert ElmSym to VeraGrid Generator.
    :param elmsym:
    :param stacubic_dict:
    :param buses:
    :param typsym_dict:
    :param baseMVA:
    :param logger:
    :param cubics_by_objid:
    :param bus_by_term_id:
    :return:
    """
    name = _get_non_empty_name(elmsym.loc_name, f"Gen_{_ref_id(elmsym.ID)}")
    name = _get_parallel_device_name(name, parallel_index, parallel_count)
    generator_idtag = _get_parallel_device_idtag(_ref_id(elmsym.ID), parallel_index, parallel_count)

    bus = get_injection_bus(elm_id=elmsym.ID,
                            stacubic_dict=stacubic_dict,
                            buses=buses,
                            cubics_by_objid=cubics_by_objid,
                            bus_by_term_id=bus_by_term_id)

    # Slack/reference machine indicator (PowerFactory exports ip_ctrl=1 on the slack generator)
    if int(elmsym.ip_ctrl) == 1:
        bus.is_slack = True

    # Resolve type
    typsym = typsym_dict.get(elmsym.typ_id, None)
    if typsym is None:
        typsym = typsym_dict.get(_ref_id(elmsym.typ_id), None)

    p_mw = float(elmsym.pgini)
    q_mvar = float(elmsym.qgini)

    # Voltage control
    vset = elmsym.usetp

    if elmsym.av_mode != "":
        if elmsym.av_mode == "constv":
            is_controlled = True
        else:
            is_controlled = False
    else:
        is_controlled = elmsym.iv_mode != 0

    # Power factor (used mainly when not controlled)
    pf = elmsym.cosgini
    if pf == 0.0 and typsym is not None:
        pf = typsym.cosn
    if pf == 0.0:
        pf = _pf_from_pq(p_mw=p_mw, q_mvar=q_mvar, default=0.8)

    # Nominal power
    snom = 9999.0
    if typsym is not None:
        snom = float(typsym.sgn)
    else:
        pass

    # Limits (q_min/q_max are often in p.u. on Sbase in DGS exports)
    qmin_raw = float(elmsym.q_min)
    qmax_raw = float(elmsym.q_max)
    if qmin_raw == 0.0 and typsym is not None:
        qmin_raw = float(typsym.q_min)
    else:
        pass
    if qmax_raw == 0.0 and typsym is not None:
        qmax_raw = float(typsym.q_max)
    else:
        pass

    qmin = _interpret_pu_limit(value=qmin_raw, baseMVA=baseMVA, reference_abs=abs(q_mvar),
                               logger=logger, name=name, field="q_min")
    qmax = _interpret_pu_limit(value=qmax_raw, baseMVA=baseMVA, reference_abs=abs(q_mvar),
                               logger=logger, name=name, field="q_max")

    # Optional P limits if present in schema
    pmin = float(elmsym.Pmin_uc)
    pmax = float(elmsym.Pmax_uc)

    # Interpret P limits if they look like p.u. too
    pmin = _interpret_pu_limit(value=pmin, baseMVA=baseMVA, reference_abs=abs(p_mw),
                               logger=logger, name=name, field="Pmin_uc")
    pmax = _interpret_pu_limit(value=pmax, baseMVA=baseMVA, reference_abs=abs(p_mw),
                               logger=logger, name=name, field="Pmax_uc")

    gen = dev.Generator(name=name,
                        idtag=generator_idtag,
                        P=p_mw,
                        Q=q_mvar,
                        power_factor=pf,
                        vset=vset,
                        is_controlled=is_controlled,
                        Qmin=qmin,
                        Qmax=qmax,
                        Snom=snom,
                        active=(elmsym.outserv == 0),
                        Pmin=pmin,
                        Pmax=pmax,
                        Sbase=baseMVA)

    # Optional sequence data from type (best-effort, may not exist in all exports)
    if typsym is not None:
        r1 = typsym.rstr
        x1 = typsym.xd

        if r1 != 0.0 or x1 != 0.0:
            gen.R1 = float(r1)
            gen.X1 = float(x1)
        else:
            pass

        if float(typsym.r0sy) != 0.0 or float(typsym.x0sy) != 0.0:
            gen.R0 = float(typsym.r0sy)
            gen.X0 = float(typsym.x0sy)
        else:
            pass

        if float(typsym.r2sy) != 0.0 or float(typsym.x2sy) != 0.0:
            gen.R2 = float(typsym.r2sy)
            gen.X2 = float(typsym.x2sy)
        else:
            pass

    return bus, gen


def convert_dgs_to_asm_generator(elmasm: ElmAsm,
                                 stacubic_dict: Dict[str, List[int]],
                                 buses: List[dev.Bus],
                                 typasmo_dict: Dict[str, TypAsmo],
                                 logger: Logger,
                                 cubics_by_objid: Dict[str, List[StaCubic]],
                                 bus_by_term_id: Dict[str, dev.Bus],
                                 parallel_index: int = 0,
                                 parallel_count: int = 1) -> Tuple[dev.Bus, dev.Generator]:
    """
    Convert ElmAsm (asynchronous machine) to VeraGrid Generator (asynchronous type).

    Important notes:
    - We model ElmAsm as a non-voltage-controlled Generator (PQ behavior).
    - The active power P is given as a parameter from PowerFactory, as the user defines it.
    - With the active power P, the asynchronous machine equivalent circuit is solve to find the slip.
    - When the slip is known, the algorithm computes the corresponding reactive power Q injection.
    - For more detail, refer to the VeraGrid documentation.
    """

    name = _get_non_empty_name(elmasm.loc_name, f"ElmAsm_{_ref_id(elmasm.ID)}")
    name = _get_parallel_device_name(name, parallel_index, parallel_count)
    generator_idtag = _get_parallel_device_idtag(_ref_id(elmasm.ID), parallel_index, parallel_count)

    # Bus resolution must be StaCubic-based (PowerFactory connectivity)
    bus = get_injection_bus(elm_id=elmasm.ID,
                            stacubic_dict=stacubic_dict,
                            buses=buses,
                            cubics_by_objid=cubics_by_objid,
                            bus_by_term_id=bus_by_term_id)

    if elmasm.i_mot == 0: # Check that the asynchronous machine is a Generator

        if elmasm.idfig == 0: # Also check that it is a Standard Asynchronous Machine

            if elmasm.bustp == 'AS' and elmasm.pmode == 0: # Finally, check the bus type and the power input mode

                P: float = float(elmasm.pgini) # AG active power P

                typasmo: TypAsmo | None = typasmo_dict.get(elmasm.typ_id, None) # AG type

                if typasmo is not None:

                    Sr = float(typasmo.sgn) * 1e-3 # Rated apparent power [MVA]
                    Rs = float(typasmo.rstr) # Stator resistance [pu]
                    Xs = float(typasmo.xstr) # Stator reactance [pu]
                    Xm = float(typasmo.xm) # Magnetising reactance [pu]
                    Rr = float(typasmo.rrtrA) # Rotor resistance [pu]
                    Xr = float(typasmo.xrtrA) # Rotor reactance [pu]

                    gen = dev.Generator(name=name,
                                        idtag=generator_idtag,
                                        P=P,
                                        power_factor=1.0,
                                        is_controlled=False,
                                        Snom=Sr,
                                        active=(elmasm.outserv == 0),
                                        Rs=Rs,
                                        Xs=Xs,
                                        Xm=Xm,
                                        Rr=Rr,
                                        Xr=Xr,
                                        tpe=GeneratorType.Asynchronous)



                else:
                    logger.add_warning(
                        msg=f"The Asynchronous Generator does not have an assigned type (TypAsmo).",
                        device=name,
                        device_class="ElmAsm",
                        value=typasmo
                    )

                    gen = dev.Generator(name=name,
                                        idtag=generator_idtag,
                                        P=P,
                                        power_factor=1.0,
                                        is_controlled=False,
                                        Snom=P,
                                        active=(elmasm.outserv == 0),
                                        tpe=GeneratorType.Asynchronous)

            else:
                logger.add_warning(
                    msg=f"Bus type is not AS or the input mode is not Electrical power.",
                    device=name,
                    device_class="ElmAsm",
                    value=elmasm.bustp
                )

                gen = dev.Generator(name=name,
                                    idtag=generator_idtag,
                                    P=0.0,
                                    power_factor=1.0,
                                    is_controlled=False,
                                    active=(elmasm.outserv == 0),
                                    tpe=GeneratorType.Asynchronous)

        else:
            logger.add_warning(
                msg=f"The AG is not an Standard Asynchronous Machine.",
                device=name,
                device_class="ElmAsm",
                value=elmasm.idfig
            )

            gen = dev.Generator(name=name,
                                idtag=generator_idtag,
                                P=0.0,
                                power_factor=1.0,
                                is_controlled=False,
                                active=(elmasm.outserv == 0),
                                tpe=GeneratorType.Asynchronous)

    else:
        logger.add_warning(
            msg=f"The asynchronous machine is not a generator, is a motor!",
            device=name,
            device_class="ElmAsm",
            value=elmasm.i_mot
        )

        gen = dev.Generator(name=name,
                            idtag=generator_idtag,
                            P=0.0,
                            power_factor=1.0,
                            is_controlled=False,
                            active=(elmasm.outserv == 0),
                            tpe=GeneratorType.Asynchronous)

    return bus, gen


def dgs_to_circuit(path: str, logger: Logger | None = None) -> dev.MultiCircuit:
    """

    :param path:
    :param logger:
    :return:
    """
    if logger is None:
        logger = Logger()

    dgs_grid = DgsCircuit()
    dgs_grid.parse_dgs(path)

    grid = dev.MultiCircuit()

    baseMVA = grid.Sbase

    # --- frequency ---
    if len(dgs_grid.elmnets) > 0:
        frnom = dgs_grid.elmnets[0].frnom
        if frnom is None:
            frequency = 50.0
        else:
            frequency = float(frnom)
    else:
        frequency = 50.0

    # StaCubic dictionaries
    stacubic_dict: Dict[str, List[int]] = dict()
    cubics_by_objid: Dict[str, List[StaCubic]] = dict()
    for cb in dgs_grid.stacubics:
        obj_id_raw = cb.obj_id
        obj_id = _ref_id(obj_id_raw)

        lst = stacubic_dict.get(obj_id, None)
        if lst is None:
            stacubic_dict[obj_id] = [cb.obj_bus]
        else:
            lst.append(cb.obj_bus)

        lst = cubics_by_objid.get(obj_id, None)
        if lst is None:
            cubics_by_objid[obj_id] = [cb]
        else:
            lst.append(cb)

        if obj_id_raw != obj_id:
            lst = stacubic_dict.get(obj_id_raw, None)
            if lst is None:
                stacubic_dict[obj_id_raw] = [cb.obj_bus]
            else:
                lst.append(cb.obj_bus)

            lst = cubics_by_objid.get(obj_id_raw, None)
            if lst is None:
                cubics_by_objid[obj_id_raw] = [cb]
            else:
                lst.append(cb)

    # graphics dictionary
    pos_by_objid: Dict[str, Tuple[float, float]] = dict()
    for g in dgs_grid.intgrfs:
        pos_by_objid[g.pDataObj] = (float(g.rCenterX), float(g.rCenterY))

    # Zones
    # In DGS, ElmTerm.cpZone is a pointer (p) to ElmZone.ID
    zone_by_id: Dict[str, dev.Zone] = dict()
    for elmzone in dgs_grid.elmzones:
        zid = _ref_id(elmzone.ID)
        if elmzone.loc_name != "":
            zone_name = elmzone.loc_name
        else:
            zone_name = f"Zone_{zid}"

        zone = dev.Zone(
            name=zone_name,
            idtag=zid,
            code="",
            latitude=0.0,
            longitude=0.0,
            area=None
        )

        grid.add_zone(zone)

        if zid is not None:
            zone_by_id[zid] = zone

    # Branch groups (ElmBranch)
    # ElmBranch is a hierarchical container in PowerFactory and does not define electrical connectivity.
    # We map it to VeraGridEngine BranchGroup for metadata/grouping only.
    branch_group_by_id: Dict[str, dev.BranchGroup] = dict()
    for elmbranch in dgs_grid.elmbranches:
        bid = _ref_id(elmbranch.ID)
        if elmbranch.loc_name != "":
            name = elmbranch.loc_name
        else:
            name = f"BranchGroup_{bid}"

        bg = dev.BranchGroup(
            name=name,
            code="",
            idtag=bid
        )

        grid.add_branch_group(obj=bg)

        if bid is not None and bid != "":
            branch_group_by_id[bid] = bg

    # Buses
    bus_by_term_id: Dict[str, dev.Bus] = dict()
    for elmterm in dgs_grid.elmterms:
        bus = convert_dgs_to_bus(elmterm=elmterm, pos_by_objid=pos_by_objid)
        grid.add_bus(obj=bus)
        tid = _ref_id(elmterm.ID)
        if tid is not None:
            bus_by_term_id[tid] = bus

    # Assign zone reference to buses
    # ElmTerm.cpZone -> ElmZone.ID -> dev.Zone
    for elmterm in dgs_grid.elmterms:
        tid = _ref_id(elmterm.ID)
        zid = _ref_id(elmterm.cpZone)

        # In some DGS exports (e.g., test_export_v6), cpZone is not present. In that case, skip assignment.
        if tid is not None and zid is not None and zid != "":
            bus = bus_by_term_id.get(tid, None)
            zone = zone_by_id.get(zid, None)

            if bus is not None:
                bus.zone = zone

    # Generator types
    typsym_dict: Dict[str, TypSym] = dict()
    for typsym in dgs_grid.typsyms:
        typsym_dict[typsym.ID] = typsym
        tid = _ref_id(typsym.ID)
        if tid is not None:
            typsym_dict[tid] = typsym

    # Asynchronous machine types (TypAsmo)
    typasmo_dict: Dict[str, TypAsmo] = dict()
    for typasmo in dgs_grid.typasmos:
        typasmo_dict[typasmo.ID] = typasmo
        tid = _ref_id(typasmo.ID)
        if tid is not None:
            typasmo_dict[tid] = typasmo

    typ_switch_dict: Dict[str, TypSwitch] = dict()
    for typ_switch in dgs_grid.typswitches:
        typ_switch_dict[typ_switch.ID] = typ_switch
        tid = _ref_id(typ_switch.ID)
        if tid is not None:
            typ_switch_dict[tid] = typ_switch

    # switches (PowerFactory/DGS: ElmCoup is the real device; StaCubic resolves connectivity)
    switch_by_cubic_id: Dict[str, StaSwitch] = build_switch_by_cubic_id(staswitchs=dgs_grid.staswitchs)

    vg_switches: List[dev.Switch] = convert_dgs_to_switches_from_elmcoup(
        elmcoups=dgs_grid.elmcoups,
        cubics_by_objid=cubics_by_objid,
        bus_by_term_id=bus_by_term_id,
        switch_by_cubic_id=switch_by_cubic_id,
        typ_switch_by_id=typ_switch_dict,
        sbase_mva=baseMVA,
        logger=logger
    )

    for sw in vg_switches:
        grid.add_switch(obj=sw)

    # Generators
    for elmsym in dgs_grid.elmsyms:
        parallel_count = _get_parallel_device_count(count=int(elmsym.ngnum))
        for parallel_index in range(parallel_count):
            bus, gen = convert_dgs_to_generator(
                elmsym=elmsym,
                stacubic_dict=stacubic_dict,
                buses=grid.buses,
                typsym_dict=typsym_dict,
                baseMVA=baseMVA,
                logger=logger,
                cubics_by_objid=cubics_by_objid,
                bus_by_term_id=bus_by_term_id,
                parallel_index=parallel_index,
                parallel_count=parallel_count
            )

            grid.add_generator(bus=bus, api_obj=gen)

    # Asynchronous machines (ElmAsm) -> model as PQ Generators
    for elmasm in dgs_grid.elmasms:
        parallel_count = _get_parallel_device_count(count=int(elmasm.ngnum))
        for parallel_index in range(parallel_count):
            bus, gen = convert_dgs_to_asm_generator(
                elmasm=elmasm,
                stacubic_dict=stacubic_dict,
                buses=grid.buses,
                typasmo_dict=typasmo_dict,
                logger=logger,
                cubics_by_objid=cubics_by_objid,
                bus_by_term_id=bus_by_term_id,
                parallel_index=parallel_index,
                parallel_count=parallel_count
            )

            grid.add_generator(bus=bus, api_obj=gen)

    # AC Voltage Sources
    for elmvac in dgs_grid.elmvacs:

        if elmvac.itype == 2:
            bus, load = convert_dgs_ward_equivalent_to_load(
                elmvac=elmvac,
                stacubic_dict=stacubic_dict,
                buses=grid.buses,
                logger=logger,
                cubics_by_objid=cubics_by_objid,
                bus_by_term_id=bus_by_term_id
            )

            grid.add_load(bus=bus, api_obj=load)

    # Loads
    for elmlod in dgs_grid.elmlods:
        bus, load = convert_dgs_to_load(
            elmlod=elmlod,
            stacubic_dict=stacubic_dict,
            buses=grid.buses,
            logger=logger,
            cubics_by_objid=cubics_by_objid,
            bus_by_term_id=bus_by_term_id
        )

        grid.add_load(bus=bus, api_obj=load)

    # Static Generators
    for elmgenstat in dgs_grid.elmgenstats:

        parallel_count = _get_parallel_device_count(count=int(elmgenstat.ngnum))

        for parallel_index in range(parallel_count):

            if elmgenstat.cCategory == 'Wind' and not bool(elmgenstat.outserv):
                dc_bus, vsc = convert_dgs_staticgen_to_vsc(
                    elmgenstat=elmgenstat,
                    stacubic_dict=stacubic_dict,
                    buses=grid.buses,
                    logger=logger,
                    cubics_by_objid=cubics_by_objid,
                    bus_by_term_id=bus_by_term_id,
                    parallel_index=parallel_index,
                    parallel_count=parallel_count
                )
                grid.add_bus(dc_bus)
                grid.add_vsc(vsc)

            elif elmgenstat.cCategory == 'HVDC Terminal':
                bus, gen = convert_dgs_staticgen_to_gen(
                    elmgenstat=elmgenstat,
                    stacubic_dict=stacubic_dict,
                    buses=grid.buses,
                    logger=logger,
                    cubics_by_objid=cubics_by_objid,
                    bus_by_term_id=bus_by_term_id,
                    parallel_index=parallel_index,
                    parallel_count=parallel_count
                )
                grid.add_generator(bus=bus, api_obj=gen)

            elif elmgenstat.cCategory == 'Storage':
                bus, battery = convert_dgs_staticgen_to_battery(
                    elmgenstat=elmgenstat,
                    stacubic_dict=stacubic_dict,
                    buses=grid.buses,
                    logger=logger,
                    cubics_by_objid=cubics_by_objid,
                    bus_by_term_id=bus_by_term_id,
                    parallel_index=parallel_index,
                    parallel_count=parallel_count
                )
                grid.add_battery(bus=bus, api_obj=battery)

            elif elmgenstat.av_mode == 'constv':
                bus, gen = convert_dgs_staticgen_to_gen(
                    elmgenstat=elmgenstat,
                    stacubic_dict=stacubic_dict,
                    buses=grid.buses,
                    logger=logger,
                    cubics_by_objid=cubics_by_objid,
                    bus_by_term_id=bus_by_term_id,
                    parallel_index=parallel_index,
                    parallel_count=parallel_count
                )
                grid.add_generator(bus=bus, api_obj=gen)

            else: # Standard Constant Q Static Generator
                bus, stagen = convert_dgs_to_static_gen(
                    elmgenstat=elmgenstat,
                    stacubic_dict=stacubic_dict,
                    buses=grid.buses,
                    logger=logger,
                    cubics_by_objid=cubics_by_objid,
                    bus_by_term_id=bus_by_term_id,
                    parallel_index=parallel_index,
                    parallel_count=parallel_count
                )

                grid.add_static_generator(bus=bus, api_obj=stagen)

    # external grids
    for eg in dgs_grid.elmxnets:

        short_circuit = True

        if short_circuit:
            bus, gen = convert_dgs_external_grid_to_generator(
                elmxnet=eg,
                stacubic_dict=stacubic_dict,
                buses=grid.buses,
                logger=logger,
                cubics_by_objid=cubics_by_objid,
                bus_by_term_id=bus_by_term_id,
                Sbase=grid.Sbase,
            )
            grid.add_generator(bus=bus, api_obj=gen)

        else:
            bus, ext_grd = convert_dgs_to_external_grid(
                elmxnet=eg,
                stacubic_dict=stacubic_dict,
                buses=grid.buses,
                logger=logger,
                cubics_by_objid=cubics_by_objid,
                bus_by_term_id=bus_by_term_id
            )
            grid.add_external_grid(bus=bus, api_obj=ext_grd)

    # Shunts (fixed)
    for elmshnt in dgs_grid.elmshnts:
        if int(elmshnt.ncapx) > 1:
            bus, cshunt = convert_dgs_to_controllable_shunt_from_elmshnt(
                elmshnt=elmshnt,
                stacubic_dict=stacubic_dict,
                buses=grid.buses,
                logger=logger,
                cubics_by_objid=cubics_by_objid,
                bus_by_term_id=bus_by_term_id,
                frequency=frequency
            )

            grid.add_controllable_shunt(bus=bus, api_obj=cshunt)
        else:
            bus, shunt = convert_dgs_to_shunt(
                elmshnt=elmshnt,
                stacubic_dict=stacubic_dict,
                buses=grid.buses,
                logger=logger,
                cubics_by_objid=cubics_by_objid,
                bus_by_term_id=bus_by_term_id,
                frequency=frequency
            )

            grid.add_shunt(bus=bus, api_obj=shunt)

    # Controllable shunts (SVC/SVS)
    for elmsvs in dgs_grid.elmsvss:
        dc_bus, vsc = convert_dgs_svs_to_vsc(
            elmsvs=elmsvs,
            stacubic_dict=stacubic_dict,
            buses=grid.buses,
            logger=logger,
            cubics_by_objid=cubics_by_objid,
            bus_by_term_id=bus_by_term_id
        )

        grid.add_bus(dc_bus)
        grid.add_vsc(vsc)

        # bus, cshunt = convert_dgs_to_controllable_shunt(
        #     elmsvs=elmsvs,
        #     stacubic_dict=stacubic_dict,
        #     buses=grid.buses,
        #     logger=logger,
        #     cubics_by_objid=cubics_by_objid,
        #     bus_by_term_id=bus_by_term_id
        # )

        # grid.add_controllable_shunt(bus=bus, api_obj=cshunt)

    # Loads (LV)
    if len(dgs_grid.elmlodlvs) > 0 or len(dgs_grid.elmlodlvps) > 0:

        logger.add_warning(
            f"ElmLodlv/ElmLodlvp found but no P/Q fields available in DGS schema",
            device_class="ElmLodlv/ElmLodlvp",
        )

    # Line types
    typlne_dict: Dict[str, dev.SequenceLineType] = dict()
    for typlne in dgs_grid.typlnes:
        seq_lne = convert_dgs_to_sequence_line(typlne=typlne)
        grid.add_sequence_line(obj=seq_lne)
        typlne_dict[typlne.ID] = seq_lne

    # Conductor / tower catalogues (overhead line modelling)
    typcon_raw_dict: Dict[str, TypCon] = dict()
    wire_type_dict: Dict[str, Wire] = dict()
    for typcon in dgs_grid.typcons:
        # Map both raw pointer and ref-id variant
        cid = _ref_id(typcon.ID)
        if cid is None:
            continue
        typcon_raw_dict[cid] = typcon
        typcon_raw_dict[typcon.ID] = typcon

        wire = convert_dgs_to_wire(typcon=typcon)
        wire_type_dict[cid] = wire
        wire_type_dict[typcon.ID] = wire

        # MultiCircuit stores these templates under Assets (catalogue)
        grid.wire_types.append(wire)

    overhead_line_type_dict: Dict[str, OverheadLineType] = dict()
    for typtow in dgs_grid.typtows:
        tow_id = _ref_id(typtow.ID)
        if tow_id is None:
            continue

        ohl_type = convert_dgs_to_overhead_line_type(
            typtow=typtow,
            typcon_by_id=typcon_raw_dict,
            wire_by_id=wire_type_dict,
            default_frequency_hz=frequency,
        )
        overhead_line_type_dict[tow_id] = ohl_type
        overhead_line_type_dict[typtow.ID] = ohl_type

        grid.overhead_line_types.append(ohl_type)

    # Transformer types
    typtr2_dict: Dict[str, dev.TransformerType] = dict()
    typtr2_raw_dict: Dict[str, TypTr2] = dict()
    for typtr2 in dgs_grid.typtr2s:
        tpe = convert_dgs_to_transformer_type(typtr2=typtr2)
        grid.add_transformer_type(obj=tpe)
        typtr2_dict[typtr2.ID] = tpe
        typtr2_raw_dict[typtr2.ID] = typtr2
        tid = _ref_id(typtr2.ID)
        if tid is not None:
            typtr2_dict[tid] = tpe
            typtr2_raw_dict[tid] = typtr2

    # Transformer types (3W)
    typtr3_dict: Dict[str, TypTr3] = dict()
    for typtr3 in dgs_grid.typtr3s:
        typtr3_dict[typtr3.ID] = typtr3
        tid = _ref_id(typtr3.ID)
        if tid is not None:
            typtr3_dict[tid] = typtr3

    # Series reactance / impedance types (raw DGS objects, used as templates)
    typsind_raw_dict: Dict[str, TypSind] = dict()
    for typsind in dgs_grid.typsinds:
        typsind_raw_dict[typsind.ID] = typsind
        tid = _ref_id(typsind.ID)
        if tid is not None:
            typsind_raw_dict[tid] = typsind

    # ------------------------------------------------------------
    # Fallback map: ElmLne.ID -> typ_id from ElmLnesec
    # Some PowerFactory exports omit ElmLne.typ_id and store it in ElmLnesec.typ_id.
    # In some cases, ElmLnesec.fold_id references an IntFolder chain; we climb until we reach an ElmLne.
    # ------------------------------------------------------------
    line_type_by_line_id: Dict[str, str] = dict()
    line_sections_by_line_id: Dict[str, List[ElmLnesec]] = dict()

    # Fast lookup of line IDs (raw and normalized)
    line_ids: Set[str] = set()
    for elmlne in dgs_grid.elmlnes:
        if elmlne.ID != "":
            line_ids.add(elmlne.ID)
            rid = _ref_id(elmlne.ID)
            if rid is not None and rid != "":
                line_ids.add(rid)

    # Folder -> parent pointer map (raw and normalized keys)
    folder_parent: Dict[str, str] = dict()
    for folder in dgs_grid.intfolders:
        if folder.ID == "":
            continue
        folder_parent[folder.ID] = folder.fold_id
        fid = _ref_id(folder.ID)
        if fid is not None and fid != "":
            folder_parent[fid] = folder.fold_id

    line_id_by_loc_name: Dict[str, str] = _get_unique_name_mapping(
        lines=dgs_grid.elmlnes,
        use_characteristic_name=False
    )
    line_id_by_chr_name: Dict[str, str] = _get_unique_name_mapping(
        lines=dgs_grid.elmlnes,
        use_characteristic_name=True
    )

    # Resolve each section to its owning line by climbing the folder chain
    for sec in dgs_grid.elmlnesecs:
        if sec.typ_id == "":
            continue

        owner_line_id = _resolve_line_section_owner_id(
            section=sec,
            line_ids=line_ids,
            folder_parent=folder_parent,
            line_id_by_loc_name=line_id_by_loc_name,
            line_id_by_chr_name=line_id_by_chr_name
        )
        if owner_line_id == "":
            logger.add_warning(
                "Could not resolve owning line for line section.",
                device=sec.loc_name,
                device_class="ElmLnesec",
                value=str(sec.ID)
            )
            continue
        else:
            pass

        typ_id = _ref_id(sec.typ_id) or sec.typ_id
        line_type_by_line_id[owner_line_id] = typ_id

        normalized_owner_id = _ref_id(owner_line_id) or owner_line_id
        line_type_by_line_id[normalized_owner_id] = typ_id

        owned_sections = line_sections_by_line_id.get(normalized_owner_id, None)
        if owned_sections is None:
            line_sections_by_line_id[normalized_owner_id] = list()
            owned_sections = line_sections_by_line_id[normalized_owner_id]
        else:
            pass
        owned_sections.append(sec)

    # ------------------------------------------------------------
    # Tower coupling helper: ElmTow may define the line template (TypTow) instead of ElmLne.typ_id.
    # We build a direct mapping Line.ID -> OverheadLineType so convert_dgs_to_line can proceed
    # even when typ_id is missing, and apply the proper template immediately.
    # ------------------------------------------------------------
    tower_template_by_line_id: Dict[str, OverheadLineType] = dict()
    for elmtow in dgs_grid.elmtows:
        if len(elmtow.pGeo) == 0:
            continue
        geo_ptr = elmtow.pGeo[0]
        if geo_ptr is None or geo_ptr == "":
            continue

        geo_id = _ref_id(geo_ptr)
        ohl_type = overhead_line_type_dict.get(geo_id, None)
        if ohl_type is None:
            ohl_type = overhead_line_type_dict.get(geo_ptr, None)
        if ohl_type is None:
            continue

        for line_ptr in elmtow.plines:
            if line_ptr is None or line_ptr == "":
                continue
            tower_template_by_line_id[line_ptr] = ohl_type
            lid = _ref_id(line_ptr)
            if lid is not None and lid != "":
                tower_template_by_line_id[lid] = ohl_type

    # lines
    line_by_dgs_id: Dict[str, List[dev.Line]] = dict()
    for elmlne in dgs_grid.elmlnes:

        # ------------------------------------------------------------
        # Pre-check: skip orphan lines (no StaCubic connectivity)
        # This avoids failing on missing typ_id for elements that are not
        # electrically connected in the exported DGS (e.g., '*_2a' duplicates).
        # ------------------------------------------------------------
        term_ids: List[str] = get_terminal_ids(element_id=elmlne.ID, cubics_by_objid=cubics_by_objid)
        if len(term_ids) != 2:
            bus_ids: List[int] | None = stacubic_dict.get(_ref_id(elmlne.ID), None)
            if bus_ids is None or len(bus_ids) != 2:

                logger.add_warning(
                    f"not connected to exactly 2 terminals",
                    device=f"{elmlne.loc_name}' (ID={elmlne.ID}) ",
                    device_class="ElmLne",
                    value=len(term_ids),
                    expected_value="2"
                )

                continue

        parallel_count = _get_parallel_device_count(count=int(elmlne.nlnum))
        for parallel_index in range(parallel_count):
            line = convert_dgs_to_line(
                lne=elmlne,
                buses=grid.buses,
                stacubic_dict=stacubic_dict,
                templates_dict=typlne_dict,
                overhead_line_type_dict=overhead_line_type_dict,
                line_type_by_line_id=line_type_by_line_id,
                line_sections_by_line_id=line_sections_by_line_id,
                tower_template_by_line_id=tower_template_by_line_id,
                freq=frequency,
                baseMVA=baseMVA,
                logger=logger,
                cubics_by_objid=cubics_by_objid,
                bus_by_term_id=bus_by_term_id,
                parallel_index=parallel_index,
                parallel_count=parallel_count
            )

            # Optional grouping metadata...
            fold_id = _ref_id(elmlne.fold_id)
            if fold_id is not None and fold_id != "":
                bg = branch_group_by_id.get(fold_id)
                if bg is not None:
                    line.group = bg

            grid.add_line(obj=line, logger=logger)

            lid_raw = elmlne.ID
            lid = _ref_id(lid_raw)
            if lid is not None:
                line_by_dgs_id.setdefault(lid, list()).append(line)
            if lid_raw is not None and lid_raw != "":
                line_by_dgs_id.setdefault(lid_raw, list()).append(line)

    # Tower coupling (ElmTow): bind the created Line objects to OverheadLineType templates.
    # IMPORTANT: the Line objects must exist first (created above).
    for elmtow in dgs_grid.elmtows:
        if int(elmtow.outserv) != 0:
            continue

        if len(elmtow.pGeo) == 0:
            logger.add_warning(
                f"no pGeo specified, skipping tower binding",
                device=f"{elmtow.loc_name}' (ID={elmtow.ID}) ",
                device_class="ElmTow"
            )

            continue

        geo_ptr = elmtow.pGeo[0]
        if geo_ptr is None:

            logger.add_warning(
                f"pGeo[0] is empty, skipping tower binding",
                device=f"{elmtow.loc_name}' (ID={elmtow.ID}) ",
                device_class="ElmTow"
            )

            continue

        geo_id = _ref_id(geo_ptr)
        ohl_type = overhead_line_type_dict.get(geo_id)
        if ohl_type is None:
            ohl_type = overhead_line_type_dict.get(geo_ptr)

        if ohl_type is None:

            logger.add_warning(
                f"referenced tower type not found",
                device=f"{elmtow.loc_name}' (ID={elmtow.ID}) ",
                device_class="ElmTow",
                value=str(geo_ptr)
            )

            continue

        for idx, line_ptr in enumerate(elmtow.plines):
            if line_ptr is None:
                continue

            line_id = _ref_id(line_ptr)
            api_lines = line_by_dgs_id.get(line_id, list())
            if len(api_lines) == 0:
                api_lines = line_by_dgs_id.get(line_ptr, list())

            if len(api_lines) == 0:

                logger.add_warning(
                    f"referenced line type not found",
                    device=f"{elmtow.loc_name}' (ID={elmtow.ID}) ",
                    device_class="ElmTow",
                    value=str(line_ptr)
                )

                continue

            circuit_idx = int(idx) + 1

            for api_line in api_lines:
                try:
                    api_line.set_circuit_idx(val=circuit_idx, obj=ohl_type)
                    api_line.apply_template(obj=ohl_type, Sbase=baseMVA, freq=frequency, logger=logger)
                except ValueError as e:
                    logger.add_warning(str(e), device_class="ElmLne", device=api_line.name)

    # common impedances
    for elmzpu in dgs_grid.elmzpus:
        sr = convert_dgs_common_impedance_to_series_reactance(
            element=elmzpu,
            buses=grid.buses,
            bus_by_terminal_id=bus_by_term_id,
            stacubic_dict=stacubic_dict,
            cubics_by_obj_id=cubics_by_objid,
            logger=logger,
            Sbase_vg=baseMVA
        )
        # MultiCircuit supports generic branch insertion
        # Optional grouping metadata: assign BranchGroup based on the DGS hierarchical folder reference.
        # IMPORTANT: this does not affect electrical connectivity.
        fold_id = _ref_id(elmzpu.fold_id)
        if fold_id is not None and fold_id != "":
            bg = branch_group_by_id.get(fold_id)
            if bg is not None:
                sr.group = bg

        grid.add_series_reactance(sr)


    # series capacitors
    for elmscap in dgs_grid.elmscaps:
        sr = convert_dgs_series_capacitor_to_reactance(
            element=elmscap,
            buses=grid.buses,
            bus_by_terminal_id=bus_by_term_id,
            stacubic_dict=stacubic_dict,
            cubics_by_obj_id=cubics_by_objid,
            logger=logger,
            sbase_mva=baseMVA
        )
        # MultiCircuit supports generic branch insertion
        # Optional grouping metadata: assign BranchGroup based on the DGS hierarchical folder reference.
        # IMPORTANT: this does not affect electrical connectivity.
        fold_id = _ref_id(elmscap.fold_id)
        if fold_id is not None and fold_id != "":
            bg = branch_group_by_id.get(fold_id)
            if bg is not None:
                sr.group = bg

        grid.add_series_reactance(obj=sr)


    # series reactances / impedances
    for elmsind in dgs_grid.elmsinds:
        sr = convert_dgs_to_series_reactance(
            element=elmsind,
            buses=grid.buses,
            bus_by_terminal_id=bus_by_term_id,
            stacubic_dict=stacubic_dict,
            cubics_by_obj_id=cubics_by_objid,
            typsind_dict=typsind_raw_dict,
            logger=logger,
            sbase_mva=baseMVA
        )
        # MultiCircuit supports generic branch insertion
        # Optional grouping metadata: assign BranchGroup based on the DGS hierarchical folder reference.
        # IMPORTANT: this does not affect electrical connectivity.
        fold_id = _ref_id(elmsind.fold_id)
        if fold_id is not None and fold_id != "":
            bg = branch_group_by_id.get(fold_id)
            if bg is not None:
                sr.group = bg

        grid.add_series_reactance(obj=sr)


    # Transformers 2W
    for elmtr2 in dgs_grid.elmtr2s:
        parallel_count = _get_parallel_device_count(count=int(elmtr2.ntnum))
        for parallel_index in range(parallel_count):
            trafo = convert_dgs_to_transformer(
                tr2=elmtr2,
                buses=grid.buses,
                stacubic_dict=stacubic_dict,
                templates_dict=typtr2_dict,
                typtr2_dict=typtr2_raw_dict,
                freq=frequency,
                baseMVA=baseMVA,
                logger=logger,
                cubics_by_objid=cubics_by_objid,
                bus_by_term_id=bus_by_term_id,
                switch_by_cubic_id=switch_by_cubic_id,
                parallel_index=parallel_index,
                parallel_count=parallel_count
            )

            # Optional grouping metadata: assign BranchGroup based on the DGS hierarchical folder reference.
            # IMPORTANT: this does not affect electrical connectivity.
            fold_id = _ref_id(elmtr2.fold_id)
            if fold_id is not None and fold_id != "":
                bg = branch_group_by_id.get(fold_id)
                if bg is not None:
                    trafo.group = bg

            grid.add_transformer2w(obj=trafo)

    # Transformers 3W
    for elmtr3 in dgs_grid.elmtr3s:
        # Skip invalid 3W transformers: missing template reference or not fully connected
        tr3_typ_id: str | None = _ref_id(elmtr3.typ_id)
        if tr3_typ_id is None or tr3_typ_id == "":

            logger.add_warning(
                f"missing typ_id (no TypTr3 reference in DGS)",
                device=f"{elmtr3.loc_name}' (ID={elmtr3.ID}) ",
                device_class="Transformer3W",
            )

            continue

        if typtr3_dict.get(tr3_typ_id, None) is None:
            logger.add_warning(
                f"referenced TypTr3 not found",
                device=f"{elmtr3.loc_name}' (ID={elmtr3.ID}) ",
                device_class="Transformer3W",
                value=str(elmtr3.typ_id)
            )
            continue
        else:
            pass

        term_ids: List[str] = get_terminal_ids(element_id=elmtr3.ID, cubics_by_objid=cubics_by_objid)
        if len(term_ids) != 3:
            bus_ids: List[int] | None = stacubic_dict.get(_ref_id(elmtr3.ID), None)
            if bus_ids is None or len(bus_ids) != 3:

                logger.add_warning(
                    f"Not connected to exactly 3 terminals",
                    device=f"{elmtr3.loc_name}' (ID={elmtr3.ID}) ",
                    device_class="Transformer3W",
                )
                continue

        parallel_count = _get_parallel_device_count(count=int(elmtr3.nt3nm))
        for parallel_index in range(parallel_count):
            trafo3w: dev.Transformer3W = convert_dgs_to_transformer3w(
                tr3=elmtr3,
                buses=grid.buses,
                stacubic_dict=stacubic_dict,
                templates_dict=typtr3_dict,
                baseMVA=baseMVA,
                logger=logger,
                cubics_by_objid=cubics_by_objid,
                bus_by_term_id=bus_by_term_id,
                switch_by_cubic_id=switch_by_cubic_id,
                parallel_index=parallel_index,
                parallel_count=parallel_count
            )

            grid.add_bus(obj=trafo3w.bus0)
            # Optional grouping metadata: assign BranchGroup based on the DGS hierarchical folder reference.
            # IMPORTANT: this does not affect electrical connectivity.
            fold_id = _ref_id(elmtr3.fold_id)
            if fold_id is not None and fold_id != "":
                bg = branch_group_by_id.get(fold_id)
                if bg is not None:
                    trafo3w.winding1.group = bg
                    trafo3w.winding2.group = bg
                    trafo3w.winding3.group = bg

            grid.add_transformer3w(obj=trafo3w)

    return grid


"""
Funcion usada antes para los switches a partir de los StaSwitch. Era erronea, deviamos parsearlos a partir de los ElmCoup:
def convert_dgs_to_switches_by_elements(cubics_by_objid: Dict[str, List[StaCubic]],
                                        switch_by_cubic_id: Dict[str, StaSwitch],
                                        bus_by_term_id: Dict[str, dev.Bus],
                                        tr3_ids: Set[str],
                                        logger: Logger) -> List[dev.Switch]:

    Create one VeraGrid Switch per 2-terminal element (line/trafo/etc.) when both ends have StaSwitch.
    This function filters out "internal" PowerFactory switches (closed and without type) unless
    they belong to a 3-Winding Transformer.

    :param cubics_by_objid: Dictionary mapping Element ID -> List of Cubicles
    :param switch_by_cubic_id: Dictionary mapping Cubic ID -> Switch Object
    :param bus_by_term_id: Dictionary mapping Terminal ID -> Bus Object
    :param tr3_ids: Set of IDs belonging to 3-Winding Transformers (to force visibility)
    :param logger: Logger object
    :return: List of VeraGrid Switch objects

    switches: List[dev.Switch] = list()

    for obj_id, cubics in cubics_by_objid.items():
        obj_id_ref: str | None = _ref_id(obj_id)
        if obj_id_ref is None or obj_id_ref == "":
            continue

        # Avoid duplicates because cubics_by_objid may contain both raw and ref keys
        if obj_id != obj_id_ref:
            continue

        ends: List[Tuple[dev.Bus, StaSwitch]] = list()

        for cb in cubics:
            cb_id: str | None = _ref_id(cb.ID)
            if cb_id is None or cb_id == "":
                continue

            stasw: StaSwitch | None = switch_by_cubic_id.get(cb_id, None)
            if stasw is None:
                continue

            term_id: str | None = _ref_id(cb.fold_id)
            if term_id is None or term_id == "":
                continue

            bus: dev.Bus = bus_by_term_id[term_id]
            ends.append((bus, stasw))

        if len(ends) != 2:
            continue

        bus_from: dev.Bus = ends[0][0]
        bus_to: dev.Bus = ends[1][0]

        # Skip degenerate cases
        if bus_from is bus_to:
            continue

        sw_a: StaSwitch = ends[0][1]
        sw_b: StaSwitch = ends[1][1]

        # Physical state
        is_closed: bool = (int(sw_a.on_off) != 0) and (int(sw_b.on_off) != 0)

        # --- VISIBILITY FILTER ---
        # 1. Check if switches have a specific Type assigned (Real Device)
        #    In DGS, an empty type usually means it is a logical connector.
        has_type_a: bool = (sw_a.typ_id is not None) and (str(sw_a.typ_id).strip() != "")
        has_type_b: bool = (sw_b.typ_id is not None) and (str(sw_b.typ_id).strip() != "")
        is_real_device: bool = has_type_a or has_type_b

        # 2. Check if it belongs to a 3-Winding Transformer (User requirement)
        is_tr3: bool = obj_id_ref in tr3_ids

        # 3. Logic: Show if OPEN or REAL DEVICE or TR3. Hide otherwise.
        should_render: bool = (not is_closed) or is_real_device or is_tr3

        if not should_render:
            continue
        # -------------------------

        # Calculate graphical position (midpoint between buses)
        mid_x: float = (float(bus_from.x) + float(bus_to.x)) / 2.0
        mid_y: float = (float(bus_from.y) + float(bus_to.y)) / 2.0

        normal_open: bool = not is_closed
        graphic_type: SwitchGraphicType = _convert_pf_switch_graphic_type(iuse=sw_a.iUse, ausage=sw_a.aUsage)

        sw = dev.Switch(bus_from=bus_from,
                        bus_to=bus_to,
                        name=f"SW_{obj_id_ref}",
                        idtag=obj_id_ref,
                        code=sw_a.typ_id,
                        active=is_closed,
                        normal_open=normal_open,
                        retained=False,
                        rated_current=0.0,
                        graphic_type=graphic_type,
                        # x=mid_x,
                        # y=mid_y
                        )

        switches.append(sw)

    return switches

"""
# TODO: There might be an error with 3W trafos impedances
