# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
import math
import numpy as np
from typing import Dict, List, Tuple, Set
from VeraGridEngine.enumerations import WindingType, SwitchGraphicType
import VeraGridEngine.Devices as dev
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

    if template is None:
        raise ValueError(f"No template for the transformer3w {tr3.ID}")

    # Check connectivity through robust StaCubic.fold_id mapping first (preferred)
    term_ids = get_terminal_ids(element_id=tr3.ID, cubics_by_objid=cubics_by_objid)
    if len(term_ids) != 3:
        # Fall back to legacy check only if terminal mapping is not available
        bus_ids = stacubic_dict.get(_ref_id(tr3.ID), None)
        if bus_ids is None:
            raise ValueError(f"No buses for the transformer3w {tr3.ID}")

        if len(bus_ids) != 3:
            raise ValueError(f"Not exactly 3 buses for the transformer3w {tr3.ID}")

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


def convert_dgs_to_line(lne: ElmLne,
                        buses: List[dev.Bus],
                        stacubic_dict: Dict[str, List[int]],
                        templates_dict: Dict[str, dev.SequenceLineType],
                        freq: float,
                        baseMVA: float,
                        logger: Logger,
                        cubics_by_objid: Dict[str, List[StaCubic]],
                        bus_by_term_id: Dict[str, dev.Bus]) -> dev.Line:
    """

    :param lne:
    :param buses:
    :param stacubic_dict:
    :param templates_dict:
    :param freq:
    :param baseMVA:
    :param logger:
    :param cubics_by_objid:
    :param bus_by_term_id:
    :return:
    """

    template = templates_dict.get(lne.typ_id, None)
    if template is None:
        raise ValueError(f"No template for the line {lne.ID}")

    # Check connectivity through robust StaCubic.fold_id mapping first (preferred)
    term_ids = get_terminal_ids(element_id=lne.ID, cubics_by_objid=cubics_by_objid)
    if len(term_ids) != 2:
        # Fall back to legacy check only if terminal mapping is not available
        bus_ids = stacubic_dict.get(_ref_id(lne.ID), None)
        if bus_ids is None:
            raise ValueError(f"No buses for the line {lne.ID}")

        if len(bus_ids) != 2:
            raise ValueError(f"Not exactly 2 buses for the line {lne.ID}")

    bus_from, bus_to = get_branch_buses(elm_id=lne.ID,
                                        stacubic_dict=stacubic_dict,
                                        buses=buses,
                                        cubics_by_objid=cubics_by_objid,
                                        bus_by_term_id=bus_by_term_id)

    line = dev.Line(bus_from=bus_from,
                    bus_to=bus_to,
                    name=lne.loc_name,
                    active=not lne.outserv,
                    length=lne.dline)

    line.apply_template(obj=template, Sbase=baseMVA, freq=freq, logger=logger)

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

    stagen = dev.StaticGenerator(
        name=elmgenstat.loc_name or f"SatticGen_{_ref_id(elmgenstat.ID)}",
        P=elmgenstat.pgini,
        Q=elmgenstat.qgini,
        active=0 if elmgenstat.outserv else 1
    )

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
      - B in MVAr @ v=1 p.u.
    PowerFactory DGS provides qcapn as MVAr per step and ncapa as connected steps.
    """
    name = elmshnt.loc_name or _ref_id(elmshnt.ID) or "Shunt"

    # Active losses are not provided in the common DGS export, assume 0.0 MW @ v=1 p.u.
    g_mw: float = 0.0

    # Reactive power per step (MVAr) and connected steps
    q_step: float = elmshnt.qcapn
    n_on: int = elmshnt.ncapa

    if n_on <= 0:
        n_on = 1

    b_mvar: float = q_step * float(n_on)

    # If total rated MVAr is present in schema, prefer it when non-zero
    qtotn: float = elmshnt.qtotn
    if qtotn != 0.0:
        b_mvar = qtotn

    if b_mvar == 0.0:
        logger.add_warning(f"Shunt '{name}': computed B=0.0 MVAr (qcapn={q_step}, ncapa={n_on}).")

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

    # Fixed shunts only: if max steps > 1, the device is stepped/controllable in PF
    ncapx: int = elmshnt.ncapx
    if ncapx > 1:
        logger.add_warning(f"ElmShnt '{name}': ncapx={ncapx} indicates stepped shunt. Skipping fixed conversion.")
        raise ValueError("ElmShnt is stepped/controllable (ncapx>1).")

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

    # Skip motors (ElmSym can represent synchronous motors too)
    if elmsym.i_mot != 0:
        logger.add_warning(f"ElmSym '{name}' is marked as motor (i_mot=1). Skipping Generator conversion.")
        raise ValueError("ElmSym is a motor, not a generator.")

    bus = get_injection_bus(elm_id=elmsym.ID,
                            stacubic_dict=stacubic_dict,
                            buses=buses,
                            cubics_by_objid=cubics_by_objid,
                            bus_by_term_id=bus_by_term_id)

    # Resolve type (optional but recommended)
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

    # slack
    if elmsym.ip_ctrl == 1:
        bus.is_slack = True

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

    # lines
    for elmlne in dgs_grid.elmlnes:
        line = convert_dgs_to_line(
            lne=elmlne,
            buses=grid.buses,
            stacubic_dict=stacubic_dict,
            templates_dict=typlne_dict,
            freq=frequency,
            baseMVA=baseMVA,
            logger=logger,
            cubics_by_objid=cubics_by_objid,
            bus_by_term_id=bus_by_term_id
        )
        grid.add_line(obj=line, logger=logger)

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