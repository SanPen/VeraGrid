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


def convert_shunt(load: dev.Shunt, new_id: str, t: int | None = None) -> ElmShnt:
    """

    :param load:
    :param new_id:
    :param t:
    :return:
    """
    e = ElmShnt()
    e.ID = new_id
    e.loc_name = load.name
    e.p = float(load.get_G_at(t))
    e.qlini = float(load.get_B_at(t))
    e.scale0 = 1.0
    e.outserv = 0 if load.get_active_at(t) else 1

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
    e.qgini = gen.get_Q_at(t)
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
    typlne.cline = seq.Cnf

    typlne.rline0 = seq.R0 if seq.R0 > 0 else 2 * seq.R
    typlne.xline0 = seq.X0 if seq.X0 > 0 else 2 * seq.X
    typlne.bline0 = seq.B0 if seq.B0 > 0 else 2 * seq.B
    typlne.cline0 = seq.Cnf0 if seq.Cnf0 > 0 else 2 * seq.Cnf

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

    # Y,YN,Z,ZN,D.
    wtpe_dict = {
        WindingType.FloatingStar: "Y",
        WindingType.GroundedStar: "Y",
        WindingType.NeutralStar: "YN",
        WindingType.Delta: "D",
        WindingType.ZigZag: "Z"
    }

    typtr2.tr2cn_h = wtpe_dict[tr.conn_hv]
    typtr2.tr2cn_l = wtpe_dict[tr.conn_lv]

    return typtr2


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
        term = bus2term_dict[load.bus]
        dgs_grid.elmlods.append(e)
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

    # transformer types
    tr2typtr2_dict: Dict[dev.TransformerType, TypTr2] = dict()
    for tr in grid.transformer_types:
        typtr2 = convert_transformer_type(tr=tr, new_id=dgs_grid.new_id())
        dgs_grid.typtr2s.append(typtr2)
        tr2typtr2_dict[tr] = typtr2

    # lines
    for line in grid.lines:

        # try search for the template
        tpe = seq2typlne_dict.get(line.template, None)

        if tpe is None:
            # produce a new template
            tpe = convert_sequence_line(seq=line.get_line_type(), new_id=dgs_grid.new_id())
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
            dgs_buses=[bus2term_dict[line.bus_from],
                       bus2term_dict[line.bus_to]]
        )

    # 2W transformers
    for tr in grid.transformers2w:
        # try search for the template
        tpe = tr2typtr2_dict.get(tr.template, None)

        if tpe is None:
            # produce a new template
            tpe = convert_transformer_type(tr=tr.get_transformer_type(),
                                           new_id=dgs_grid.new_id())
            dgs_grid.typtr2s.append(tpe)

        e = ElmTr2()
        e.ID = dgs_grid.new_id()
        e.loc_name = tr.name
        e.typ_id = tpe.ID
        e.ntnum = 1
        e.ratfac = 1
        e.outserv = 0 if tr.get_active_at(t) else 1

        hv_bus, lv_bus = tr.get_buses_sorted_by_voltage()

        dgs_grid.elmtr2s.append(e)
        dgs_grid.add_element_cubicles(
            element_id=e.ID,
            # the order must be HV, LV
            dgs_buses=[bus2term_dict[hv_bus],
                       bus2term_dict[lv_bus]]
        )

    # diagrams
    # for dia in grid.diagrams:
    #     if dia.diagram_type == DiagramType.Schematic:
    #         intgrfnet = IntGrfnet()
    #         intgrfnet.loc_name = dia.name
    #         intgrfnet.pDataFolder = net.ID
    #         dgs_grid.intgrfnets.append(intgrfnet)
    #
    #         for dtype, point_group in dia.data.items():
    #             for idtag, point in point_group.locations.items():
    #                 point.x
    #                 point.y
    #                 point.api_object.

    return dgs_grid
