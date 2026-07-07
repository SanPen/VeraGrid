# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
import sys
import os
from pathlib import Path
from typing import Dict, List, Type, Optional, Tuple
from VeraGridEngine.IO.dgs.dgs_objects import *
from VeraGridEngine.basic_structures import Logger


def _populate_from_pf_object(pf_obj: DGSElement, dgs_cls: Type[DGSElement]):
    """
    Populate a DGSElement subclass from a PowerFactory API object,
    using the class schema (properties_list).
    Assumes the DGSElement has an explicit __init__.
    """
    elem = dgs_cls()

    for prop in dgs_cls.properties_list:
        name = prop.name
        value = pf_obj.name
        setattr(elem, name, value)

    return elem


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


class DgsCircuit:
    """Strongly-typed container for a PowerFactory DGS file."""

    _ELEMENT_CLASSES: List[Type[DGSElement]] = [
        General,
        BlkDef,
        BlkFrom,
        BlkGoto,
        BlkRef,
        BlkSig,
        BlkSlot,
        BlkSum,
        ChaRef,
        ChaVec,
        ElmComp,
        ElmDsl,
        ElmBranch,
        ElmAsm,
        ElmCoup,
        ElmFeeder,
        ElmGenstat,
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
        StaSwitch,
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

    _REGISTRY: Dict[str, Type[DGSElement]] = {cls.element_type: cls for cls in _ELEMENT_CLASSES}

    def __init__(self) -> None:
        """

        """
        self._id_counter = 0

        self.generals: List[General] = list()
        self.blkdefs: List[BlkDef] = list()
        self.blkfroms: List[BlkFrom] = list()
        self.blkgotos: List[BlkGoto] = list()
        self.blkrefs: List[BlkRef] = list()
        self.blksigs: List[BlkSig] = list()
        self.blkslots: List[BlkSlot] = list()
        self.blksums: List[BlkSum] = list()
        self.elmcomps: List[ElmComp] = list()
        self.elmdsls: List[ElmDsl] = list()
        self.elmbranches: List[ElmBranch] = list()
        self.charefs: List[ChaRef] = list()
        self.chavecs: List[ChaVec] = list()
        self.elmasms: List[ElmAsm] = list()
        self.elmcoups: List[ElmCoup] = list()
        self.elmfeeders: List[ElmFeeder] = list()
        self.elmgenstats: List[ElmGenstat] = list()
        self.elmlnes: List[ElmLne] = list()
        self.elmtows: List[ElmTow] = list()
        self.elmsinds: List[ElmSind] = list()
        self.elmlnesecs: List[ElmLnesec] = list()
        self.elmvacs: List[ElmVac] = list()
        self.elmlods: List[ElmLod] = list()
        self.elmlodlvs: List[ElmLodlv] = list()
        self.elmlodlvps: List[ElmLodlvp] = list()
        self.elmnets: List[ElmNet] = list()
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
        self.staswitchs: List[StaSwitch] = list()
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
            BlkFrom: self.blkfroms,
            BlkGoto: self.blkgotos,
            BlkRef: self.blkrefs,
            BlkSig: self.blksigs,
            BlkSlot: self.blkslots,
            BlkSum: self.blksums,
            ChaRef: self.charefs,
            ChaVec: self.chavecs,
            ElmComp: self.elmcomps,
            ElmDsl: self.elmdsls,
            ElmBranch: self.elmbranches,
            ElmAsm: self.elmasms,
            ElmCoup: self.elmcoups,
            ElmFeeder: self.elmfeeders,
            ElmGenstat: self.elmgenstats,
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
            StaSwitch: self.staswitchs,
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

    def parse_dgs(self, path: str):
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
                    current_cls = self._REGISTRY.get(element_type)

                else:
                    # Data line
                    if current_cls is not None:
                        obj = current_cls.parse_line(line=line, header_map=header_map)

                        if obj is not None:
                            objects_lst = self._CLASS_TO_LIST[current_cls]
                            objects_lst.append(obj)

    def write_dgs(self, path: str):
        """
        Write the circuit back to a DGS file.
        """
        path2 = Path(path)

        with path2.open("w", encoding="utf-8") as f:

            comment = "*" * 80 + "\n"
            comment += "* Created with VeraGrid\n"
            comment += "*" * 80 + "\n"
            f.write(comment + "\n")

            for cls in self._ELEMENT_CLASSES:
                objects: List[DGSElement] = self._CLASS_TO_LIST[cls]

                if len(objects) > 0:

                    header = "$$" + cls.element_type + ";" + ";".join(
                        f"{p.name}({p.dgs_type})" for p in cls.properties_list
                    )
                    f.write(header + "\n")

                    comment = "*" * 80 + "\n"
                    for prp in objects[0].properties_list:
                        comment += f"* {prp.name}: {prp.dgs_type}: {prp.description}\n"

                    comment += "*" * 80
                    f.write(comment + "\n")

                    for obj in objects:
                        f.write(obj.to_dgs_line() + "\n")

                    f.write("\n")

    def from_api(self, study_case_name: str | None = None, pf_path: str = "") -> None:
        """
        Populate this (empty) PfCircuit from an active PowerFactory application.
        Assumes:
        - self is empty (no existing elements)
        - schema registries (_ELEMENT_CLASSES, _CLASS_TO_LIST) are complete
        :param study_case_name: case name if any
        :param pf_path: PowerFactory path
        :return:
        """
        if pf_path == "":
            pf_path = r"C:\Program Files\DIgSILENT\PowerFactory 2025 SP1"
        os.environ["PATH"] = pf_path + ";" + os.environ["PATH"]
        python_folder = f"{sys.version_info.major}.{sys.version_info.minor}"
        module_folder = os.path.join(pf_path, "Python", python_folder)

        if not os.path.exists(module_folder):
            print(f"PowerFactory path for the compatible module not found: {module_folder}")

        # add the pf path to the system path
        sys.path.append(pf_path)
        sys.path.append(module_folder)

        # Obtain PowerFactory application ------------------------------------------------------------------------------
        try:
            import powerfactory as pf
            print(f"loaded PowerFactory version {pf.__version__}")
        except ImportError as e:
            print("PowerFactory Python module not available. "
                  "Ensure this is executed inside a PowerFactory Python environment.", str(e))
            return None

        try:
            app = pf.GetApplicationExt()
        except pf.ExitError as error:
            print(error)
            print('error.code = %d' % error.code)
            return None

        except RuntimeError as e:
            print("Failed to obtain PowerFactory application. "
                  "Ensure PowerFactory is running and a project is open.", str(e))
            return None

        # Activate study case  -----------------------------------------------------------------------------------------

        try:
            project = app.GetActiveProject()
        except RuntimeError as e:
            print("No active PowerFactory project.", str(e))
            return None

        if project is None:
            print("No active PowerFactory project.")
            return None

        # Fetch all study cases
        try:
            cases = project.GetContents("*.IntCase", recursive=True)
        except RuntimeError as e:
            print("Failed to retrieve study cases.", str(e))
            return None

        if not cases:
            print("No study cases found in the project.")
            return None

        active_case = None

        if study_case_name is not None:
            for case in cases:
                if case.loc_name == study_case_name:
                    active_case = case
                    break

            if active_case is None:
                print(f"Study case '{study_case_name}' not found in project.")
                return None

        else:
            # Use currently active case, if any
            try:
                active_case = app.GetActiveStudyCase()
            except RuntimeError:
                active_case = None

            if active_case is None:
                print("No study case is active. Please specify study_case_name explicitly.")
                return None

        # Activate selected case
        try:
            active_case.Activate()
        except RuntimeError as e:
            print(f"Failed to activate study case '{active_case.loc_name}'.", str(e))
            return None

        # Iterate over all known DGSElement subclasses
        for dgs_cls in self._ELEMENT_CLASSES:
            pf_class_name = dgs_cls.element_type

            try:
                pf_objects = app.GetCalcRelevantObjects(f"*.{pf_class_name}")
            except (RuntimeError, AttributeError):
                pf_objects = list()

            if pf_objects:
                target_list = self._CLASS_TO_LIST[dgs_cls]

                for pf_obj in pf_objects:
                    elem = _populate_from_pf_object(pf_obj, dgs_cls)
                    target_list.append(elem)
