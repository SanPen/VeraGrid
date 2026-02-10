# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
import math
import re
import numpy as np
from typing import Dict, List, Tuple, Set
from VeraGridEngine.enumerations import WindingType, SwitchGraphicType
import VeraGridEngine.Devices as dev
from VeraGridEngine.Devices.Branches.wire import Wire
from VeraGridEngine.Devices.Branches.overhead_line_type import OverheadLineType, WireInTower
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.dgs.dgs_circuit import DgsCircuit
from VeraGridEngine.IO.dgs.dgs_objects import *


def _ref_id(x: str | None) -> str | None:
    """
    Extract the referenced object ID from PowerFactory/DGS pointer strings.
    DGS pointers may contain a path separated by backslashes. We keep only the last token.
    """
    if x is None:
        return None
    s = str(x)
    return s.split("\\")[-1] if "\\" in s else s


def get_terminal_ids(element_id: str, cubics_by_objid: Dict[str, List[StaCubic]]) -> List[str]:
    """
    Get the connected terminal IDs (ElmTerm.ID) for a given branch/injection element ID
    using the StaCubic.fold_id -> ElmTerm.ID mapping.
    """
    cbs = cubics_by_objid.get(_ref_id(element_id), [])
    # StaCubic.fold_id typically points to the parent ElmTerm of the connection
    return [_ref_id(cb.fold_id) for cb in cbs if _ref_id(cb.fold_id) is not None and _ref_id(cb.fold_id) != ""]


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
        xpos=float(x),
        ypos=float(-y),
        active=(int(elmterm.outserv or 0) == 0),
    )

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
        return [(0.0, 0.0)]
    if spacing_m <= 0.0:
        return [(0.0, 0.0)]

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
    name = typcon.loc_name if typcon.loc_name is not None and str(typcon.loc_name).strip() != '' else f"Wire_{tid}"

    # PowerFactory: diatub may be 0/empty for non-tubular conductors.
    diatub = float(typcon.diatub)
    is_tube = diatub > 0.0

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
    name = typtow.loc_name if typtow.loc_name is not None and str(typtow.loc_name).strip() != '' else f"Tower_{tid}"

    # Frequency / earth parameters
    freq = float(typtow.frnom) if typtow.frnom is not None and float(typtow.frnom) > 0.0 else float(default_frequency_hz)
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

    vnom = max(v_candidates) if len(v_candidates) > 0 else 0.0

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
                              name=typtr2.loc_name)

    conn_hv = _convert_pf_tr2_connection(typtr2.tr2cn_h)
    conn_lv = _convert_pf_tr2_connection(typtr2.tr2cn_l)

    if conn_hv is not None:
        tpe.conn_hv = conn_hv

    if conn_lv is not None:
        tpe.conn_lv = conn_lv

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

    # Equal-Vnom transformers: HV/LV is ambiguous. Make ordering deterministic so that
    # RAW and DGS imports end up with the same 'from/to' orientation.
    m = re.search(r"_(\d+)_(\d+)(?:_|$)", tr_name or "")
    if m:
        i = int(m.group(1))
        j = int(m.group(2))

        sa = (str(bus_a.name or "").strip().split() or [""])[0]
        sb = (str(bus_b.name or "").strip().split() or [""])[0]
        ida = int(sa) if sa.isdigit() else None
        idb = int(sb) if sb.isdigit() else None

        if ida == j and idb == i:
            return bus_b, bus_a
        if ida == i and idb == j:
            return bus_a, bus_b

    logger.add_warning(f"Transformer '{tr_name}': HV/LV ambiguous (equal Vnom={va}). Keeping original order.")
    return bus_a, bus_b

    if va > vb:
        return bus_a, bus_b
    if vb > va:
        return bus_b, bus_a

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
        logger.add_warning(f"Transformer3W '{tr_name}': one or more buses have Vnom=0.0 (va={va}, vb={vb}, vc={vc}).")
        return bus_a, bus_b, bus_c

    buses: List[dev.Bus] = [bus_a, bus_b, bus_c]
    buses_sorted: List[dev.Bus] = sorted(buses, key=lambda b: float(b.Vnom), reverse=True)

    v0 = float(buses_sorted[0].Vnom)
    v1 = float(buses_sorted[1].Vnom)
    v2 = float(buses_sorted[2].Vnom)

    if v0 == v1 or v1 == v2:
        logger.add_warning(
            f"Transformer3W '{tr_name}': HV/MV/LV ambiguous (Vnom={v0}, {v1}, {v2}). Keeping Vnom-based ordering."
        )

    return buses_sorted[0], buses_sorted[1], buses_sorted[2]


def convert_dgs_to_transformer(tr2: ElmTr2,
                               buses: List[dev.Bus],
                               stacubic_dict: Dict[str, List[int]],
                               templates_dict: Dict[str, dev.TransformerType],
                               typtr2_dict: Dict[str, TypTr2],
                               freq: float,
                               baseMVA: float,
                               logger: Logger,
                               cubics_by_objid: Dict[str, List[StaCubic]],
                               bus_by_term_id: Dict[str, dev.Bus]) -> dev.Transformer2W:
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
    typtr2_raw = typtr2_dict.get(tr2.typ_id, None)

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

    bus_hv, bus_lv = _order_hv_lv(bus_a=bus_from,
                                  bus_b=bus_to,
                                  logger=logger,
                                  tr_name=tr2.loc_name)

    trafo = dev.Transformer2W(bus_from=bus_hv,
                              bus_to=bus_lv,
                              name=tr2.loc_name,
                              active=not tr2.outserv,
                              template=template)

    trafo.apply_template(obj=template, Sbase=baseMVA, logger=logger)

    #   - TypTr2.dutap   : tap step in percent (%)
    #   - TypTr2.nntap0  : neutral position (integer)
    #   - TypTr2.ntpmn   : minimum position (integer)
    #   - TypTr2.ntpmx   : maximum position (integer)
    #   - TypTr2.tap_side: side where the tap-changer is located (typically 0=HV, 1=LV)
    #   - ElmTr2.nntap   : current position (integer)

    step: float = float(typtr2_raw.dutap) / 100.0
    n0: int = int(typtr2_raw.nntap0)
    n: int = int(tr2.nntap)

    tap: float = 1.0 + (n - n0) * step
    tap_min: float = 1.0 + (int(typtr2_raw.ntpmn) - n0) * step
    tap_max: float = 1.0 + (int(typtr2_raw.ntpmx) - n0) * step

    # Ensure ordering for min/max (in case data is inverted in the source)
    if tap_min > tap_max:
        tap_min, tap_max = tap_max, tap_min

    # If tap-changer is on LV side, move it to HV side by inversion to match VeraGrid model
    if int(typtr2_raw.tap_side) != 0:
        tap = 1.0 / tap
        tap_min_i: float = 1.0 / tap_min
        tap_max_i: float = 1.0 / tap_max
        tap_min = min(tap_min_i, tap_max_i)
        tap_max = max(tap_min_i, tap_max_i)

    trafo.tap_module = tap
    trafo.tap_module_min = tap_min
    trafo.tap_module_max = tap_max
    # ---------------------------------------------------------------

    return trafo


def convert_dgs_to_transformer3w(tr3: ElmTr3,
                                 buses: List[dev.Bus],
                                 stacubic_dict: Dict[str, List[int]],
                                 templates_dict: Dict[str, TypTr3],
                                 baseMVA: float,
                                 logger: Logger,
                                 cubics_by_objid: Dict[str, List[StaCubic]],
                                 bus_by_term_id: Dict[str, dev.Bus]) -> dev.Transformer3W:
    """
    Convert ElmTr3 to Transformer3W using TypTr3 as template for design values.
    """
    template = templates_dict.get(tr3.typ_id, None)
    if template is None:
        template = templates_dict.get(_ref_id(tr3.typ_id), None)

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

    trafo3w = dev.Transformer3W(name=tr3.loc_name,
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
                f"ElmCoup '{coup.loc_name}' (ID={coup.ID}) skipped: "
                f"expected 2 terminals, got {len(term_ids)}."
            )
            continue

        bus_from: dev.Bus = bus_by_term_id[term_ids[0]]
        bus_to: dev.Bus = bus_by_term_id[term_ids[1]]

        # Skip degenerate cases
        if bus_from is bus_to:
            logger.add_warning(
                f"ElmCoup '{coup.loc_name}' (ID={coup.ID}) skipped: both ends connect to the same bus."
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
                    f"ElmCoup '{coup.loc_name}' (ID={coup.ID}) state differs from StaSwitch "
                    f"'{stasw.loc_name}' (ID={stasw.ID}): "
                    f"ElmCoup.on_off={int(coup.on_off)} vs StaSwitch.on_off={int(stasw.on_off)}. "
                    f"Using ElmCoup.on_off as truth."
                )

        graphic_type: SwitchGraphicType = _convert_pf_switch_graphic_type(iuse=0, ausage=coup.aUsage)

        sw = dev.Switch(
            bus_from=bus_from,
            bus_to=bus_to,
            name=coup.loc_name or f"ElmCoup_{coup_id}",
            idtag=coup_id,
            code=coup.typ_id,
            active=is_closed,
            normal_open=not is_closed,
            retained=False,
            rated_current=0.0,
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
            f"StaSwitch '{stasw.loc_name}' (ID={stasw.ID}) skipped: not connected to exactly 2 terminals."
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
        tower_template_by_line_id: Dict[str, OverheadLineType],
        freq: float,
        baseMVA: float,
        logger: Logger,
        cubics_by_objid: Dict[str, List[StaCubic]],
        bus_by_term_id: Dict[str, dev.Bus]
) -> dev.Line:
    """Convert a PowerFactory/DGS ElmLne into a VeraGrid Line.

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

    if (typ_id is None or typ_id == "") and tower_template is None:
        raise ValueError(
            f"ElmLne '{lne.loc_name}' (ID={lne.ID}): missing typ_id in ElmLne and no ElmLnesec fallback found."
        )

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

    if seq_template is None and ohl_template is None:
        raise ValueError(
            f"ElmLne '{lne.loc_name}' (ID={lne.ID}): no line template found for typ_id='{typ_id}'. "
            f"Expected TypLne (SequenceLineType) or TypTow (OverheadLineType)."
        )

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

    line = dev.Line(
        bus_from=bus_from,
        bus_to=bus_to,
        name=lne.loc_name,
        active=not lne.outserv,
        length=lne.dline
    )

    # ------------------------------------------------------------
    # Apply the resolved template
    # ------------------------------------------------------------
    if seq_template is not None:
        line.apply_template(obj=seq_template, Sbase=baseMVA, freq=freq, logger=logger)
    else:
        # OverheadLineType uses a 1-based circuit index. Default to circuit 1 here.
        line.set_circuit_idx(val=1, obj=ohl_template)
        line.apply_template(obj=ohl_template, Sbase=baseMVA, freq=freq, logger=logger)

    return line


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
        rate=1.0
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
        logger.add_warning(f"Load '{name}': scale0={s} looks like percent. Interpreting as {s / 100.0}.")
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
            logger.add_warning(f"Load '{name}': P/Q not provided, derived from slini/coslini.")

    # Apply scaling
    scale = _get_scale_factor(scale0=elmlod.scale0, logger=logger, name=name)
    p *= scale
    q *= scale

    return p, q


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
        active=0 if elmlod.outserv else 1
    )

    return bus, load


def convert_dgs_to_static_gen(elmgenstat: ElmGenstat,
                              stacubic_dict: Dict[str, List[int]],
                              buses: List[dev.Bus],
                              logger: Logger,
                              cubics_by_objid: Dict[str, List[StaCubic]],
                              bus_by_term_id: Dict[str, dev.Bus]) -> Tuple[dev.Bus, dev.StaticGenerator]:
    """
    Convert ElmGenstat to VeraGrid Load.
    """
    bus = get_injection_bus(elm_id=elmgenstat.ID,
                            stacubic_dict=stacubic_dict,
                            buses=buses,
                            cubics_by_objid=cubics_by_objid,
                            bus_by_term_id=bus_by_term_id)

    # Slack/reference machine indicator (PowerFactory exports ip_ctrl=1 on the slack generator)
    if int(elmgenstat.ip_ctrl) == 1:
        bus.is_slack = True


    stagen = dev.StaticGenerator(
        name=elmgenstat.loc_name or f"SatticGen_{_ref_id(elmgenstat.ID)}",
        P=elmgenstat.pgini,
        Q=elmgenstat.qgini,
        active=0 if elmgenstat.outserv else 1
    )

    # Preserve PowerFactory 'ip_ctrl' (1 means this is the reference/slack machine)
    stagen.ip_ctrl = int(elmgenstat.ip_ctrl)
    return bus, stagen


def convert_dgs_to_external_grid(elmxnet: ElmXnet,
                                 stacubic_dict: Dict[str, List[int]],
                                 buses: List[dev.Bus],
                                 logger: Logger,
                                 cubics_by_objid: Dict[str, List[StaCubic]],
                                 bus_by_term_id: Dict[str, dev.Bus]) -> Tuple[dev.Bus, dev.ExternalGrid]:
    """
    Convert ElmXnet to VeraGrid Load.
    """
    bus = get_injection_bus(elm_id=elmxnet.ID,
                            stacubic_dict=stacubic_dict,
                            buses=buses,
                            cubics_by_objid=cubics_by_objid,
                            bus_by_term_id=bus_by_term_id)

    xgrid = dev.ExternalGrid(
        name=elmxnet.loc_name or f"Load_{_ref_id(elmxnet.ID)}",
        active=0 if elmxnet.outserv else 1
    )

    if elmxnet.bustp == b'SL':
        bus.is_slack = True
        xgrid.Vm = elmxnet.usetp

    elif elmxnet.bustp == b'PV':
        xgrid.P = elmxnet.pgini

    elif elmxnet.bustp == b'PQ':
        xgrid.P = elmxnet.pgini
        xgrid.Q = elmxnet.qgini

    return bus, xgrid


def _extract_shunt_gb(elmshnt: ElmShnt, logger: Logger) -> Tuple[float, float]:
    """
    Extract (G, B) from an ElmShnt.
    VeraGrid expects:
      - G in MW @ v=1 p.u.
      - B in MVAr @ v=1 p.u. (positive capacitive, negative inductive)

    PowerFactory DGS typically provides:
      - qcapn / ncapa for capacitor steps
      - qrean for reactor MVAr
      - qtotn as total rated MVAr magnitude (often positive regardless of type)
      - shtype: 1 = reactor, 2 = capacitor
    """
    name = elmshnt.loc_name or _ref_id(elmshnt.ID) or "Shunt"

    # Active losses are not provided in the common DGS export, assume 0.0 MW @ v=1 p.u.
    g_mw: float = 0.0

    shtype: int = elmshnt.shtype  # 1 reactor, 2 capacitor
    qtotn: float = elmshnt.qtotn

    # Default to 0.0 in case the element is not energized or data is missing
    b_mvar: float = 0.0

    # Prefer total rating when available, but apply sign from shtype (PF export often stores magnitude)
    if qtotn != 0.0:
        b_mvar = abs(qtotn)
    else:
        if shtype == 1:
            # Reactor
            b_mvar = abs(elmshnt.qrean)
        elif shtype == 2:
            # Capacitor (may be step-based)
            q_step: float = elmshnt.qcapn
            n_on: int = elmshnt.ncapa
            if n_on <= 0:
                n_on = 1
            b_mvar = abs(q_step) * float(n_on)
        else:
            # Fallback: net MVAr = qcapn - qrean
            q_step: float = elmshnt.qcapn
            n_on: int = elmshnt.ncapa
            if n_on <= 0:
                n_on = 1
            b_mvar = (q_step * float(n_on)) - elmshnt.qrean

    # Apply sign convention
    if shtype == 1:
        b_mvar = -abs(b_mvar)
    elif shtype == 2:
        b_mvar = abs(b_mvar)
    # else: keep computed sign (fallback branch)

    if b_mvar == 0.0:
        logger.add_warning(
            f"Shunt '{name}': computed B=0.0 MVAr (shtype={shtype}, qcapn={elmshnt.qcapn}, ncapa={elmshnt.ncapa}, qrean={elmshnt.qrean}, qtotn={qtotn})."
        )

    return g_mw, b_mvar

def convert_dgs_to_shunt(elmshnt: ElmShnt,
                         stacubic_dict: Dict[str, List[int]],
                         buses: List[dev.Bus],
                         logger: Logger,
                         cubics_by_objid: Dict[str, List[StaCubic]],
                         bus_by_term_id: Dict[str, dev.Bus]) -> Tuple[dev.Bus, dev.Shunt]:
    """
    Convert ElmShnt to VeraGrid fixed Shunt.
    """
    name = elmshnt.loc_name or f"Shunt_{_ref_id(elmshnt.ID)}"

    bus = get_injection_bus(elm_id=elmshnt.ID,
                            stacubic_dict=stacubic_dict,
                            buses=buses,
                            cubics_by_objid=cubics_by_objid,
                            bus_by_term_id=bus_by_term_id)

    g_mw, b_mvar = _extract_shunt_gb(elmshnt=elmshnt, logger=logger)

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
    qtotn: float = float(elmshnt.qtotn)
    if q_step == 0.0 and qtotn != 0.0:
        q_step = qtotn / float(ncapx)
        logger.add_warning(
            f"ElmShnt '{name}': qcapn=0.0 but qtotn={qtotn}; using q_step=qtotn/ncapx={q_step}."
        )

    # Step increments: [0.0, q_step, q_step, ..., q_step] with length ncapx+1
    b_steps: np.ndarray = np.concatenate((np.array([0.0], dtype=float), np.full(ncapx, q_step, dtype=float)))

    # Initial step index equals the number of connected steps (ncapa) because b_steps[0] is OFF (0 MVAr).
    n_on: int = int(elmshnt.ncapa)

    initial_step: int = n_on

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
                                                  bus_by_term_id: Dict[str, dev.Bus]) -> Tuple[dev.Bus, dev.ControllableShunt]:
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

    b_steps, initial_step, bmin, bmax = _build_elmshnt_step_model(elmshnt=elmshnt, logger=logger)

    # DGS does not reliably encode automatic voltage control semantics for ElmShnt.
    # Stepped shunts are imported as operator-controlled devices (no automatic regulation).
    is_controlled: bool = False
    vset: float = float(elmshnt.usetp)

    cshunt: dev.ControllableShunt = dev.ControllableShunt(
        name=name,
        idtag=_ref_id(elmshnt.ID),
        is_nonlinear=False,
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
        is_controlled=is_controlled,
        control_bus=bus,
    )

    # Override step arrays to match the DGS stepped-bank model (OFF + ncapx identical increments).
    cshunt.b_steps = b_steps
    cshunt.g_steps = np.zeros(len(b_steps), dtype=float)
    cshunt.active_steps = np.ones(len(b_steps), dtype=int)

    # Ensure B/G are coherent with the initial step after overriding arrays
    cshunt.step = int(initial_step)

    return bus, cshunt

def convert_dgs_to_controllable_shunt(elmsvs: ElmSvs,
                                      stacubic_dict: Dict[str, List[int]],
                                      buses: List[dev.Bus],
                                      logger: Logger,
                                      cubics_by_objid: Dict[str, List[StaCubic]],
                                      bus_by_term_id: Dict[str, dev.Bus]) -> Tuple[dev.Bus, dev.ControllableShunt]:
    """
    Convert ElmSvs (PowerFactory SVS/SVC) to VeraGrid ControllableShunt.

    Notes
    -----
    - Electrical connectivity is obtained via StaCubic, consistent with other injected devices.
    - If the DGS does not provide a voltage setpoint, Vset defaults to 1.0 p.u. (per project convention).
    """
    name = elmsvs.loc_name or f"ElmSvs_{_ref_id(elmsvs.ID)}"

    bus = get_injection_bus(elm_id=elmsvs.ID,
                            stacubic_dict=stacubic_dict,
                            buses=buses,
                            cubics_by_objid=cubics_by_objid,
                            bus_by_term_id=bus_by_term_id)

    bmin = float(elmsvs.qmin)
    bmax = float(elmsvs.qmax)

    vset = float(elmsvs.usetp)

    # Build a small stepped model for B so the device can represent bmin / 0 / bmax when applicable
    if bmin < 0.0 and bmax > 0.0:
        b_steps = np.array([bmin, -bmin, bmax], dtype=float)
        initial_step = 1
    elif bmin == bmax:
        b_steps = np.array([bmax], dtype=float)
        initial_step = 0
    else:
        b_steps = np.array([bmin, (bmax - bmin)], dtype=float)
        initial_step = 0

    cshunt = dev.ControllableShunt(
        name=name,
        idtag=_ref_id(elmsvs.ID),
        is_nonlinear=False,
        number_of_steps=int(len(b_steps)),
        step=int(initial_step),
        g_per_step=0.0,
        b_per_step=0.0,
        Bmin=bmin,
        Bmax=bmax,
        Gmin=0.0,
        Gmax=0.0,
        active=(elmsvs.outserv == 0),
        vset=vset,
        is_controlled=True,
        control_bus=bus
    )

    # Override step arrays to match the constructed block model
    cshunt.b_steps = b_steps
    cshunt.g_steps = np.zeros(len(b_steps), dtype=float)
    cshunt.active_steps = np.ones(len(b_steps), dtype=int)

    # Ensure B/G are coherent with the initial step after overriding arrays
    cshunt.step = int(initial_step)

    return bus, cshunt


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
        logger.add_warning(f"Generator '{name}': {field}={v} looks like p.u. on Sbase. Interpreting as {v * baseMVA}.")
        return v * baseMVA

    return v


def convert_dgs_to_generator(elmsym: ElmSym,
                             stacubic_dict: Dict[str, List[int]],
                             buses: List[dev.Bus],
                             typsym_dict: Dict[str, TypSym],
                             baseMVA: float,
                             logger: Logger,
                             cubics_by_objid: Dict[str, List[StaCubic]],
                             bus_by_term_id: Dict[str, dev.Bus]) -> Tuple[dev.Bus, dev.Generator]:
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
    name = elmsym.loc_name or f"Gen_{_ref_id(elmsym.ID)}"

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

    p_mw = elmsym.pgini
    q_mvar = elmsym.qgini

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
        snom = typsym.sgn

    # Limits (q_min/q_max are often in p.u. on Sbase in DGS exports)
    qmin_raw = elmsym.q_min
    qmax_raw = elmsym.q_max

    qmin = _interpret_pu_limit(value=qmin_raw, baseMVA=baseMVA, reference_abs=abs(q_mvar),
                               logger=logger, name=name, field="q_min")
    qmax = _interpret_pu_limit(value=qmax_raw, baseMVA=baseMVA, reference_abs=abs(q_mvar),
                               logger=logger, name=name, field="q_max")

    # Optional P limits if present in schema
    pmin = elmsym.Pmin_uc
    pmax = elmsym.Pmax_uc

    # Interpret P limits if they look like p.u. too
    pmin = _interpret_pu_limit(value=pmin, baseMVA=baseMVA, reference_abs=abs(p_mw),
                               logger=logger, name=name, field="Pmin_uc")
    pmax = _interpret_pu_limit(value=pmax, baseMVA=baseMVA, reference_abs=abs(p_mw),
                               logger=logger, name=name, field="Pmax_uc")

    gen = dev.Generator(name=name,
                        P=p_mw,
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

    return bus, gen


def convert_dgs_to_asm_generator(elmasm: ElmAsm,
                                 stacubic_dict: Dict[str, List[int]],
                                 buses: List[dev.Bus],
                                 typasmo_dict: Dict[str, TypAsmo],
                                 baseMVA: float,
                                 logger: Logger,
                                 cubics_by_objid: Dict[str, List[StaCubic]],
                                 bus_by_term_id: Dict[str, dev.Bus]) -> Tuple[dev.Bus, dev.Generator]:
    """
    Convert ElmAsm (asynchronous machine) to VeraGrid Generator.

    Important notes:
    - We model ElmAsm as a non-voltage-controlled Generator (PQ behavior).
    - VeraGrid stores PQ behavior via (P, power_factor). There is no explicit Q field for PQ generators.
    - Therefore, we deduce the power factor from (P, Q) in the DGS.
    - If P and Q have opposite sign, VeraGrid cannot reproduce that sign combination using only Pf.
      In that case we log a warning and compute Pf from magnitudes.
    """
    name: str = elmasm.loc_name
    if name == "":
        name = f"ElmAsm_{_ref_id(elmasm.ID)}"

    # Bus resolution must be StaCubic-based (PowerFactory connectivity)
    bus = get_injection_bus(elm_id=elmasm.ID,
                            stacubic_dict=stacubic_dict,
                            buses=buses,
                            cubics_by_objid=cubics_by_objid,
                            bus_by_term_id=bus_by_term_id)

    p_mw: float = float(elmasm.pgini)
    q_mvar: float = float(elmasm.qgini)

    # Deduce power factor from P and Q
    # For a PQ generator in VeraGrid: Q ~= P * sqrt(1/Pf^2 - 1)
    abs_p: float = abs(p_mw)
    abs_q: float = abs(q_mvar)

    if abs_p > 0.0:
        s_mva: float = math.sqrt(p_mw * p_mw + q_mvar * q_mvar)
        if s_mva > 0.0:
            pf: float = abs_p / s_mva
        else:
            pf = 1.0
    else:
        # If P is zero, Pf cannot encode Q (VeraGrid formula would give Q=0).
        # We keep Pf=1.0 and warn if Q is not zero.
        pf = 1.0
        if abs_q > 0.0:
            logger.add_warning(
                f"ElmAsm '{name}' has P=0 with Q={q_mvar}. "
                f"PQ Generator in VeraGrid cannot encode reactive power when P=0 using only Pf. "
                f"Using Pf=1.0."
            )

    # If P and Q signs differ, VeraGrid Pf-only representation cannot match that sign combination
    if p_mw * q_mvar < 0.0:
        logger.add_warning(
            f"ElmAsm '{name}' has P and Q with opposite sign (P={p_mw}, Q={q_mvar}). "
            f"VeraGrid PQ Generator stores reactive via Pf magnitude only. "
            f"Computed Pf from |P| and |Q| (Pf={pf})."
        )

    # Resolve Snom from TypAsmo if available
    snom: float = 9999.0
    typasmo: TypAsmo | None = typasmo_dict.get(elmasm.typ_id, None)
    if typasmo is None:
        typasmo = typasmo_dict.get(_ref_id(elmasm.typ_id), None)

    if typasmo is not None:
        # Prefer nominal apparent power if present
        if typasmo.sgn != 0.0:
            snom = float(typasmo.sgn)
        else:
            # Fallback: if cosn is available, estimate S from Pn/cosn
            if typasmo.pgn != 0.0 and typasmo.cosn != 0.0:
                snom = float(typasmo.pgn / typasmo.cosn)
    else:
        # Fallback to operating point apparent power if non-zero
        s_op: float = math.sqrt(p_mw * p_mw + q_mvar * q_mvar)
        if s_op > 0.0:
            snom = float(s_op)

    # ElmAsm should behave as PQ (no voltage control)
    gen = dev.Generator(name=name,
                        P=p_mw,
                        power_factor=pf,
                        vset=1.0,
                        is_controlled=False,
                        Snom=snom,
                        active=(elmasm.outserv == 0),
                        Sbase=baseMVA)

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

    baseMVA = 100.0

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

        zone = dev.Zone(
            name=elmzone.loc_name if elmzone.loc_name != "" else f"Zone_{zid}",
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
        name = elmbranch.loc_name if elmbranch.loc_name != "" else f"BranchGroup_{bid}"

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

    # Generators
    for elmsym in dgs_grid.elmsyms:
        bus, gen = convert_dgs_to_generator(
            elmsym=elmsym,
            stacubic_dict=stacubic_dict,
            buses=grid.buses,
            typsym_dict=typsym_dict,
            baseMVA=baseMVA,
            logger=logger,
            cubics_by_objid=cubics_by_objid,
            bus_by_term_id=bus_by_term_id
        )

        grid.add_generator(bus=bus, api_obj=gen)

    # Asynchronous machines (ElmAsm) -> model as PQ Generators
    for elmasm in dgs_grid.elmasms:
        bus, gen = convert_dgs_to_asm_generator(
            elmasm=elmasm,
            stacubic_dict=stacubic_dict,
            buses=grid.buses,
            typasmo_dict=typasmo_dict,
            baseMVA=baseMVA,
            logger=logger,
            cubics_by_objid=cubics_by_objid,
            bus_by_term_id=bus_by_term_id
        )

        grid.add_generator(bus=bus, api_obj=gen)

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

    # Loads
    for elmgenstat in dgs_grid.elmgenstats:
        bus, stagen = convert_dgs_to_static_gen(
            elmgenstat=elmgenstat,
            stacubic_dict=stacubic_dict,
            buses=grid.buses,
            logger=logger,
            cubics_by_objid=cubics_by_objid,
            bus_by_term_id=bus_by_term_id
        )

        grid.add_static_generator(bus=bus, api_obj=stagen)

    # external grids
    for eg in dgs_grid.elmxnets:
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
                bus_by_term_id=bus_by_term_id
            )

            grid.add_controllable_shunt(bus=bus, api_obj=cshunt)
        else:
            bus, shunt = convert_dgs_to_shunt(
                elmshnt=elmshnt,
                stacubic_dict=stacubic_dict,
                buses=grid.buses,
                logger=logger,
                cubics_by_objid=cubics_by_objid,
                bus_by_term_id=bus_by_term_id
            )

            grid.add_shunt(bus=bus, api_obj=shunt)

    # Controllable shunts (SVC/SVS)
    for elmsvs in dgs_grid.elmsvss:
        bus, cshunt = convert_dgs_to_controllable_shunt(
            elmsvs=elmsvs,
            stacubic_dict=stacubic_dict,
            buses=grid.buses,
            logger=logger,
            cubics_by_objid=cubics_by_objid,
            bus_by_term_id=bus_by_term_id
        )

        grid.add_controllable_shunt(bus=bus, api_obj=cshunt)

    # Loads (LV)
    if len(dgs_grid.elmlodlvs) > 0 or len(dgs_grid.elmlodlvps) > 0:
        logger.add_warning("ElmLodlv/ElmLodlvp found but not converted: no P/Q fields available in DGS schema.")

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

    # Name-based helper maps. Some PF exports place ElmLnesec under folders that are not in the
    # IntFolder chain of the ElmLne, so fold_id climbing cannot reach the line. In that case,
    # the best available fallback is matching by loc_name / chr_name.
    line_id_by_loc_name: Dict[str, str] = dict()
    line_id_by_chr_name: Dict[str, str] = dict()
    for elmlne in dgs_grid.elmlnes:
        if elmlne.loc_name != "":
            line_id_by_loc_name[elmlne.loc_name] = _ref_id(elmlne.ID) or elmlne.ID
        if elmlne.chr_name != "":
            line_id_by_chr_name[elmlne.chr_name] = _ref_id(elmlne.ID) or elmlne.ID

    # Resolve each section to its owning line by climbing the folder chain
    for sec in dgs_grid.elmlnesecs:
        if sec.typ_id == "":
            continue

        current = sec.fold_id
        if current == "":
            continue

        cur = _ref_id(current)
        if cur is None or cur == "":
            cur = current

        owner_line_id: str = ""
        for _ in range(25):
            if cur in line_ids:
                owner_line_id = cur
                break

            parent_ptr = folder_parent.get(cur)
            if parent_ptr is None or parent_ptr == "":
                break

            nxt = _ref_id(parent_ptr)
            cur = nxt if (nxt is not None and nxt != "") else parent_ptr

        if owner_line_id == "":
            # Fallback: try matching by section names.
            if sec.loc_name != "" and sec.loc_name in line_id_by_loc_name:
                owner_line_id = line_id_by_loc_name[sec.loc_name]
            elif sec.chr_name != "" and sec.chr_name in line_id_by_chr_name:
                owner_line_id = line_id_by_chr_name[sec.chr_name]

        if owner_line_id == "":
            # Name-based fallback: try to match the section to a line by loc_name or chr_name.
            # This is used only if the folder-climb mechanism cannot resolve ownership.
            if sec.loc_name != "":
                owner_line_id = line_id_by_loc_name.get(sec.loc_name, "")
            if owner_line_id == "" and sec.chr_name != "":
                owner_line_id = line_id_by_chr_name.get(sec.chr_name, "")

        if owner_line_id != "":
            tid = _ref_id(sec.typ_id)
            typ_id = tid if (tid is not None and tid != "") else sec.typ_id
            line_type_by_line_id[owner_line_id] = typ_id
            # Store a normalized key too, because lne.ID might come with or without PF path prefix.
            oid = _ref_id(owner_line_id)
            if oid is not None and oid != "":
                line_type_by_line_id[oid] = typ_id

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
    line_by_dgs_id: Dict[str, dev.Line] = dict()
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
                    f"ElmLne '{elmlne.loc_name}' (ID={elmlne.ID}) skipped: "
                    f"not connected to exactly 2 terminals (StaCubic terminals={len(term_ids)}). "
                    f"typ_id='{elmlne.typ_id}'."
                )
                continue

        line = convert_dgs_to_line(
            lne=elmlne,
            buses=grid.buses,
            stacubic_dict=stacubic_dict,
            templates_dict=typlne_dict,
            overhead_line_type_dict=overhead_line_type_dict,
            line_type_by_line_id=line_type_by_line_id,
            tower_template_by_line_id=tower_template_by_line_id,
            freq=frequency,
            baseMVA=baseMVA,
            logger=logger,
            cubics_by_objid=cubics_by_objid,
            bus_by_term_id=bus_by_term_id
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
            line_by_dgs_id[lid] = line
        if lid_raw is not None and lid_raw != "":
            line_by_dgs_id[lid_raw] = line

    # Tower coupling (ElmTow): bind the created Line objects to OverheadLineType templates.
    # IMPORTANT: the Line objects must exist first (created above).
    for elmtow in dgs_grid.elmtows:
        if int(elmtow.outserv) != 0:
            continue

        if len(elmtow.pGeo) == 0:
            logger.add_warning(f"ElmTow '{elmtow.loc_name}': no pGeo specified, skipping tower binding.")
            continue

        geo_ptr = elmtow.pGeo[0]
        if geo_ptr is None:
            logger.add_warning(f"ElmTow '{elmtow.loc_name}': pGeo[0] is empty, skipping tower binding.")
            continue

        geo_id = _ref_id(geo_ptr)
        ohl_type = overhead_line_type_dict.get(geo_id)
        if ohl_type is None:
            ohl_type = overhead_line_type_dict.get(geo_ptr)

        if ohl_type is None:
            logger.add_warning(f"ElmTow '{elmtow.loc_name}': referenced tower type '{geo_ptr}' not found.")
            continue

        for idx, line_ptr in enumerate(elmtow.plines):
            if line_ptr is None:
                continue

            line_id = _ref_id(line_ptr)
            api_line = line_by_dgs_id.get(line_id)
            if api_line is None:
                api_line = line_by_dgs_id.get(line_ptr)

            if api_line is None:
                logger.add_warning(f"ElmTow '{elmtow.loc_name}': referenced line '{line_ptr}' not found.")
                continue

            # VeraGrid OverheadLineType uses a 1-based circuit index.
            circuit_idx = int(idx) + 1
            api_line.set_circuit_idx(val=circuit_idx, obj=ohl_type)
            api_line.apply_template(obj=ohl_type, Sbase=baseMVA, freq=frequency, logger=logger)

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

    # switches (PowerFactory/DGS: ElmCoup is the real device; StaCubic resolves connectivity)
    switch_by_cubic_id: Dict[str, StaSwitch] = build_switch_by_cubic_id(staswitchs=dgs_grid.staswitchs)

    vg_switches: List[dev.Switch] = convert_dgs_to_switches_from_elmcoup(
        elmcoups=dgs_grid.elmcoups,
        cubics_by_objid=cubics_by_objid,
        bus_by_term_id=bus_by_term_id,
        switch_by_cubic_id=switch_by_cubic_id,
        logger=logger
    )

    for sw in vg_switches:
        grid.add_switch(obj=sw)
    # Transformers 2W
    for elmtr2 in dgs_grid.elmtr2s:
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
            bus_by_term_id=bus_by_term_id
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
                f"Transformer3W '{elmtr3.loc_name}' (ID={elmtr3.ID}) "
                f"skipped: missing typ_id (no TypTr3 reference in DGS)."
            )
            continue

        term_ids: List[str] = get_terminal_ids(element_id=elmtr3.ID, cubics_by_objid=cubics_by_objid)
        if len(term_ids) != 3:
            bus_ids: List[int] | None = stacubic_dict.get(_ref_id(elmtr3.ID), None)
            if bus_ids is None or len(bus_ids) != 3:
                logger.add_warning(
                    f"Transformer3W '{elmtr3.loc_name}' (ID={elmtr3.ID}) "
                    f"skipped: not connected to exactly 3 terminals."
                )
                continue

        trafo3w = convert_dgs_to_transformer3w(
            tr3=elmtr3,
            buses=grid.buses,
            stacubic_dict=stacubic_dict,
            templates_dict=typtr3_dict,
            baseMVA=baseMVA,
            logger=logger,
            cubics_by_objid=cubics_by_objid,
            bus_by_term_id=bus_by_term_id
        )

        grid.add_bus(obj=trafo3w.bus0)
        # Optional grouping metadata: assign BranchGroup based on the DGS hierarchical folder reference.
        # IMPORTANT: this does not affect electrical connectivity.
        fold_id = _ref_id(elmtr3.fold_id)
        if fold_id is not None and fold_id != "":
            bg = branch_group_by_id.get(fold_id)
            if bg is not None:
                trafo3w.group = bg

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
#TODO: There might be an error with 3W trafos impedances