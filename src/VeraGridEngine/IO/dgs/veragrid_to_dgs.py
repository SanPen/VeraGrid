# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import Dict, List, Type, Optional, Tuple

import numpy as np

import VeraGridEngine.Devices as dev
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.dgs.dgs_circuit import DgsCircuit
from VeraGridEngine.IO.dgs.dgs_objects import *
from VeraGridEngine.enumerations import DiagramType, WindingType
from VeraGridEngine.Devices.Branches.transformer_type import reverse_transformer_short_circuit_study

SQRT3 = np.sqrt(3)


def convert_bus(bus: dev.Bus, new_id: str, t: int | None = None) -> ElmTerm:
    """

    :param bus:
    :param new_id:
    :param t:
    :return:
    """
    elm_term = ElmTerm()
    elm_term.ID = new_id
    elm_term.loc_name = bus.name
    elm_term.uknom = bus.Vnom
    elm_term.unknom = bus.Vnom / SQRT3
    elm_term.vtarget = 1.0
    elm_term.outserv = 0 if bus.get_active_at(t) else 1

    if bus.is_slack:
        elm_term.bustp = "SL"

    return elm_term


def convert_bus_graphic(elm_term, bus: dev.Bus, new_id: str) -> IntGrf:
    """

    :param elm_term:
    :param bus:
    :param new_id:
    :return:
    """
    # opcional: IntGrf para posición
    int_grf = IntGrf()
    int_grf.ID = new_id
    int_grf.pDataObj = elm_term.ID
    int_grf.rCenterX = bus.x
    int_grf.rCenterY = bus.y

    return int_grf


def convert_shunt(shunt: dev.Shunt, new_id: str, ushnm_kv: float, t: int | None = None) -> ElmShnt:
    """
    Export VeraGrid fixed Shunt to PowerFactory ElmShnt.

    VeraGrid:
      - G in MW @ v=1 p.u.
      - B in MVAr @ v=1 p.u. (positive capacitive, negative inductive)

    DGS (ElmShnt) fields used by our importer:
      - shtype: 1 reactor, 2 capacitor
      - qtotn: total rated MVAr magnitude (usually stored as magnitude in PF)
      - qcapn/ncapa (capacitor steps) and qrean (reactor) as fallback
    """
    e = ElmShnt()
    e.ID = new_id
    e.loc_name = shunt.name

    g_mw = float(shunt.get_G_at(t))
    b_mvar = float(shunt.get_B_at(t))

    # Nominal voltage of the connection bus (kV)
    e.ushnm = float(ushnm_kv)

    # Technology / type (match typical PF export style)
    e.ctech = 1

    # Capacitor vs reactor (sign convention)
    if b_mvar >= 0.0:
        e.shtype = 2  # capacitor
        e.qcapn = abs(b_mvar)
        e.ncapx = 1
        e.ncapa = 1
        e.qrean = 0.0
    else:
        e.shtype = 1  # reactor
        e.qcapn = 0.0
        e.ncapx = 1
        e.ncapa = 1
        e.qrean = abs(b_mvar)

    # Total MVAr magnitude (importer prefers this when != 0)
    e.qtotn = abs(b_mvar)

    # Fixed shunt (not switchable by default)
    e.iswitch = 0

    # Frequency (optional but sane)
    e.fres = 50.0

    # Active losses are not represented in this common PF DGS shunt model.
    e.greaf0 = 0.0

    e.outserv = 0 if shunt.get_active_at(t) else 1
    return e


def convert_load(load: dev.Load, new_id: str, t: int | None = None) -> ElmLod:
    """

    :param load:
    :param new_id:
    :param t:
    :return:
    """
    e = ElmLod()
    e.ID = new_id
    e.loc_name = load.name
    e.plini = float(load.get_P_at(t))
    e.qlini = float(load.get_Q_at(t))
    e.scale0 = 1.0
    e.outserv = 0 if load.get_active_at(t) else 1

    return e


def convert_static_gen(stagen: dev.StaticGenerator, new_id: str, t: int | None = None) -> ElmGenstat:
    """

    :param stagen:
    :param new_id:
    :param t:
    :return:
    """
    e = ElmGenstat()
    e.ID = new_id
    e.loc_name = stagen.name
    e.pgini = float(stagen.get_P_at(t))
    e.qgini = float(stagen.get_Q_at(t))
    e.scale0 = 1.0
    e.outserv = 0 if stagen.get_active_at(t) else 1
    e.ngnum = 1
    e.cosn = stagen.get_Pf_at(t)
    e.sgn = stagen.Snom if stagen.Snom > 0 else 9999.0

    return e


def convert_gen_to_static_gen(gen: dev.Generator, new_id: str, t: int | None = None) -> ElmGenstat:
    """

    :param gen:
    :param new_id:
    :param t:
    :return:
    """
    e = ElmGenstat()
    e.ID = new_id
    e.loc_name = gen.name
    e.pgini = float(gen.get_P_at(t))
    e.qgini = float(gen.get_Q_at(t))
    e.scale0 = 1.0
    e.outserv = 0 if gen.get_active_at(t) else 1
    e.ngnum = 1
    e.cosn = gen.get_Pf_at(t)
    e.sgn = gen.Snom if gen.Snom > 0 else 9999.0

    return e


def convert_battery(batt: dev.Battery, new_id: str, t: int | None = None) -> ElmGenstat:
    """

    :param batt:
    :param new_id:
    :param t:
    :return:
    """
    e = ElmGenstat()
    e.ID = new_id
    e.loc_name = batt.name
    e.pgini = float(batt.get_P_at(t))
    e.qgini = float(batt.get_Q_at(t))
    e.scale0 = 1.0
    e.outserv = 0 if batt.get_active_at(t) else 1
    e.cCategory = "stor"
    e.ngnum = 1
    e.cosn = batt.get_Pf_at(t)
    e.sgn = batt.Snom if batt.Snom > 0 else 9999.0

    return e


def convert_generator(gen: dev.Generator, tpe_new_id: str, new_id: str, bus_v_controlled: Dict[dev.Bus, bool],
                      Sbase: float, t: int | None) -> Tuple[TypSym, ElmSym]:
    """

    :param gen:
    :param tpe_new_id:
    :param new_id:
    :param bus_v_controlled:
    :param Sbase:
    :param t:
    :return:
    """
    # Generate a fake TypSym
    tpe = TypSym()
    tpe.ID = tpe_new_id
    tpe.loc_name = gen.name
    tpe.ugn = gen.bus.Vnom
    tpe.cosn = gen.get_Pf_at(t)
    tpe.nphase = 3
    tpe.sgn = 0.01 if gen.Snom == 0 else gen.Snom

    e = ElmSym()
    e.ID = new_id
    e.loc_name = gen.name
    e.ngnum = 1
    e.outserv = 0 if gen.get_active_at(t) else 1
    e.pgini = gen.get_P_at(t)

    # DGS/PowerFactory convention: qgini is reactive power injection.
    q = -gen.get_Q_at(t)

    # If Q is not stored in VeraGrid (often 0.0), approximate it from P and power factor.
    if abs(q) < 1e-12:
        p = float(e.pgini)
        pf = abs(gen.get_Pf_at(t))
        if 0.0 < pf < 1.0 and abs(p) > 0.0:
            import math
            q_abs = abs(p) * math.tan(math.acos(pf))
            q = -q_abs if gen.bus.is_slack else q_abs

    e.qgini = q

    e.q_min = gen.get_Qmin_at(t) / Sbase
    e.q_max = gen.get_Qmax_at(t) / Sbase
    e.usetp = gen.get_Vset_at(t)
    e.ip_ctrl = 1 if gen.bus.is_slack else 0
    e.typ_id = tpe.ID
    e.Pmin_uc = gen.get_Pmin_at(t)
    e.Pmax_uc = gen.get_Pmax_at(t)

    if not bus_v_controlled[gen.bus]:
        # NOTE: in power factory, only one generator can control the bus voltage
        e.av_mode = "constv" if gen.is_controlled else "constq"
        bus_v_controlled[gen.bus] = True
    else:
        # the bus was flagged already
        e.av_mode = "constq"

    return tpe, e


def convert_sequence_line(seq: dev.SequenceLineType, new_id: str) -> TypLne:
    """

    :param seq:
    :param new_id:
    :return:
    """
    typlne = TypLne()
    typlne.ID = new_id

    typlne.loc_name = seq.name
    typlne.rline = seq.R
    typlne.xline = seq.X
    typlne.bline = seq.B

    if seq.use_conductance:
        typlne.cline = seq.Cnf
    else:
        typlne.cline = 0.0

    typlne.bline0 = seq.B0 if seq.B0 > 0 else 2 * seq.B

    if seq.use_conductance:
        typlne.cline0 = seq.Cnf0 if seq.Cnf0 > 0 else 2 * seq.Cnf
    else:
        typlne.cline0 = 0.0

    typlne.rline0 = seq.R0 if seq.R0 > 0 else 2 * seq.R
    typlne.xline0 = seq.X0 if seq.X0 > 0 else 2 * seq.X

    typlne.uline = seq.Vnom
    typlne.sline = seq.Imax
    typlne.InomAir = seq.Imax
    typlne.aohl_ = "cab"

    return typlne


def convert_transformer_type(tr: dev.TransformerType, new_id: str) -> TypTr2:
    """

    :param tr:
    :param new_id:
    :return:
    """
    typtr2 = TypTr2()
    typtr2.ID = new_id

    typtr2.utrn_h = tr.HV
    typtr2.utrn_l = tr.LV
    typtr2.strn = tr.Sn
    typtr2.pcutr = tr.Pcu
    typtr2.pfe = tr.Pfe
    typtr2.curmg = tr.I0
    typtr2.uktr = tr.Vsc
    typtr2.loc_name = tr.name
    typtr2.nt2ph = 3  # 3 phase

    """
    class WindingType(Enum):
        FloatingStar = "Y"
        GroundedStar = "Yg"
        NeutralStar = "Yn"
        Delta = "D"
        ZigZag = "Z"
    """

    # Y, YN, Z, ZN, D.
    wtpe_dict = {
        WindingType.FloatingStar: "Y",
        WindingType.NeutralStar: "Y",
        WindingType.GroundedStar: "YN",
        WindingType.Delta: "D",
        WindingType.ZigZag: "Z",
    }

    typtr2.tr2cn_h = wtpe_dict[tr.conn_hv]
    typtr2.tr2cn_l = wtpe_dict[tr.conn_lv]

    return typtr2



def _set_tr2_tap_fields_from_vgrid(tr: dev.Transformer2W, tpe: TypTr2, e: ElmTr2) -> None:
    """Set tap fields in TypTr2 and ElmTr2.

    This makes the exported DGS coherent with the importer (dgs_to_veragrid),
    which reconstructs tap_module from:
      - TypTr2.dutap, TypTr2.nntap0, TypTr2.ntpmn, TypTr2.ntpmx, TypTr2.tap_side, TypTr2.itapch
      - ElmTr2.nntap

    Notes:
    - VeraGrid Transformer2W exposes tap_module, tap_module_min, tap_module_max.
    - We must NOT choose step = max_dev. That makes most taps round to 0.
    - If tap_min/max look like garbage defaults, we ignore them.
    """
    tap = float(tr.tap_module)
    tap_min = float(tr.tap_module_min)
    tap_max = float(tr.tap_module_max)

    # sanitize
    if tap_min > tap_max:
        tap_min, tap_max = tap_max, tap_min

    tol = 1e-12
    tap_dev = abs(tap - 1.0)
    min_dev = abs(tap_min - 1.0)
    max_dev = abs(tap_max - 1.0)

    # Default: tap changer on HV side (0). If VeraGrid has a proper attribute, map it here.
    tpe.tap_side = 0
    tpe.phitr = 0.0
    tpe.nntap0 = 0

    # Fully neutral -> no tap changer
    if tap_dev < tol and min_dev < tol and max_dev < tol:
        tpe.itapch = 0
        tpe.dutap = 0.0
        tpe.ntpmn = 0
        tpe.ntpmx = 0
        e.nntap = 0
        return


    # Choose a step that produces a non-zero integer position for the actual tap.
    devs = [d for d in (tap_dev, min_dev, max_dev) if d > 1e-9]
    if len(devs) == 0:
        # practically neutral
        tpe.itapch = 0
        tpe.dutap = 0.0
        tpe.ntpmn = 0
        tpe.ntpmx = 0
        e.nntap = 0
        return

    step = min(devs)

    # Ensure that the current tap does not round to 0 if tap != 1.0
    n = int(round((tap - 1.0) / step))
    if n == 0 and tap_dev > 1e-6:
        step = tap_dev
        n = int(round((tap - 1.0) / step))

    # If still 0 (numerical weirdness), fall back to single-step encoding
    if n == 0 and tap_dev > 1e-6:
        n = -1 if tap < 1.0 else 1

    # Export final fields
    tpe.itapch = 1
    tpe.dutap = float(step * 100.0)  # percent per step
    e.nntap = int(n)

    tpe.ntpmn = int(round((tap_min - 1.0) / step))
    tpe.ntpmx = int(round((tap_max - 1.0) / step))

    if tpe.ntpmn > tpe.ntpmx:
        tpe.ntpmn, tpe.ntpmx = tpe.ntpmx, tpe.ntpmn


def generate_diesel_dsl_composite(dgs_grid: DgsCircuit, name: str, net_id: str) -> ElmComp:
    """
    Generate a diesel composite
    :param dgs_grid:
    :param name:
    :param net_id:
    :return:
    """
    elmcomp = ElmComp()
    elmcomp.ID = dgs_grid.new_id()
    elmcomp.loc_name = name
    elmcomp.fold_id = net_id

    for dsl_name in ["PSS/E COMP",
                     "PSS/E DEGOV1",
                     "PSS/E EXAC1"]:
        comp1 = ElmDsl()
        comp1.ID = dgs_grid.new_id()
        comp1.loc_name = dsl_name
        comp1.fold_id = elmcomp.ID
        dgs_grid.elmdsls.append(comp1)

    dgs_grid.elmcomps.append(elmcomp)

    return elmcomp


def generate_pv_dsl_composite(dgs_grid: DgsCircuit, name: str, net_id: str) -> ElmComp:
    """
    Generate a PV composite
    :param dgs_grid:
    :param name:
    :param net_id:
    :return:
    """
    elmcomp = ElmComp()
    elmcomp.ID = dgs_grid.new_id()
    elmcomp.loc_name = name
    elmcomp.fold_id = net_id

    for dsl_name in ["Active Power Reduction",
                     "Controller",
                     "DC Busbar and Capacitor",
                     "PV Array",
                     "Protection",
                     "Qreference",
                     "Solar Radiation",
                     "Temperature"]:
        comp1 = ElmDsl()
        comp1.ID = dgs_grid.new_id()
        comp1.loc_name = dsl_name
        comp1.fold_id = elmcomp.ID
        dgs_grid.elmdsls.append(comp1)

    dgs_grid.elmcomps.append(elmcomp)

    return elmcomp


def circuit_to_dgs(grid: dev.MultiCircuit, t: int | None = None, convert_gen_to_elmgenstat: bool = False) -> DgsCircuit:
    """
    Convert MultiCircuit to DgsCircuit
    :param grid: MultiCircuit
    :param t: time step (None for snapshot)
    :param convert_gen_to_elmgenstat: Convert generators to ElmGenstat depending on the technology assigned
    :return: DgsCircuit
    """
    dgs_grid = DgsCircuit()

    # general
    general = General()
    general.ID = dgs_grid.new_id()
    general.Descr = "Version"
    general.Val = "5.0"
    dgs_grid.generals.append(general)

    # grid
    net = ElmNet()
    net.ID = dgs_grid.new_id()
    net.loc_name = grid.name if grid.name != "" else "Grid"
    net.frnom = grid.fBase
    dgs_grid.elmnets.append(net)

    # Default load type. Assign to all loads so typ_id is never empty.
    typlod = TypLod()
    typlod.ID = dgs_grid.new_id()
    typlod.loc_name = "Default Load Type"
    typlod.fold_id = net.ID

    # Defaults (voltage dependency coefficients)
    typlod.systp = 0
    typlod.phtech = 0

    typlod.aP = 1.0
    typlod.bP = 0.0
    typlod.kpu0 = 0.0
    typlod.kpu1 = 1.0
    typlod.kpu = 2.0

    typlod.aQ = 1.0
    typlod.bQ = 0.0
    typlod.kqu0 = 0.0
    typlod.kqu1 = 1.0
    typlod.kqu = 2.0

    dgs_grid.typlods.append(typlod)


    # buses
    bus2term_dict: Dict[dev.Bus, ElmTerm] = dict()
    bus_v_controlled: Dict[dev.Bus, bool] = dict()
    for bus in grid.buses:
        elm_term = convert_bus(bus, new_id=dgs_grid.new_id(), t=t)
        dgs_grid.elmterms.append(elm_term)
        bus2term_dict[bus] = elm_term
        bus_v_controlled[bus] = False  # initialization values

        # int_grf = convert_bus_graphic(elm_term, bus, new_id=dgs_grid.new_id())
        # dgs_grid.intgrfs.append(int_grf)

    # Loads
    for load in grid.loads:
        e = convert_load(load, new_id=dgs_grid.new_id(), t=t)

        # Folder/type linkage
        e.fold_id = net.ID
        e.typ_id = typlod.ID

        # Input mode/scaling
        e.mode_inp = "DEF"
        e.pf_recap = 0
        e.i_scale = 1

        # Provide S and cos(phi) consistent with P/Q
        p = float(e.plini)
        q = float(e.qlini)
        s = (p * p + q * q) ** 0.5
        e.slini = float(s)
        e.coslini = float(p / s) if s > 0.0 else 1.0

        term = bus2term_dict[load.bus]
        dgs_grid.elmlods.append(e)
        dgs_grid.add_element_cubicles(element_id=e.ID, dgs_buses=[term])

    # Shunts
    for shunt in grid.shunts:
        term = bus2term_dict[shunt.bus]
        e = convert_shunt(shunt, new_id=dgs_grid.new_id(), ushnm_kv=term.uknom, t=t)
        dgs_grid.elmshnts.append(e)
        dgs_grid.add_element_cubicles(element_id=e.ID, dgs_buses=[term])

    # Static generators
    for stagen in grid.static_generators:
        e = convert_static_gen(stagen, new_id=dgs_grid.new_id(), t=t)
        term = bus2term_dict[stagen.bus]
        dgs_grid.elmgenstats.append(e)
        dgs_grid.add_element_cubicles(element_id=e.ID, dgs_buses=[term])

    # Batteries
    for batt in grid.batteries:
        e = convert_battery(batt, new_id=dgs_grid.new_id(), t=t)
        term = bus2term_dict[batt.bus]
        dgs_grid.elmgenstats.append(e)
        dgs_grid.add_element_cubicles(element_id=e.ID, dgs_buses=[term])

    # generators
    for gen in grid.generators:
        tech_list = gen.tech_list
        if len(gen.tech_list) > 0:
            tech_name = tech_list[0].name.lower()

            if ("pv" in tech_name or "batt" in tech_name or "wind" in tech_name) and convert_gen_to_elmgenstat:
                # This has to be a ElmGenstat
                e = convert_gen_to_static_gen(gen=gen, new_id=dgs_grid.new_id(), t=t)
                dgs_grid.elmgenstats.append(e)
            else:
                # Normal generator
                tpe, e = convert_generator(gen=gen,
                                           tpe_new_id=dgs_grid.new_id(),
                                           new_id=dgs_grid.new_id(),
                                           bus_v_controlled=bus_v_controlled,
                                           Sbase=grid.Sbase,
                                           t=t)
                dgs_grid.typsyms.append(tpe)
                dgs_grid.elmsyms.append(e)

            # Add DSL composites
            # if "diesel" in tech_name:
            #     composite = generate_diesel_dsl_composite(dgs_grid=dgs_grid,
            #                                               name=f"{gen.name} composite",
            #                                               net_id=net.ID)
            #     e.c_pmod = composite.ID
            # elif "pv" in tech_name:
            #     composite = generate_pv_dsl_composite(dgs_grid=dgs_grid,
            #                                           name=f"{gen.name} composite",
            #                                           net_id=net.ID)
            #     e.c_pmod = composite.ID

        else:

            # generate the actual generator
            tpe, e = convert_generator(gen=gen,
                                       tpe_new_id=dgs_grid.new_id(),
                                       new_id=dgs_grid.new_id(),
                                       bus_v_controlled=bus_v_controlled,
                                       Sbase=grid.Sbase,
                                       t=t)
            dgs_grid.typsyms.append(tpe)
            dgs_grid.elmsyms.append(e)

        term = bus2term_dict[gen.bus]
        dgs_grid.add_element_cubicles(element_id=e.ID, dgs_buses=[term])

    # sequence lines
    seq2typlne_dict: Dict[dev.SequenceLineType, TypLne] = dict()
    for seq in grid.sequence_line_types:
        typtr2 = convert_sequence_line(seq=seq, new_id=dgs_grid.new_id())
        dgs_grid.typlnes.append(typtr2)
        seq2typlne_dict[seq] = typtr2

    # transformer types (base types)
    base_tr2typtr2_dict: Dict[dev.TransformerType, TypTr2] = dict()
    for trt in grid.transformer_types:
        typtr2 = convert_transformer_type(tr=trt, new_id=dgs_grid.new_id())
        dgs_grid.typtr2s.append(typtr2)
        base_tr2typtr2_dict[trt] = typtr2

    # Export-aware transformer type cache:
    tr2typtr2_cache: Dict[
        Tuple[dev.TransformerType, float, float, float, float, float, float, float],
        TypTr2
    ] = dict()

    # lines
    for line in grid.lines:

        tpe = seq2typlne_dict.get(line.template, None)

        # --- guard: DGS export requires length > 0 ---
        if line.length <= 0.0:
            line.length = 1.0

        if tpe is None:
            seq = line.get_line_type()

            # DGS TypLne expects:
            #   rline/xline in Ohm/km
            #   bline/bline0 in uS/km
            vnom = line.bus_from.Vnom if line.bus_from.Vnom > 0.0 else line.bus_to.Vnom
            if vnom > 0.0:
                zbase = (vnom * vnom) / 100.0  # Sbase=100 MVA
                ybase = 1.0 / zbase

                # R/X: p.u./km -> Ohm/km
                seq.R *= zbase
                seq.X *= zbase
                if seq.R0 > 0.0:
                    seq.R0 *= zbase
                if seq.X0 > 0.0:
                    seq.X0 *= zbase

                # B: p.u./km -> uS/km
                seq.B *= (ybase * 1e6)
                if seq.B0 > 0.0:
                    seq.B0 *= (ybase * 1e6)

            tpe = convert_sequence_line(seq=seq, new_id=dgs_grid.new_id())
            dgs_grid.typlnes.append(tpe)

        e = ElmLne()
        e.ID = dgs_grid.new_id()
        e.loc_name = line.name
        e.typ_id = tpe.ID
        e.dline = line.length
        e.fline = 1.0
        e.nlnum = 1
        e.outserv = 0 if line.get_active_at(t) else 1

        dgs_grid.elmlnes.append(e)
        dgs_grid.add_element_cubicles(
            element_id=e.ID,
            dgs_buses=[bus2term_dict[line.bus_from], bus2term_dict[line.bus_to]]
        )

    # 2W transformers
    for tr in grid.transformers2w:

        # Get actual connected buses first (we will force TypTr2 nominal voltages from them)
        hv_bus, lv_bus = tr.get_buses_sorted_by_voltage()

        # Create ONE TypTr2 per ElmTr2. Reusing/caching transformer types can merge
        tpe = convert_transformer_type(tr=tr.get_transformer_type(), new_id=dgs_grid.new_id())
        dgs_grid.typtr2s.append(tpe)
        tpe_is_new = True

        if float(tpe.frnom) == 0.0:
            tpe.frnom = float(net.frnom)

        # Force nominal voltages from the actual connected buses (not from template)
        # to avoid template contamination and shared-type issues.
        tpe.utrn_h = float(hv_bus.Vnom)
        tpe.utrn_l = float(lv_bus.Vnom)

        # The importer rebuilds transformer R/X from TypTr2.uktr (%) + TypTr2.pcutr (kW).
        rate = float(grid.Sbase)

        Pfe, Pcu, Vsc, I0, Sn = reverse_transformer_short_circuit_study(
            R=float(tr.R),
            X=float(tr.X),
            G=float(tr.G),
            B=float(tr.B),
            rate=rate,
            Sbase=float(grid.Sbase),
        )

        tpe.pfe = float(Pfe)
        tpe.pcutr = float(Pcu)
        tpe.uktr = float(Vsc)
        tpe.curmg = float(I0)
        tpe.strn = float(Sn)

        e = ElmTr2()
        e.ID = dgs_grid.new_id()
        e.loc_name = tr.name
        e.typ_id = tpe.ID
        e.ntnum = 1
        e.ratfac = 1
        e.outserv = 0 if tr.get_active_at(t) else 1

        # PF-like folder placement
        e.fold_id = net.ID

        # PF-like tap controller defaults
        e.usetp = 1.0
        e.usp_low = 0.99
        e.usp_up = 1.01
        e.t2ldc = 0

        # Export tap fields from VeraGrid -> TypTr2/ElmTr2
        _set_tr2_tap_fields_from_vgrid(tr=tr, tpe=tpe, e=e)

        dgs_grid.elmtr2s.append(e)

        # Preserve branch orientation as stored in VeraGrid (bus_from -> bus_to)
        dgs_grid.add_element_cubicles(
            element_id=e.ID,
            dgs_buses=[bus2term_dict[tr.bus_from],
                       bus2term_dict[tr.bus_to]]
        )


    return dgs_grid
