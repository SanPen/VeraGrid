# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, Iterator, List, Type, Optional, Tuple
from VeraGridEngine.IO.dgs.dgs_objects import (
    BlkDef,
    BlkDiv,
    BlkFrom,
    BlkGoto,
    BlkMul,
    BlkRef,
    BlkSig,
    BlkSlot,
    BlkSum,
    BlkSwt,
    ChaRef,
    ChaVec,
    ComLdf,
    DgsProperty,
    DGSElement,
    ElmArea,
    ElmAsm,
    ElmBranch,
    ElmComp,
    ElmCoup,
    ElmDsl,
    ElmFeeder,
    ElmGenstat,
    # Alex review required: VSC equipment rows converted into the final MultiCircuit.
    ElmVsc,
    ElmVscmono,
    ElmLne,
    ElmLnesec,
    ElmLod,
    ElmLodlv,
    ElmLodlvp,
    ElmNet,
    ElmPhi,
    ElmScap,
    ElmShnt,
    ElmSind,
    ElmSite,
    ElmSubstat,
    ElmSvs,
    ElmSym,
    ElmTerm,
    ElmTow,
    ElmTr2,
    ElmTr3,
    ElmTr4,
    ElmVac,
    ElmXnet,
    ElmZone,
    ElmZpu,
    General,
    IntFolder,
    IntGrf,
    IntGrfcon,
    IntGrfnet,
    IntRef,
    IntTemplate,
    Matrix,
    RelFuse,
    StaCt,
    StaCubic,
    StaSwitch,
    StaImea,
    StaPqmea,
    StaVmea,
    StaVt,
    TypAsmo,
    TypCon,
    TypCt,
    TypFuse,
    TypGeo,
    TypLne,
    TypLod,
    TypSind,
    TypSwitch,
    TypSym,
    TypTow,
    TypTr2,
    TypTr3,
    TypTr4,
    TypVt,
    _split_dgs_line,
)
from VeraGridEngine.basic_structures import Logger

def parse_header(line: str) -> Tuple[str, Dict[str, int]]:
    """
    Parse $$ header line and return property -> index map.
    """
    element_type = line[2:].split(";", 1)[0]
    parts = line.strip().split(';')[1:]  # skip $$ElementType
    header_map: Dict[str, int] = {}

    for i, name_stub in enumerate(parts):
        name_stub = parts[i]
        stubs = name_stub.split("(")
        prop_name = stubs[0] if len(stubs) > 0 else name_stub
        header_map[prop_name] = i

        # PowerFactory exports commonly use 'FID' as the unique identifier column.
        # The schema in dgs_objects.py uses the python attribute name 'ID'. Map both.
        if prop_name == 'FID':
            header_map['ID'] = i

    return element_type, header_map


def _elm_sind_initial_resistance_envelope_is_declared(
        elements: List[ElmSind],
) -> bool:
    """Validate and select the ``ElmSind.s:Rin`` output envelope.

    A DGS table owns one header for every row. Consequently, a legacy table
    cannot be mixed with enriched rows without changing the meaning of its
    missing resistance evidence. Validation occurs before the output file is
    opened so a rejected table cannot leave a truncated artifact.

    :param elements: Series-impedance rows scheduled for serialization.
    :return: Whether the output table must declare ``s:Rin``.
    :raises ValueError: If enriched and legacy rows are mixed or an enriched
        resistance is invalid.
    """
    declared_count: int = 0
    element: ElmSind
    for element in elements:
        if element.initial_resistance_column_declared:
            declared_count += 1
        else:
            pass

    if declared_count == 0:
        return False
    else:
        if declared_count == len(elements):
            for element in elements:
                if (
                        element.Rin is not None
                        and math.isfinite(element.Rin)
                        and element.Rin > 0.0
                ):
                    pass
                else:
                    raise ValueError(
                        "Cannot write an enriched ElmSind table with an invalid s:Rin value"
                    )
            return True
        else:
            raise ValueError(
                "Cannot write one ElmSind table with mixed legacy and enriched s:Rin evidence"
            )


class DgsCircuit:
    """Strongly-typed container for a PowerFactory DGS file."""

    _ELEMENT_CLASSES: List[Type[DGSElement]] = [
        General,
        BlkDef,
        BlkDiv,
        BlkFrom,
        BlkGoto,
        BlkMul,
        BlkRef,
        BlkSig,
        BlkSlot,
        BlkSum,
        BlkSwt,
        ChaRef,
        ChaVec,
        ComLdf,
        ElmComp,
        ElmDsl,
        ElmBranch,
        ElmAsm,
        ElmCoup,
        ElmFeeder,
        ElmGenstat,
        # Alex review required: recognize both VSC formats as declarative DGS elements.
        ElmVsc,
        ElmVscmono,
        ElmLne,
        ElmTow,
        ElmZpu,
        ElmScap,
        ElmSind,
        ElmLnesec,
        ElmVac,
        ElmLod,
        ElmLodlv,
        ElmLodlvp,
        ElmNet,
        ElmPhi,
        ElmShnt,
        ElmSvs,
        ElmSite,
        ElmSubstat,
        ElmSym,
        ElmTerm,
        ElmTr2,
        ElmTr3,
        ElmTr4,
        ElmXnet,
        ElmZone,
        ElmArea,
        General,
        IntFolder,
        IntRef,
        IntTemplate,
        IntGrf,
        IntGrfcon,
        IntGrfnet,
        Matrix,
        RelFuse,
        StaCubic,
        StaCt,
        StaImea,
        StaPqmea,
        StaSwitch,
        StaVmea,
        StaVt,
        TypSwitch,
        TypAsmo,
        TypCt,
        TypFuse,
        TypCon,
        TypGeo,
        TypLne,
        TypTow,
        TypSind,
        TypLod,
        TypSym,
        TypTr2,
        TypTr3,
        TypTr4,
        TypVt,
    ]

    ELEMENT_CLASS_BY_KIND: Dict[str, Type[DGSElement]] = {
        cls.element_type: cls for cls in _ELEMENT_CLASSES
    }

    def __init__(self) -> None:
        """

        """
        self._id_counter = 0

        self.generals: List[General] = list()
        self.blkdefs: List[BlkDef] = list()
        self.blkdivs: List[BlkDiv] = list()
        self.blkfroms: List[BlkFrom] = list()
        self.blkgotos: List[BlkGoto] = list()
        self.blkmuls: List[BlkMul] = list()
        self.blkrefs: List[BlkRef] = list()
        self.blksigs: List[BlkSig] = list()
        self.blkslots: List[BlkSlot] = list()
        self.blksums: List[BlkSum] = list()
        self.comldfs: List[ComLdf] = list()
        self.blkswts: List[BlkSwt] = list()
        self.elmcomps: List[ElmComp] = list()
        self.elmdsls: List[ElmDsl] = list()
        self.elmbranches: List[ElmBranch] = list()
        self.charefs: List[ChaRef] = list()
        self.chavecs: List[ChaVec] = list()
        self.elmasms: List[ElmAsm] = list()
        self.elmcoups: List[ElmCoup] = list()
        self.elmfeeders: List[ElmFeeder] = list()
        self.elmgenstats: List[ElmGenstat] = list()
        # Alex review required: discard transient collections after creating the final VSC devices.
        self.elmvscs: List[ElmVsc] = list()
        self.elmvscmonos: List[ElmVscmono] = list()
        self.elmlnes: List[ElmLne] = list()
        self.elmtows: List[ElmTow] = list()
        self.elmsinds: List[ElmSind] = list()
        self.elmlnesecs: List[ElmLnesec] = list()
        self.elmvacs: List[ElmVac] = list()
        self.elmlods: List[ElmLod] = list()
        self.elmlodlvs: List[ElmLodlv] = list()
        self.elmlodlvps: List[ElmLodlvp] = list()
        self.elmnets: List[ElmNet] = list()
        self.elmphis: List[ElmPhi] = list()
        self.elmshnts: List[ElmShnt] = list()
        self.elmsvss: List[ElmSvs] = list()
        self.elmzpus: List[ElmZpu] = list()
        self.elmscaps: List[ElmScap] = list()
        self.elmsites: List[ElmSite] = list()
        self.elmsubstats: List[ElmSubstat] = list()
        self.elmsyms: List[ElmSym] = list()
        self.elmterms: List[ElmTerm] = list()
        self.elmtr2s: List[ElmTr2] = list()
        self.elmtr3s: List[ElmTr3] = list()
        self.elmtr4s: List[ElmTr4] = list()
        self.elmxnets: List[ElmXnet] = list()
        self.elmzones: List[ElmZone] = list()
        self.elmareas: List[ElmArea] = list()
        self.intfolders: List[IntFolder] = list()
        self.intrefs: List[IntRef] = list()
        self.inttemplates: List[IntTemplate] = list()
        self.intgrfs: List[IntGrf] = list()
        self.intgrfcons: List[IntGrfcon] = list()
        self.intgrfnets: List[IntGrfnet] = list()
        self.matrixes: List[Matrix] = list()
        self.relfuses: List[RelFuse] = list()
        self.stacubics: List[StaCubic] = list()
        self.stacts: List[StaCt] = list()
        self.staimeas: List[StaImea] = list()
        self.stapqmeas: List[StaPqmea] = list()
        self.staswitchs: List[StaSwitch] = list()
        self.stavmeas: List[StaVmea] = list()
        self.stavts: List[StaVt] = list()
        self.typswitches: List[TypSwitch] = list()
        self.typasmos: List[TypAsmo] = list()
        self.typcts: List[TypCt] = list()
        self.typfuses: List[TypFuse] = list()
        self.typcons: List[TypCon] = list()
        self.typgeos: List[TypGeo] = list()
        self.typlnes: List[TypLne] = list()
        self.typtows: List[TypTow] = list()
        self.typsinds: List[TypSind] = list()
        self.typlods: List[TypLod] = list()
        self.typsyms: List[TypSym] = list()
        self.typtr2s: List[TypTr2] = list()
        self.typtr3s: List[TypTr3] = list()
        self.typtr4s: List[TypTr4] = list()
        self.typvts: List[TypVt] = list()

        self._CLASS_TO_LIST: Dict[Type[DGSElement], List[DGSElement]] = {
            General: self.generals,
            BlkDef: self.blkdefs,
            BlkDiv: self.blkdivs,
            BlkFrom: self.blkfroms,
            BlkGoto: self.blkgotos,
            BlkMul: self.blkmuls,
            BlkRef: self.blkrefs,
            BlkSig: self.blksigs,
            BlkSlot: self.blkslots,
            BlkSum: self.blksums,
            BlkSwt: self.blkswts,
            ChaRef: self.charefs,
            ChaVec: self.chavecs,
            ComLdf: self.comldfs,
            ElmComp: self.elmcomps,
            ElmDsl: self.elmdsls,
            ElmBranch: self.elmbranches,
            ElmAsm: self.elmasms,
            ElmCoup: self.elmcoups,
            ElmFeeder: self.elmfeeders,
            ElmGenstat: self.elmgenstats,
            # Alex review required: route each VSC table into its typed import collection.
            ElmVsc: self.elmvscs,
            ElmVscmono: self.elmvscmonos,
            ElmLne: self.elmlnes,
            ElmTow: self.elmtows,
            ElmZpu: self.elmzpus,
            ElmScap: self.elmscaps,
            ElmSind: self.elmsinds,
            ElmLnesec: self.elmlnesecs,
            ElmVac: self.elmvacs,
            ElmLod: self.elmlods,
            ElmLodlv: self.elmlodlvs,
            ElmLodlvp: self.elmlodlvps,
            ElmNet: self.elmnets,
            ElmPhi: self.elmphis,
            ElmShnt: self.elmshnts,
            ElmSvs: self.elmsvss,
            ElmSite: self.elmsites,
            ElmSubstat: self.elmsubstats,
            ElmSym: self.elmsyms,
            ElmTerm: self.elmterms,
            ElmTr2: self.elmtr2s,
            ElmTr3: self.elmtr3s,
            ElmTr4: self.elmtr4s,
            ElmXnet: self.elmxnets,
            ElmZone: self.elmzones,
            ElmArea: self.elmareas,
            IntFolder: self.intfolders,
            IntRef: self.intrefs,
            IntTemplate: self.inttemplates,
            IntGrf: self.intgrfs,
            IntGrfcon: self.intgrfcons,
            IntGrfnet: self.intgrfnets,
            Matrix: self.matrixes,
            RelFuse: self.relfuses,
            StaCubic: self.stacubics,
            StaCt: self.stacts,
            StaImea: self.staimeas,
            StaPqmea: self.stapqmeas,
            StaSwitch: self.staswitchs,
            StaVmea: self.stavmeas,
            StaVt: self.stavts,
            TypSwitch: self.typswitches,
            TypAsmo: self.typasmos,
            TypCt: self.typcts,
            TypFuse: self.typfuses,
            TypCon: self.typcons,
            TypGeo: self.typgeos,
            TypLne: self.typlnes,
            TypTow: self.typtows,
            TypSind: self.typsinds,
            TypLod: self.typlods,
            TypSym: self.typsyms,
            TypTr2: self.typtr2s,
            TypTr3: self.typtr3s,
            TypTr4: self.typtr4s,
            TypVt: self.typvts,
        }

        self.logger = Logger()

    def new_id(self) -> str:
        """

        :return:
        """
        self._id_counter += 1
        return str(self._id_counter)

    def get_all_elements_iter(self) -> Iterator[DGSElement]:
        """Iterate over every parsed DGS element in schema order.

        This public boundary lets import layers build exact FID indexes without
        reaching into the circuit's private class registry.

        :return: Iterator over all parsed DGS elements.
        """
        element_list: List[DGSElement]
        element: DGSElement
        for element_list in self._CLASS_TO_LIST.values():
            for element in element_list:
                yield element

    def add_element_cubicles(self, element_id: str, dgs_buses: List[ElmTerm]):
        """
        Add cubicles + their StaSwitch objects.
        IMPORTANT: Import expects StaSwitch.fold_id == StaCubic.ID.
        """
        for i, b in enumerate(dgs_buses):
            c = StaCubic()
            c.ID = self.new_id()
            c.loc_name = f"StaCubic_{c.ID}"
            c.obj_id = element_id
            c.obj_bus = i
            c.fold_id = b.ID
            c.it2p1 = 0
            c.it2p2 = 1
            c.it2p3 = 2
            self.stacubics.append(c)

            # Create the switch that belongs to this cubicle
            sw = StaSwitch()
            sw.ID = self.new_id()
            sw.loc_name = f"StaSwitch_{sw.ID}"
            sw.fold_id = c.ID  # points to StaCubic.ID
            sw.on_off = 1  # default closed
            sw.typ_id = ""
            sw.iUse = 0
            sw.for_name = ""
            sw.aUsage = "cbk"  # matches typical PF exports
            self.staswitchs.append(sw)

    def parse_dgs(self, path: str) -> None:
        """
        Parse a DGS file and populate the typed lists.
        """
        path2 = Path(path)
        current_cls: Optional[Type[DGSElement]] = None
        header_map: Dict[str, int] | None = None

        with path2.open("r", encoding="utf-8", errors="ignore") as f:
            for raw_line in f:
                line = raw_line.strip()

                if line == "" or line.startswith("*"):
                    # Empty line or comment
                    pass

                elif line.startswith("$$"):
                    # Header line
                    element_type, header_map = parse_header(line)
                    normalized_element_type: str
                    if element_type in ("ElmPhi__pll", "ElmPhi__Pll"):
                        # PowerFactory exposes the implementation suffix on
                        # some native PLL exports. Both names share the exact
                        # declarative ElmPhi row contract.
                        normalized_element_type = "ElmPhi"
                    else:
                        normalized_element_type = element_type
                    current_cls = self.ELEMENT_CLASS_BY_KIND.get(
                        normalized_element_type,
                        None,
                    )

                else:
                    # Data line
                    if current_cls is not None:
                        obj = current_cls.parse_line(line=line, header_map=header_map)

                        if obj is not None:
                            if isinstance(obj, ElmSind):
                                if header_map is not None:
                                    # Preserve whether the source declared the
                                    # enriched physical-resistance envelope so
                                    # invalid data cannot masquerade as legacy.
                                    obj.initial_resistance_column_declared = (
                                        "s:Rin" in header_map
                                    )
                                else:
                                    obj.initial_resistance_column_declared = False
                            else:
                                pass
                            objects_lst = self._CLASS_TO_LIST[current_cls]
                            objects_lst.append(obj)

    def write_dgs(self, path: str) -> None:
        """Write the circuit to a declarative DGS file.

        :param path: Destination DGS path.
        :return: None.
        """
        path2 = Path(path)
        elm_sind_resistance_declared: bool = (
            _elm_sind_initial_resistance_envelope_is_declared(
                elements=self.elmsinds,
            )
        )

        with path2.open("w", encoding="utf-8") as f:

            comment = "*" * 80 + "\n"
            comment += "* Created with VeraGrid\n"
            comment += "*" * 80 + "\n"
            f.write(comment + "\n")

            for cls in self._ELEMENT_CLASSES:
                objects: List[DGSElement] = self._CLASS_TO_LIST[cls]

                if len(objects) > 0:
                    output_properties: List[DgsProperty] = list()
                    prop: DgsProperty
                    for prop in cls.properties_list:
                        omit_legacy_resistance: bool = (
                                cls is ElmSind
                                and not elm_sind_resistance_declared
                                and prop.name == "s:Rin"
                        )
                        if omit_legacy_resistance:
                            pass
                        else:
                            output_properties.append(prop)

                    header = "$$" + cls.element_type + ";" + ";".join(
                        f"{prop.name}({prop.dgs_type})"
                        for prop in output_properties
                    )
                    f.write(header + "\n")

                    comment = "*" * 80 + "\n"
                    for prp in output_properties:
                        comment += f"* {prp.name}: {prp.dgs_type}: {prp.description}\n"

                    comment += "*" * 80
                    f.write(comment + "\n")

                    for obj in objects:
                        serialized_line: str = obj.to_dgs_line()
                        if cls is ElmSind and not elm_sind_resistance_declared:
                            serialized_parts: List[str] = _split_dgs_line(
                                serialized_line
                            )
                            output_parts: List[str] = list()
                            property_index: int
                            for property_index, prop in enumerate(
                                    cls.properties_list
                            ):
                                if prop.name == "s:Rin":
                                    pass
                                else:
                                    output_parts.append(
                                        serialized_parts[property_index]
                                    )
                            f.write(";".join(output_parts) + "\n")
                        else:
                            f.write(serialized_line + "\n")

                    f.write("\n")
