# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import Any, Dict, List


class DgsProperty:
    """
    Dgs Property
    """

    def __init__(self, name: str, dgs_type: str, description: str, py_name: str):
        self.name = name
        self.dgs_type = dgs_type
        self.description = description
        self.py_name = py_name

        if dgs_type.startswith("b"):  # boolean
            self.py_type = bool
            self.default_value = False

        elif dgs_type.startswith("i"):  # integer
            self.py_type = int
            self.default_value = 0

        elif dgs_type.startswith("r"):  # real/float
            self.py_type = float
            self.default_value = 0.0

        elif dgs_type.startswith("a"):  # string
            self.py_type = str
            self.default_value = ""

        elif dgs_type.startswith("p"):  # object reference
            self.py_type = str
            self.default_value = None

        else:
            # Unknown/rare types: keep as string by default
            self.py_type = str
            self.default_value = None

    def parse(self, raw: str) -> str | int | bool | float | None:
        """

        :param raw: incoming value
        :return:
        """
        if raw is None:
            return self.default_value

        raw = raw.strip()

        # PowerFactory placeholders / missing values
        if raw == "" or raw == "*":
            return self.default_value

        # Boolean parsing
        if self.py_type is bool:
            v = raw.strip().lower()
            if v in {"1", "true", "t", "yes", "y"}:
                return True
            elif v in {"0", "false", "f", "no", "n"}:
                return False
            else:
                # Unexpected encoding → fallback
                return self.default_value

        # Numeric parsing (int/float) with decimal comma
        if self.py_type in (int, float):
            raw_norm = raw.replace(",", ".")
            try:
                if self.py_type is int:
                    # Some PF fields may show "1.0" for ints; tolerate that
                    return int(float(raw_norm))
                else:
                    return float(raw_norm)
            except ValueError:
                return self.default_value

        # String/reference
        return raw

    def format(self, value: Any) -> str:
        """

        :param value:
        :return:
        """
        if value is None:
            return ''
        if self.dgs_type == 'b':
            return '1' if bool(value) else '0'
        return str(value)


class DGSElement:
    """
    Base class
    """
    element_type: str
    properties_list: List[DgsProperty]
    properties: Dict[str, DgsProperty]

    def __init_subclass__(cls):
        cls.properties = {p.name: p for p in cls.properties_list}

    @classmethod
    def parse_line(cls, line: str, header_map: dict[str, int]):
        """
        Parse a DGS data line using a header-derived column map.

        Parameters
        ----------
        line : str
            Raw data line from DGS
        header_map : dict[str, int]
            Mapping {property_name -> column_index}
            derived from the $$ header line
        """
        parts = line.rstrip('\n').split(';')
        obj = cls()

        for prop in cls.properties_list:

            idx = header_map.get(prop.name, None)

            # Fix ID vs FID thing, internally it is always ID, and we handle the FID issue
            if idx is None and prop.name == "ID":
                idx = header_map.get("FID", None)

            if idx is not None:

                if -1 < idx < len(parts):
                    raw = parts[idx]
                    value = prop.parse(raw)
                    setattr(obj, prop.py_name, value)
                else:
                    # Column declared but missing in this line
                    pass
            else:
                # Property not present in this DGS version
                pass

        return obj

    def to_dgs_line(self) -> str:
        """
        Create DGS line
        :return:
        """
        return ';'.join(p.format(getattr(self, p.py_name)) for p in self.properties_list)

    def __repr__(self):
        """

        :return:
        """
        if hasattr(self, "loc_name"):
            return getattr(self, "loc_name")
        else:
            return getattr(self, "ID")


class ChaRef(DGSElement):
    element_type = 'ChaRef'
    properties_list = [
        DgsProperty('ID', 'a:40', 'DGS field ID (a:40)', py_name='ID'),
        DgsProperty('loc_name', 'a:40', 'DGS field loc_name (a:40)', py_name='loc_name'),
        DgsProperty('fold_id', 'p', 'DGS field fold_id (p)', py_name='fold_id'),
    ]

    def __init__(self) -> None:
        self.ID: str = ""
        self.loc_name: str = ""
        self.fold_id: str = ""


class ChaVec(DGSElement):
    element_type = 'ChaVec'
    properties_list = [
        DgsProperty('ID', 'a:40', 'DGS field ID (a:40)', py_name='ID'),
        DgsProperty('loc_name', 'a:40', 'DGS field loc_name (a:40)', py_name='loc_name'),
        DgsProperty('fold_id', 'p', 'DGS field fold_id (p)', py_name='fold_id'),
        DgsProperty('scale', 'p', 'DGS field scale (p)', py_name='scale'),
        DgsProperty('usage', 'i', 'DGS field usage (i)', py_name='usage'),
        DgsProperty('approx', 'i', 'DGS field approx (i)', py_name='approx'),
        DgsProperty('vector:SIZEROW', 'i', 'DGS field vector:SIZEROW (i)', py_name='vector_SIZEROW'),
        DgsProperty('vector:0', 'r', 'DGS field vector:0 (r)', py_name='vector_0'),
        DgsProperty('vector:1', 'r', 'DGS field vector:1 (r)', py_name='vector_1'),
        DgsProperty('vector:2', 'r', 'DGS field vector:2 (r)', py_name='vector_2'),
    ]

    def __init__(self) -> None:
        self.ID: str = ""
        self.loc_name: str = ""
        self.fold_id: str = ""
        self.scale: str = ""
        self.usage: int = 0
        self.approx: int = 0
        self.vector_SIZEROW: int = 0
        self.vector_0: float = 0.0
        self.vector_1: float = 0.0
        self.vector_2: float = 0.0


class ElmComp(DGSElement):
    element_type = 'ElmComp'
    properties_list = [
        DgsProperty('ID', 'a:40', 'DGS field ID (a:40)', py_name='ID'),
        DgsProperty('loc_name', 'a', 'DGS field loc_name (a)', py_name='loc_name'),
        DgsProperty('fold_id', 'p', 'DGS field fold_id (p)', py_name='fold_id'),
        DgsProperty('outserv', 'i', 'DGS field outserv (i)', py_name='outserv'),
        DgsProperty('typ_id', 'p', 'DGS field typ_id (p)', py_name='typ_id'),
    ]

    def __init__(self) -> None:
        self.ID: str = ""
        self.loc_name: str = ""
        self.fold_id: str = ""
        self.typ_id: str = ""
        self.outserv: int = 0


class ElmDsl(DGSElement):
    element_type = 'ElmDsl'
    properties_list = [
        DgsProperty('ID', 'a:40', 'DGS field ID (a:40)', py_name='ID'),
        DgsProperty('loc_name', 'a', 'DGS field loc_name (a)', py_name='loc_name'),
        DgsProperty('fold_id', 'p', 'DGS field fold_id (p)', py_name='fold_id'),
        DgsProperty('outserv', 'i', 'DGS field outserv (i)', py_name='outserv'),
        DgsProperty('typ_id', 'p', 'DGS field typ_id (p)', py_name='typ_id'),
    ]

    def __init__(self) -> None:
        self.ID: str = ""
        self.loc_name: str = ""
        self.fold_id: str = ""
        self.typ_id: str = ""
        self.outserv: int = 0


class ElmAsm(DGSElement):
    element_type = 'ElmAsm'
    properties_list = [
        DgsProperty('ID', 'a:40', 'DGS field ID (a:40)', py_name='ID'),
        DgsProperty('loc_name', 'a', 'DGS field loc_name (a)', py_name='loc_name'),
        DgsProperty('fold_id', 'p', 'DGS field fold_id (p)', py_name='fold_id'),
        DgsProperty('typ_id', 'p', 'DGS field typ_id (p)', py_name='typ_id'),
        DgsProperty('chr_name', 'a', 'DGS field chr_name (a)', py_name='chr_name'),
        DgsProperty('i_mot', 'i', 'DGS field i_mot (i)', py_name='i_mot'),
        DgsProperty('ngnum', 'i', 'DGS field ngnum (i)', py_name='ngnum'),
        DgsProperty('outserv', 'i', 'DGS field outserv (i)', py_name='outserv'),
        DgsProperty('pgini', 'r', 'DGS field pgini (r)', py_name='pgini'),
        DgsProperty('qgini', 'r', 'DGS field qgini (r)', py_name='qgini'),
    ]

    def __init__(self) -> None:
        self.ID: str = ""
        self.loc_name: str = ""
        self.fold_id: str = ""
        self.typ_id: str = ""
        self.chr_name: str = ""
        self.i_mot: int = 0
        self.ngnum: int = 0
        self.outserv: int = 0
        self.pgini: float = 0.0
        self.qgini: float = 0.0


class ElmCoup(DGSElement):
    element_type = 'ElmCoup'
    properties_list = [
        DgsProperty('ID', 'a:40', 'DGS field ID (a:40)', py_name='ID'),
        DgsProperty('loc_name', 'a', 'DGS field loc_name (a)', py_name='loc_name'),
        DgsProperty('fold_id', 'p', 'DGS field fold_id (p)', py_name='fold_id'),
        DgsProperty('typ_id', 'p', 'DGS field typ_id (p)', py_name='typ_id'),
        DgsProperty('chr_name', 'a', 'DGS field chr_name (a)', py_name='chr_name'),
        DgsProperty('aUsage', 'a', 'DGS field aUsage (a)', py_name='aUsage'),
        DgsProperty('nneutral', 'i', 'DGS field nneutral (i)', py_name='nneutral'),
        DgsProperty('nphase', 'i', 'DGS field nphase (i)', py_name='nphase'),
        DgsProperty('on_off', 'i', 'DGS field on_off (i)', py_name='on_off'),
        DgsProperty('for_name', 'a:50', 'DGS field for_name (a:50)', py_name='for_name'),
    ]

    def __init__(self) -> None:
        self.ID: str = ""
        self.loc_name: str = ""
        self.fold_id: str = ""
        self.typ_id: str = ""
        self.chr_name: str = ""
        self.aUsage: str = ""
        self.nneutral: int = 0
        self.nphase: int = 3
        self.on_off: int = 0
        self.for_name: str = ""


class ElmFeeder(DGSElement):
    element_type = 'ElmFeeder'
    properties_list = [
        DgsProperty('ID', 'a:40', 'DGS field ID (a:40)', py_name='ID'),
        DgsProperty('loc_name', 'a:40', 'DGS field loc_name (a:40)', py_name='loc_name'),
        DgsProperty('fold_id', 'p', 'DGS field fold_id (p)', py_name='fold_id'),
        DgsProperty('obj_id', 'p', 'DGS field obj_id (p)', py_name='obj_id'),
        DgsProperty('iorient', 'i', 'DGS field iorient (i)', py_name='iorient'),
        DgsProperty('i_scale', 'i', 'DGS field i_scale (i)', py_name='i_scale'),
        DgsProperty('Iset', 'r', 'DGS field Iset (r)', py_name='Iset'),
        DgsProperty('icolor', 'i', 'DGS field icolor (i)', py_name='icolor'),
        DgsProperty('outserv', 'i', 'DGS field outserv (i)', py_name='outserv'),
    ]

    def __init__(self) -> None:
        self.ID: str = ""
        self.loc_name: str = ""
        self.fold_id: str = ""
        self.obj_id: str = ""
        self.iorient: int = 0
        self.i_scale: int = 0
        self.Iset: float = 0.0
        self.icolor: int = 0
        self.outserv: int = 0


class ElmGenstat(DGSElement):
    element_type = 'ElmGenstat'
    properties_list = [
        DgsProperty('ID', 'a:40', 'DGS field ID (a:40)', py_name='ID'),
        DgsProperty('loc_name', 'a:40', 'DGS field loc_name (a:40)', py_name='loc_name'),
        DgsProperty('fold_id', 'p', 'DGS field fold_id (p)', py_name='fold_id'),
        DgsProperty('bus1', 'p', 'DGS field bus1 (p)', py_name='bus1'),
        DgsProperty('outserv', 'i', 'DGS field outserv (i)', py_name='outserv'),
        DgsProperty('sgn', 'r', 'DGS field sgn (r)', py_name='sgn'),
        DgsProperty('cosn', 'r', 'DGS field cosn (r)', py_name='cosn'),
        DgsProperty('ngnum', 'i', 'DGS field ngnum (i)', py_name='ngnum'),
        DgsProperty('pgini', 'r', 'DGS field pgini (r)', py_name='pgini'),
        DgsProperty('qgini', 'r', 'DGS field qgini (r)', py_name='qgini'),
        DgsProperty('av_mode', 'a', 'DGS field av_mode (a)', py_name='av_mode'),
        DgsProperty('ip_ctrl', 'i', 'DGS field ip_ctrl (i)', py_name='ip_ctrl'),
        DgsProperty('cCategory', 'a:40', 'plant types', py_name='cCategory'),
        DgsProperty('c_pmod', 'a:40', 'plant model', py_name='c_pmod'),
    ]

    def __init__(self) -> None:
        self.ID: str = ""
        self.loc_name: str = ""
        self.fold_id: str = ""
        self.bus1: str = ""
        self.outserv: int = 0
        self.sgn: float = 0.0
        self.cosn: float = 0.0
        self.ngnum: int = 0
        self.pgini: float = 0.0
        self.qgini: float = 0.0
        self.av_mode: str = ""
        self.ip_ctrl: int = 0
        self.cCategory: str = ""
        self.c_pmod: str = ""


class ElmLne(DGSElement):
    element_type = 'ElmLne'
    properties_list = [
        DgsProperty('ID', 'a:40', 'DGS field ID (a:40)', py_name='ID'),
        DgsProperty('loc_name', 'a:40', 'DGS field loc_name (a:40)', py_name='loc_name'),
        DgsProperty('fold_id', 'p', 'DGS field fold_id (p)', py_name='fold_id'),
        DgsProperty('typ_id', 'p', 'DGS field typ_id (p)', py_name='typ_id'),
        DgsProperty('dline', 'r', 'DGS field dline (r)', py_name='dline'),
        DgsProperty('chr_name', 'a:20', 'DGS field chr_name (a:20)', py_name='chr_name'),
        DgsProperty('fline', 'r', 'Derating factor', py_name='fline'),
        DgsProperty('outserv', 'i', 'DGS field outserv (i)', py_name='outserv'),
        DgsProperty('pStoch', 'p', 'DGS field pStoch (p)', py_name='pStoch'),
        DgsProperty('for_name', 'a:50', 'DGS field for_name (a:50)', py_name='for_name'),
        DgsProperty('GPScoords:SIZEROW', 'i', 'DGS field GPScoords:SIZEROW (i)', py_name='GPScoords_SIZEROW'),
        DgsProperty('GPScoords:SIZECOL', 'i', 'DGS field GPScoords:SIZECOL (i)', py_name='GPScoords_SIZECOL'),
        DgsProperty('nlnum', 'i', 'DGS field nlnum (i)', py_name='nlnum'),
        DgsProperty('inAir', 'i', 'DGS field inAir (i)', py_name='inAir'),
    ]

    def __init__(self) -> None:
        self.ID: str = ""
        self.loc_name: str = ""
        self.fold_id: str = ""
        self.typ_id: str = ""
        self.dline: float = 0.0
        self.chr_name: str = ""
        self.fline: float = 1.0
        self.outserv: int = 0
        self.pStoch: str = ""
        self.for_name: str = ""
        self.GPScoords_SIZEROW: int = 0
        self.GPScoords_SIZECOL: int = 0
        self.nlnum: int = 1
        self.inAir: int = 0


class ElmSind(DGSElement):
    element_type = 'ElmSind'
    properties_list = [
        # test_export_v5.dgs uses FID(...) not ID(...)
        DgsProperty('FID', 'a:40', 'DGS field FID (a:40)', py_name='ID'),
        # Optional alias (harmless if missing)
        DgsProperty('ID', 'a:40', 'DGS field ID (a:40)', py_name='ID'),

        DgsProperty('OP', 'a:1', 'DGS field OP (a:1)', py_name='OP'),
        DgsProperty('loc_name', 'a:80', 'Name', py_name='loc_name'),
        DgsProperty('for_name', 'a:100', 'Foreign Key', py_name='for_name'),
        DgsProperty('fold_id', 'p', 'In Folder', py_name='fold_id'),

        DgsProperty('ucn', 'r', 'Rated Voltage in kV', py_name='ucn'),
        DgsProperty('Sn', 'r', 'Rated Power in MVA', py_name='Sn'),
        DgsProperty('uk', 'r', 'Short-Circuit Voltage uk in %', py_name='uk'),
        DgsProperty('Pcu', 'r', 'Copper Losses in kW', py_name='Pcu'),

        DgsProperty('outserv', 'i', 'Out of Service', py_name='outserv'),
    ]

    def __init__(self):
        self.ID: str = ""
        self.OP: str = ""
        self.loc_name: str = ""
        self.for_name: str = ""
        self.fold_id: str = ""
        self.typ_id: str = ""

        self.ucn: float = 0.0
        self.Sn: float = 0.0
        self.uk: float = 0.0
        self.Pcu: float = 0.0

        self.outserv: int = 0


class TypSind(DGSElement):
    """PowerFactory Series Reactor type (TypSind)."""
    element_type = 'TypSind'
    properties_list = [
        DgsProperty('ID', 'a:40', 'DGS field ID (a:40)', py_name='ID'),
        DgsProperty('loc_name', 'a:40', 'DGS field loc_name (a:40)', py_name='loc_name'),
        DgsProperty('fold_id', 'p', 'DGS field fold_id (p)', py_name='fold_id'),

        # Type impedance parameters (same naming as ElmSind in many exports)
        DgsProperty('Re', 'r', 'Type series resistance (Re)', py_name='Re'),
        DgsProperty('Xe', 'r', 'Type series reactance (Xe)', py_name='Xe'),
    ]

    def __init__(self) -> None:
        self.ID: str = ""
        self.loc_name: str = ""
        self.fold_id: str = ""
        self.Re: float = 0.0
        self.Xe: float = 0.0


class ElmLnesec(DGSElement):
    element_type = 'ElmLnesec'
    properties_list = [
        DgsProperty('ID', 'a:40', 'DGS field ID (a:40)', py_name='ID'),
        DgsProperty('loc_name', 'a', 'DGS field loc_name (a)', py_name='loc_name'),
        DgsProperty('fold_id', 'p', 'DGS field fold_id (p)', py_name='fold_id'),
        DgsProperty('typ_id', 'p', 'DGS field typ_id (p)', py_name='typ_id'),
        DgsProperty('chr_name', 'a', 'DGS field chr_name (a)', py_name='chr_name'),
        DgsProperty('dline', 'r', 'DGS field dline (r)', py_name='dline'),
        DgsProperty('fline', 'r', 'DGS field fline (r)', py_name='fline'),
        DgsProperty('index', 'r', 'DGS field index (r)', py_name='index'),
    ]

    def __init__(self) -> None:
        self.ID: str = ""
        self.loc_name: str = ""
        self.fold_id: str = ""
        self.typ_id: str = ""
        self.chr_name: str = ""
        self.dline: float = 0.0
        self.fline: float = 0.0
        self.index: float = 0.0


class ElmLod(DGSElement):
    element_type = 'ElmLod'
    properties_list = [
        DgsProperty('ID', 'a:40', 'DGS field ID (a:40)', py_name='ID'),
        DgsProperty('loc_name', 'a:40', 'DGS field loc_name (a:40)', py_name='loc_name'),
        DgsProperty('fold_id', 'p', 'DGS field fold_id (p)', py_name='fold_id'),
        DgsProperty('typ_id', 'p', 'DGS field typ_id (p)', py_name='typ_id'),
        DgsProperty('chr_name', 'a:20', 'DGS field chr_name (a:20)', py_name='chr_name'),
        DgsProperty('plini', 'r', 'DGS field plini (r)', py_name='plini'),
        DgsProperty('qlini', 'r', 'DGS field qlini (r)', py_name='qlini'),
        DgsProperty('scale0', 'r', 'DGS field scale0 (r)', py_name='scale0'),
        DgsProperty('outserv', 'i', 'DGS field outserv (i)', py_name='outserv'),
        DgsProperty('for_name', 'a:50', 'DGS field for_name (a:50)', py_name='for_name'),
        DgsProperty('mode_inp', 'a:3', 'DGS field mode_inp (a:3)', py_name='mode_inp'),
        DgsProperty('slini', 'r', 'DGS field slini (r)', py_name='slini'),
        DgsProperty('coslini', 'r', 'DGS field coslini (r)', py_name='coslini'),
        DgsProperty('pf_recap', 'i', 'DGS field pf_recap (i)', py_name='pf_recap'),
        DgsProperty('i_scale', 'i', 'DGS field i_scale (i)', py_name='i_scale'),
        DgsProperty('classif', 'a:20', 'DGS field classif (a:20)', py_name='classif'),
    ]

    def __init__(self) -> None:
        self.ID: str = ""
        self.loc_name: str = ""
        self.fold_id: str = ""
        self.typ_id: str = ""
        self.chr_name: str = ""
        self.plini: float = 0.0
        self.qlini: float = 0.0
        self.scale0: float = 0.0
        self.outserv: int = 0
        self.for_name: str = ""
        self.mode_inp: str = ""
        self.slini: float = 0.0
        self.coslini: float = 0.0
        self.pf_recap: int = 0
        self.i_scale: int = 0
        self.classif: str = ""


class ElmLodlv(DGSElement):
    element_type = 'ElmLodlv'
    properties_list = [
        DgsProperty('ID', 'a:40', 'DGS field ID (a:40)', py_name='ID'),
        DgsProperty('loc_name', 'a', 'DGS field loc_name (a)', py_name='loc_name'),
        DgsProperty('fold_id', 'p', 'DGS field fold_id (p)', py_name='fold_id'),
        DgsProperty('typ_id', 'p', 'DGS field typ_id (p)', py_name='typ_id'),
        DgsProperty('chr_name', 'a', 'DGS field chr_name (a)', py_name='chr_name'),
        DgsProperty('for_name', 'a', 'DGS field for_name (a)', py_name='for_name'),
        DgsProperty('ulini', 'r', 'DGS field ulini (r)', py_name='ulini'),
    ]

    def __init__(self) -> None:
        self.ID: str = ""
        self.loc_name: str = ""
        self.fold_id: str = ""
        self.typ_id: str = ""
        self.chr_name: str = ""
        self.for_name: str = ""
        self.ulini: float = 0.0


class ElmLodlvp(DGSElement):
    element_type = 'ElmLodlvp'
    properties_list = [
        DgsProperty('ID', 'a:40', 'DGS field ID (a:40)', py_name='ID'),
        DgsProperty('loc_name', 'a', 'DGS field loc_name (a)', py_name='loc_name'),
        DgsProperty('fold_id', 'p', 'DGS field fold_id (p)', py_name='fold_id'),
        DgsProperty('typ_id', 'p', 'DGS field typ_id (p)', py_name='typ_id'),
        DgsProperty('chr_name', 'a', 'DGS field chr_name (a)', py_name='chr_name'),
        DgsProperty('for_name', 'a', 'DGS field for_name (a)', py_name='for_name'),
        DgsProperty('lneposkm', 'r', 'DGS field lneposkm (r)', py_name='lneposkm'),
        DgsProperty('outserv', 'i', 'DGS field outserv (i)', py_name='outserv'),
        DgsProperty('ulini', 'r', 'DGS field ulini (r)', py_name='ulini'),
    ]

    def __init__(self) -> None:
        self.ID: str = ""
        self.loc_name: str = ""
        self.fold_id: str = ""
        self.typ_id: str = ""
        self.chr_name: str = ""
        self.for_name: str = ""
        self.lneposkm: float = 0.0
        self.outserv: int = 0
        self.ulini: float = 0.0


class ElmNet(DGSElement):
    element_type = 'ElmNet'
    properties_list = [
        DgsProperty('ID', 'a:40', 'DGS field ID (a:40)', py_name='ID'),
        DgsProperty('loc_name', 'a:40', 'DGS field loc_name (a:40)', py_name='loc_name'),
        DgsProperty('fold_id', 'p', 'DGS field fold_id (p)', py_name='fold_id'),
        DgsProperty('frnom', 'r', 'Nominal Frequency in Hz', py_name='frnom'),
        DgsProperty('for_name', 'a:50', 'DGS field for_name (a:50)', py_name='for_name'),
        DgsProperty('pDiagram', 'p', 'Diagram in IntGrfnet', py_name='pDiagram'),
    ]

    def __init__(self) -> None:
        self.ID: str = ""
        self.loc_name: str = ""
        self.fold_id: str = ""
        self.frnom: float = 0.0
        self.for_name: str = ""
        self.pDiagram: str = ""


class ElmShnt(DGSElement):
    element_type = 'ElmShnt'
    properties_list = [
        DgsProperty('ID', 'a:40', 'DGS field ID (a:40)', py_name='ID'),
        DgsProperty('loc_name', 'a:40', 'DGS field loc_name (a:40)', py_name='loc_name'),
        DgsProperty('fold_id', 'p', 'DGS field fold_id (p)', py_name='fold_id'),
        DgsProperty('chr_name', 'a:20', 'DGS field chr_name (a:20)', py_name='chr_name'),
        DgsProperty('shtype', 'i', 'DGS field shtype (i)', py_name='shtype'),
        DgsProperty('ushnm', 'r', 'DGS field ushnm (r)', py_name='ushnm'),
        DgsProperty('qcapn', 'r', 'DGS field qcapn (r)', py_name='qcapn'),
        DgsProperty('ncapx', 'i', 'DGS field ncapx (i)', py_name='ncapx'),
        DgsProperty('ncapa', 'i', 'DGS field ncapa (i)', py_name='ncapa'),
        DgsProperty('outserv', 'i', 'DGS field outserv (i)', py_name='outserv'),
        DgsProperty('ctech', 'i', 'DGS field ctech (i)', py_name='ctech'),
        DgsProperty('fres', 'r', 'DGS field fres (r)', py_name='fres'),
        DgsProperty('greaf0', 'r', 'DGS field greaf0 (r)', py_name='greaf0'),
        DgsProperty('iswitch', 'i', 'DGS field iswitch (i)', py_name='iswitch'),
        DgsProperty('qtotn', 'r', 'DGS field qtotn (r)', py_name='qtotn'),
    ]

    def __init__(self) -> None:
        self.ID: str = ""
        self.loc_name: str = ""
        self.fold_id: str = ""
        self.chr_name: str = ""
        self.shtype: int = 0
        self.ushnm: float = 0.0
        self.qcapn: float = 0.0
        self.ncapx: int = 0
        self.ncapa: int = 0
        self.outserv: int = 0
        self.ctech: int = 0
        self.fres: float = 0.0
        self.greaf0: float = 0.0
        self.iswitch: int = 0
        self.qtotn: float = 0.0


class ElmSvs(DGSElement):
    element_type = 'ElmSvs'
    properties_list = [
        DgsProperty('ID', 'a:40', 'DGS field ID (a:40)', py_name='ID'),
        DgsProperty('loc_name', 'a:40', 'DGS field loc_name (a:40)', py_name='loc_name'),
        DgsProperty('fold_id', 'p', 'DGS field fold_id (p)', py_name='fold_id'),
        DgsProperty('chr_name', 'a:20', 'DGS field chr_name (a:20)', py_name='chr_name'),

        # Reactive limits (MVAr @ v=1 p.u.)
        DgsProperty('qmin', 'r', 'DGS field qmin (r)', py_name='qmin'),
        DgsProperty('qmax', 'r', 'DGS field qmax (r)', py_name='qmax'),

        # PF SVS/SVC model-specific fields (kept for completeness)
        DgsProperty('tcrmax', 'r', 'DGS field tcrmax (r)', py_name='tcrmax'),
        DgsProperty('nxcap', 'i', 'DGS field nxcap (i)', py_name='nxcap'),
        DgsProperty('nfixcap', 'i', 'DGS field nfixcap (i)', py_name='nfixcap'),
        DgsProperty('Qfixcap', 'r', 'DGS field Qfixcap (r)', py_name='Qfixcap'),

        # Out of service flag (0/1)
        DgsProperty('outserv', 'i', 'DGS field outserv (i)', py_name='outserv'),

        # Voltage setpoint for controlled operation (p.u.). Not always present in the DGS header.
        # If absent in the file, it will remain at its default value (1.0).
        DgsProperty('usetp', 'r', 'DGS field usetp (r)', py_name='usetp'),
    ]

    def __init__(self) -> None:
        # Identifiers
        self.ID: str = ""
        self.loc_name: str = ""
        self.fold_id: str = ""
        self.chr_name: str = ""

        # Operating limits (MVAr @ v=1 p.u.)
        self.qmin: float = 0.0
        self.qmax: float = 0.0

        # Thyristor controlled reactor max (PF SVC/SVS model-specific, may be unused in VeraGrid)
        self.tcrmax: float = 0.0

        # Step / block data (PF model-specific, may be used to infer an equivalent stepped model)
        self.nxcap: int = 0
        self.nfixcap: int = 0
        self.Qfixcap: float = 0.0

        # Status
        self.outserv: int = 0

        # Voltage setpoint (p.u.) for controlled shunts
        self.usetp: float = 1.0


class ElmSite(DGSElement):
    element_type = 'ElmSite'
    properties_list = [
        DgsProperty('ID', 'a:40', 'DGS field ID (a:40)', py_name='ID'),
        DgsProperty('loc_name', 'a:40', 'DGS field loc_name (a:40)', py_name='loc_name'),
        DgsProperty('for_name', 'a:50', 'DGS field for_name (a:50)', py_name='for_name'),
        DgsProperty('fold_id', 'p', 'DGS field fold_id (p)', py_name='fold_id'),
        DgsProperty('sType', 'a:80', 'DGS field sType (a:80)', py_name='sType'),
        DgsProperty('GPSlat', 'r', 'DGS field GPSlat (r)', py_name='GPSlat'),
        DgsProperty('GPSlon', 'r', 'DGS field GPSlon (r)', py_name='GPSlon'),
    ]

    def __init__(self) -> None:
        self.ID: str = ""
        self.loc_name: str = ""
        self.for_name: str = ""
        self.fold_id: str = ""
        self.sType: str = ""
        self.GPSlat: float = 0.0
        self.GPSlon: float = 0.0


class ElmSubstat(DGSElement):
    element_type = 'ElmSubstat'
    properties_list = [
        DgsProperty('ID', 'a:40', 'DGS field ID (a:40)', py_name='ID'),
        DgsProperty('loc_name', 'a', 'DGS field loc_name (a)', py_name='loc_name'),
        DgsProperty('fold_id', 'p', 'DGS field fold_id (p)', py_name='fold_id'),
        DgsProperty('Unom', 'r', 'DGS field Unom (r)', py_name='Unom'),
        DgsProperty('pRA', 'p', 'DGS field pRA (p)', py_name='pRA'),
        DgsProperty('for_name', 'a:50', 'DGS field for_name (a:50)', py_name='for_name'),
        DgsProperty('sShort', 'a:6', 'DGS field sShort (a:6)', py_name='sShort'),
        DgsProperty('sType', 'a:80', 'DGS field sType (a:80)', py_name='sType'),
        DgsProperty('GPSlat', 'r', 'DGS field GPSlat (r)', py_name='GPSlat'),
        DgsProperty('GPSlon', 'r', 'DGS field GPSlon (r)', py_name='GPSlon'),
    ]

    def __init__(self) -> None:
        self.ID: str = ""
        self.loc_name: str = ""
        self.fold_id: str = ""
        self.Unom: float = 0.0
        self.pRA: str = ""
        self.for_name: str = ""
        self.sShort: str = ""
        self.sType: str = ""
        self.GPSlat: float = 0.0
        self.GPSlon: float = 0.0


class ElmSym(DGSElement):
    element_type = 'ElmSym'
    properties_list = [
        DgsProperty('ID', 'a:40', 'DGS field ID (a:40)', py_name='ID'),
        DgsProperty('loc_name', 'a:40', 'DGS field loc_name (a:40)', py_name='loc_name'),
        DgsProperty('fold_id', 'p', 'DGS field fold_id (p)', py_name='fold_id'),
        DgsProperty('typ_id', 'p', 'DGS field typ_id (p)', py_name='typ_id'),
        DgsProperty('ngnum', 'i', 'DGS field ngnum (i)', py_name='ngnum'),
        DgsProperty('i_mot', 'i', 'DGS field i_mot (i)', py_name='i_mot'),
        DgsProperty('chr_name', 'a:20', 'DGS field chr_name (a:20)', py_name='chr_name'),
        DgsProperty('outserv', 'i', 'DGS field outserv (i)', py_name='outserv'),
        DgsProperty('pgini', 'r', 'DGS field pgini (r)', py_name='pgini'),
        DgsProperty('qgini', 'r', 'DGS field qgini (r)', py_name='qgini'),
        DgsProperty('usetp', 'r', 'DGS field usetp (r)', py_name='usetp'),
        DgsProperty('iv_mode', 'i', 'DGS field iv_mode (i)', py_name='iv_mode'),
        DgsProperty('q_min', 'r', 'DGS field q_min (r)', py_name='q_min'),
        DgsProperty('q_max', 'r', 'DGS field q_max (r)', py_name='q_max'),
        DgsProperty('Pmin_uc', 'r', 'DGS field Pmin_uc (r)', py_name='Pmin_uc'),
        DgsProperty('Pmax_uc', 'r', 'DGS field Pmax_uc (r)', py_name='Pmax_uc'),
        DgsProperty('iqtype', 'i', 'DGS field iqtype (i)', py_name='iqtype'),
        DgsProperty('for_name', 'a:50', 'DGS field for_name (a:50)', py_name='for_name'),
        DgsProperty('cCategory', 'a', 'DGS field cCategory (a)', py_name='cCategory'),
        DgsProperty('cosgini', 'r', 'DGS field cosgini (r)', py_name='cosgini'),
        DgsProperty('pf_recap', 'i', 'DGS field pf_recap (i)', py_name='pf_recap'),
        DgsProperty('av_mode', 'a', 'DGS field av_mode (a)', py_name='av_mode'),
        DgsProperty('phtech', 'i', 'DGS field phtech (i)', py_name='phtech'),
        DgsProperty('phtech', 'i', 'Reference machine', py_name='ip_ctrl'),
        DgsProperty('c_pmod', 'a:40', 'plant model', py_name='c_pmod'),
    ]

    def __init__(self) -> None:
        self.ID: str = ""
        self.loc_name: str = ""
        self.fold_id: str = ""
        self.typ_id: str = ""
        self.ngnum: int = 1
        self.i_mot: int = 0
        self.chr_name: str = ""
        self.outserv: int = 0
        self.pgini: float = 0.0
        self.qgini: float = 0.0
        self.usetp: float = 0.0
        self.iv_mode: int = 0
        self.q_min: float = 0.0
        self.q_max: float = 0.0
        self.Pmin_uc: float = 0.0
        self.Pmax_uc: float = 0.0
        self.iqtype: int = 0
        self.for_name: str = ""
        self.cCategory: str = ""
        self.cosgini: float = 0.0
        self.pf_recap: int = 0
        self.av_mode: str = ""
        self.phtech: int = 0
        self.ip_ctrl: int = 0
        self.c_pmod: str = ""


class ElmTerm(DGSElement):
    """

    *  FID: Unique identifier for DGS file
    *  OP: Operation (C=create, U=update, D=delete, M=merge, I=ignore)
    *  loc_name: Name
    *  fold_id: In Folder
    *  typ_id: Type in TypBar
    *  systype: System Type:AC:DC:AC/BI
    *  iUsage: Usage:Busbar:Junction Node:Internal Node
    *  uknom: Nominal Voltage: Line-Line in kV
    *  unknom: Nominal Voltage: Line-Ground in kV
    *  iminus: Nominal Voltage: DC-Polarity:positive (+):negative (-):neutral
    *  outserv: Out of Service
    *  GPSlat: Geographical Position: Latitude / Northing in deg
    *  GPSlon: Geographical Position: Longitude / Easting in deg
    *  vtarget: Voltage Control: Target Voltage in p.u.

    """
    element_type = 'ElmTerm'
    properties_list = [
        DgsProperty('ID', 'a:40', 'DGS field ID (a:40)', py_name='ID'),
        DgsProperty('loc_name', 'a:40', 'DGS field loc_name (a:40)', py_name='loc_name'),
        DgsProperty('fold_id', 'p', 'DGS field fold_id (p)', py_name='fold_id'),
        DgsProperty('typ_id', 'p', 'DGS field typ_id (p)', py_name='typ_id'),
        DgsProperty('iUsage', 'i', 'DGS field iUsage (i)', py_name='iUsage'),
        DgsProperty('uknom', 'r', 'DGS field uknom (r)', py_name='uknom'),
        DgsProperty('chr_name', 'a:20', 'DGS field chr_name (a:20)', py_name='chr_name'),
        DgsProperty('outserv', 'i', 'DGS field outserv (i)', py_name='outserv'),
        DgsProperty('cpZone', 'p', 'DGS field cpZone (p)', py_name='cpZone'),
        DgsProperty('phtech', 'i', 'DGS field phtech (i)', py_name='phtech'),
        DgsProperty('for_name', 'a:50', 'DGS field for_name (a:50)', py_name='for_name'),
        DgsProperty('systype', 'i', 'DGS field systype (i)', py_name='systype'),
        DgsProperty('unknom', 'r', 'DGS field unknom (r)', py_name='unknom'),
        DgsProperty('iminus', 'i', 'DGS field iminus (i)', py_name='iminus'),
        DgsProperty('GPSlat', 'r', 'DGS field GPSlat (r)', py_name='GPSlat'),
        DgsProperty('GPSlon', 'r', 'DGS field GPSlon (r)', py_name='GPSlon'),
        DgsProperty('vtarget', 'r', 'DGS field vtarget (r)', py_name='vtarget'),
        DgsProperty('m:u', 'r', 'DGS field m:u (r)', py_name='m_u'),
        DgsProperty('m:phiu', 'r', 'DGS field m:phiu (r)', py_name='m_phiu'),
    ]

    def __init__(self) -> None:
        self.ID: str = ""
        self.loc_name: str = ""
        self.fold_id: str = ""
        self.typ_id: str = ""
        self.iUsage: int = 0
        self.uknom: float = 0.0
        self.chr_name: str = ""
        self.outserv: int = 0
        self.phtech: int = 0
        self.for_name: str = ""
        self.systype: int = 0
        self.unknom: float = 0.0
        self.iminus: int = 0
        self.GPSlat: float = 0.0
        self.GPSlon: float = 0.0
        self.vtarget: float = 0.0
        self.m_u: float = 0.0
        self.m_phiu: float = 0.0
        self.cpZone: str = ""


class ElmTr2(DGSElement):
    element_type = 'ElmTr2'
    properties_list = [
        DgsProperty('ID', 'a:40', 'DGS field ID (a:40)', py_name='ID'),
        DgsProperty('loc_name', 'a:40', 'DGS field loc_name (a:40)', py_name='loc_name'),
        DgsProperty('fold_id', 'p', 'DGS field fold_id (p)', py_name='fold_id'),
        DgsProperty('typ_id', 'p', 'DGS field typ_id (p)', py_name='typ_id'),
        DgsProperty('outserv', 'i', 'Out of Service', py_name='outserv'),
        DgsProperty('nntap', 'i', 'Tap Changer 1: Tap Position', py_name='nntap'),
        DgsProperty('sernum', 'a:20', 'Serial Number (a:20)', py_name='sernum'),
        DgsProperty('constr', 'i', 'Year of Construction', py_name='constr'),
        DgsProperty('chr_name', 'a:20', 'DGS field chr_name (a:20)', py_name='chr_name'),
        DgsProperty('cgnd_h', 'i', 'Internal Grounding Impedance, HV Side: Star Point:Connected:Not connected',
                    py_name='cgnd_h'),
        DgsProperty('cgnd_l', 'i', 'Internal Grounding Impedance, LV Side: Star Point:Connected:Not connected',
                    py_name='cgnd_l'),
        DgsProperty('i_auto', 'i', 'Auto Transformer', py_name='i_auto'),
        DgsProperty('ntrcn', 'i', 'Controller, Tap Changer 1: Automatic Tap Changing', py_name='ntrcn'),
        DgsProperty('ratfac', 'r', 'Rating Factor', py_name='ratfac'),
        DgsProperty('for_name', 'a:50', 'DGS field for_name (a:50)', py_name='for_name'),
        DgsProperty('ntnum', 'i', 'DGS field ntnum (i)', py_name='ntnum'),
        DgsProperty('usetp', 'r', 'DGS field usetp (r)', py_name='usetp'),
        DgsProperty('usp_low', 'r', 'DGS field usp_low (r)', py_name='usp_low'),
        DgsProperty('usp_up', 'r', 'DGS field usp_up (r)', py_name='usp_up'),
        DgsProperty('t2ldc', 'i', 'DGS field t2ldc (i)', py_name='t2ldc'),
        DgsProperty('mTaps_SIZEROW', 'i', 'DGS field mTaps:SIZEROW (i)', py_name='mTaps_SIZEROW'),
        DgsProperty('mTaps_SIZECOL', 'i', 'DGS field mTaps:SIZECOL (i)', py_name='mTaps_SIZECOL'),
    ]

    def __init__(self) -> None:
        self.ID: str = ""
        self.loc_name: str = ""
        self.fold_id: str = ""
        self.typ_id: str = ""
        self.outserv: int = 0
        self.nntap: int = 0
        self.sernum: str = ""
        self.constr: int = 0
        self.chr_name: str = ""
        self.cgnd_h: int = 0
        self.cgnd_l: int = 0
        self.i_auto: int = 0
        self.ntrcn: int = 0
        self.ratfac: float = 1.0
        self.for_name: str = ""
        self.ntnum: int = 1
        self.usetp: float = 0.0
        self.usp_low: float = 0.0
        self.usp_up: float = 0.0
        self.t2ldc: int = 0
        self.mTaps_SIZEROW: int = 0
        self.mTaps_SIZECOL: int = 0


class ElmTr3(DGSElement):
    element_type = 'ElmTr3'
    properties_list = [
        DgsProperty('ID', 'a:40', 'DGS field ID (a:40)', py_name='ID'),
        DgsProperty('loc_name', 'a:40', 'DGS field loc_name (a:40)', py_name='loc_name'),
        DgsProperty('fold_id', 'p', 'DGS field fold_id (p)', py_name='fold_id'),
        DgsProperty('typ_id', 'p', 'DGS field typ_id (p)', py_name='typ_id'),
        DgsProperty('outserv', 'i', 'DGS field outserv (i)', py_name='outserv'),
        DgsProperty('nt3nm', 'i', 'DGS field nt3nm (i)', py_name='nt3nm'),
        DgsProperty('n3tap_h', 'i', 'DGS field n3tap_h (i)', py_name='n3tap_h'),
        DgsProperty('n3tap_m', 'i', 'DGS field n3tap_m (i)', py_name='n3tap_m'),
        DgsProperty('n3tap_l', 'i', 'DGS field n3tap_l (i)', py_name='n3tap_l'),
        DgsProperty('chr_name', 'a:20', 'DGS field chr_name (a:20)', py_name='chr_name'),
        DgsProperty('for_name', 'a:50', 'DGS field for_name (a:50)', py_name='for_name'),
        DgsProperty('i_auto_hl', 'i', 'DGS field i_auto_hl (i)', py_name='i_auto_hl'),
        DgsProperty('ictrlside', 'i', 'DGS field ictrlside (i)', py_name='ictrlside'),
        DgsProperty('ntrcn', 'i', 'DGS field ntrcn (i)', py_name='ntrcn'),
        DgsProperty('t3ldc', 'i', 'DGS field t3ldc (i)', py_name='t3ldc'),
        DgsProperty('usetp', 'r', 'DGS field usetp (r)', py_name='usetp'),
        DgsProperty('usp_low', 'r', 'DGS field usp_low (r)', py_name='usp_low'),
        DgsProperty('usp_up', 'r', 'DGS field usp_up (r)', py_name='usp_up'),
        DgsProperty('mTaps:SIZEROW', 'i', 'DGS field mTaps:SIZEROW (i)', py_name='mTaps_SIZEROW'),
        DgsProperty('mTaps:SIZECOL', 'i', 'DGS field mTaps:SIZECOL (i)', py_name='mTaps_SIZECOL'),
        DgsProperty('mTaps:0:0', 'r', 'DGS field mTaps:0:0 (r)', py_name='mTaps_0_0'),
        DgsProperty('mTaps:0:1', 'r', 'DGS field mTaps:0:1 (r)', py_name='mTaps_0_1'),
        DgsProperty('mTaps:0:2', 'r', 'DGS field mTaps:0:2 (r)', py_name='mTaps_0_2'),
        DgsProperty('mTaps:0:3', 'r', 'DGS field mTaps:0:3 (r)', py_name='mTaps_0_3'),
        DgsProperty('mTaps:0:4', 'r', 'DGS field mTaps:0:4 (r)', py_name='mTaps_0_4'),
        DgsProperty('mTaps:0:5', 'r', 'DGS field mTaps:0:5 (r)', py_name='mTaps_0_5'),
        DgsProperty('mTaps:0:6', 'r', 'DGS field mTaps:0:6 (r)', py_name='mTaps_0_6'),
        DgsProperty('mTaps:0:7', 'r', 'DGS field mTaps:0:7 (r)', py_name='mTaps_0_7'),
        DgsProperty('mTaps:1:0', 'r', 'DGS field mTaps:1:0 (r)', py_name='mTaps_1_0'),
        DgsProperty('mTaps:1:1', 'r', 'DGS field mTaps:1:1 (r)', py_name='mTaps_1_1'),
        DgsProperty('mTaps:1:2', 'r', 'DGS field mTaps:1:2 (r)', py_name='mTaps_1_2'),
        DgsProperty('mTaps:1:3', 'r', 'DGS field mTaps:1:3 (r)', py_name='mTaps_1_3'),
        DgsProperty('mTaps:1:4', 'r', 'DGS field mTaps:1:4 (r)', py_name='mTaps_1_4'),
        DgsProperty('mTaps:1:5', 'r', 'DGS field mTaps:1:5 (r)', py_name='mTaps_1_5'),
        DgsProperty('mTaps:1:6', 'r', 'DGS field mTaps:1:6 (r)', py_name='mTaps_1_6'),
        DgsProperty('mTaps:1:7', 'r', 'DGS field mTaps:1:7 (r)', py_name='mTaps_1_7'),
        DgsProperty('mTaps:2:0', 'r', 'DGS field mTaps:2:0 (r)', py_name='mTaps_2_0'),
        DgsProperty('mTaps:2:1', 'r', 'DGS field mTaps:2:1 (r)', py_name='mTaps_2_1'),
        DgsProperty('mTaps:2:2', 'r', 'DGS field mTaps:2:2 (r)', py_name='mTaps_2_2'),
        DgsProperty('mTaps:2:3', 'r', 'DGS field mTaps:2:3 (r)', py_name='mTaps_2_3'),
        DgsProperty('mTaps:2:4', 'r', 'DGS field mTaps:2:4 (r)', py_name='mTaps_2_4'),
        DgsProperty('mTaps:2:5', 'r', 'DGS field mTaps:2:5 (r)', py_name='mTaps_2_5'),
        DgsProperty('mTaps:2:6', 'r', 'DGS field mTaps:2:6 (r)', py_name='mTaps_2_6'),
        DgsProperty('mTaps:2:7', 'r', 'DGS field mTaps:2:7 (r)', py_name='mTaps_2_7'),
        DgsProperty('iMeasTap', 'i', 'DGS field iMeasTap (i)', py_name='iMeasTap'),
    ]

    def __init__(self) -> None:
        self.ID: str = ""
        self.loc_name: str = ""
        self.fold_id: str = ""
        self.typ_id: str = ""
        self.outserv: int = 0
        self.nt3nm: int = 0
        self.n3tap_h: int = 0
        self.n3tap_m: int = 0
        self.n3tap_l: int = 0
        self.chr_name: str = ""
        self.for_name: str = ""
        self.i_auto_hl: int = 0
        self.ictrlside: int = 0
        self.ntrcn: int = 0
        self.t3ldc: int = 0
        self.usetp: float = 0.0
        self.usp_low: float = 0.0
        self.usp_up: float = 0.0
        self.mTaps_SIZEROW: int = 0
        self.mTaps_SIZECOL: int = 0
        self.mTaps_0_0: float = 0.0
        self.mTaps_0_1: float = 0.0
        self.mTaps_0_2: float = 0.0
        self.mTaps_0_3: float = 0.0
        self.mTaps_0_4: float = 0.0
        self.mTaps_0_5: float = 0.0
        self.mTaps_0_6: float = 0.0
        self.mTaps_0_7: float = 0.0
        self.mTaps_1_0: float = 0.0
        self.mTaps_1_1: float = 0.0
        self.mTaps_1_2: float = 0.0
        self.mTaps_1_3: float = 0.0
        self.mTaps_1_4: float = 0.0
        self.mTaps_1_5: float = 0.0
        self.mTaps_1_6: float = 0.0
        self.mTaps_1_7: float = 0.0
        self.mTaps_2_0: float = 0.0
        self.mTaps_2_1: float = 0.0
        self.mTaps_2_2: float = 0.0
        self.mTaps_2_3: float = 0.0
        self.mTaps_2_4: float = 0.0
        self.mTaps_2_5: float = 0.0
        self.mTaps_2_6: float = 0.0
        self.mTaps_2_7: float = 0.0
        self.iMeasTap: int = 0


class ElmXnet(DGSElement):
    element_type = 'ElmXnet'
    properties_list = [
        DgsProperty('ID', 'a:40', 'DGS field ID (a:40)', py_name='ID'),
        DgsProperty('loc_name', 'a:40', 'DGS field loc_name (a:40)', py_name='loc_name'),
        DgsProperty('fold_id', 'p', 'DGS field fold_id (p)', py_name='fold_id'),
        DgsProperty('outserv', 'i', 'DGS field outserv (i)', py_name='outserv'),
        DgsProperty('snss', 'r', 'DGS field snss (r)', py_name='snss'),
        DgsProperty('rntxn', 'r', 'DGS field rntxn (r)', py_name='rntxn'),
        DgsProperty('z2tz1', 'r', 'DGS field z2tz1 (r)', py_name='z2tz1'),
        DgsProperty('snssmin', 'r', 'DGS field snssmin (r)', py_name='snssmin'),
        DgsProperty('rntxnmin', 'r', 'DGS field rntxnmin (r)', py_name='rntxnmin'),
        DgsProperty('z2tz1min', 'r', 'DGS field z2tz1min (r)', py_name='z2tz1min'),
        DgsProperty('chr_name', 'a:20', 'DGS field chr_name (a:20)', py_name='chr_name'),
        DgsProperty('bustp', 'a:2', 'DGS field bustp (a:2)', py_name='bustp'),
        DgsProperty('pgini', 'r', 'DGS field pgini (r)', py_name='pgini'),
        DgsProperty('qgini', 'r', 'DGS field qgini (r)', py_name='qgini'),
        DgsProperty('phiini', 'r', 'DGS field phiini (r)', py_name='phiini'),
        DgsProperty('usetp', 'r', 'DGS field usetp (r)', py_name='usetp'),
        DgsProperty('cgnd', 'i', 'DGS field cgnd (i)', py_name='cgnd'),
        DgsProperty('iintgnd', 'i', 'DGS field iintgnd (i)', py_name='iintgnd'),
        DgsProperty('ikssmin', 'r', 'DGS field ikssmin (r)', py_name='ikssmin'),
        DgsProperty('r0tx0', 'r', 'DGS field r0tx0 (r)', py_name='r0tx0'),
        DgsProperty('r0tx0min', 'r', 'DGS field r0tx0min (r)', py_name='r0tx0min'),
    ]

    def __init__(self) -> None:
        self.ID: str = ""
        self.loc_name: str = ""
        self.fold_id: str = ""
        self.outserv: int = 0
        self.snss: float = 0.0
        self.rntxn: float = 0.0
        self.z2tz1: float = 0.0
        self.snssmin: float = 0.0
        self.rntxnmin: float = 0.0
        self.z2tz1min: float = 0.0
        self.chr_name: str = ""
        self.bustp: str = ""
        self.pgini: float = 0.0
        self.qgini: float = 0.0
        self.phiini: float = 0.0
        self.usetp: float = 0.0
        self.cgnd: int = 0
        self.iintgnd: int = 0
        self.ikssmin: float = 0.0
        self.r0tx0: float = 0.0
        self.r0tx0min: float = 0.0


class ElmZone(DGSElement):
    element_type = 'ElmZone'
    properties_list = [
        DgsProperty('ID', 'a:40', 'DGS field ID (a:40)', py_name='ID'),
        DgsProperty('loc_name', 'a:40', 'DGS field loc_name (a:40)', py_name='loc_name'),
        DgsProperty('for_name', 'a:50', 'DGS field for_name (a:50)', py_name='for_name'),
        DgsProperty('fold_id', 'p', 'DGS field fold_id (p)', py_name='fold_id'),
        DgsProperty('icolor', 'i', 'DGS field icolor (i)', py_name='icolor'),
        DgsProperty('curscale', 'r', 'DGS field curscale (r)', py_name='curscale'),
    ]

    def __init__(self) -> None:
        self.ID: str = ""
        self.loc_name: str = ""
        self.for_name: str = ""
        self.fold_id: str = ""
        self.icolor: int = 0
        self.curscale: float = 0.0


class General(DGSElement):
    element_type = 'General'
    properties_list = [
        DgsProperty('ID', 'a:40', 'DGS field ID (a:40)', py_name='ID'),
        DgsProperty('Descr', 'a:40', 'DGS field Descr (a:40)', py_name='Descr'),
        DgsProperty('Val', 'a:40', 'DGS field Val (a:40)', py_name='Val'),
    ]

    def __init__(self) -> None:
        self.ID: str = ""
        self.Descr: str = ""
        self.Val: str = ""


class IntFolder(DGSElement):
    element_type = 'IntFolder'
    properties_list = [
        DgsProperty('ID', 'a:40', 'DGS field ID (a:40)', py_name='ID'),
        DgsProperty('loc_name', 'a', 'DGS field loc_name (a)', py_name='loc_name'),
        DgsProperty('fold_id', 'p', 'DGS field fold_id (p)', py_name='fold_id'),
        DgsProperty('iopt_typ', 'i', 'DGS field iopt_typ (i)', py_name='iopt_typ'),
    ]

    def __init__(self) -> None:
        self.ID: str = ""
        self.loc_name: str = ""
        self.fold_id: str = ""
        self.iopt_typ: int = 0


class IntGrf(DGSElement):
    element_type = 'IntGrf'
    properties_list = [
        DgsProperty('ID', 'a:40', 'DGS field ID (a:40)', py_name='ID'),
        DgsProperty('loc_name', 'a:40', 'DGS field loc_name (a:40)', py_name='loc_name'),
        DgsProperty('fold_id', 'p', 'DGS field fold_id (p)', py_name='fold_id'),
        DgsProperty('iCol', 'i', 'DGS field iCol (i)', py_name='iCol'),
        DgsProperty('iVis', 'i', 'DGS field iVis (i)', py_name='iVis'),
        DgsProperty('iLevel', 'i', 'DGS field iLevel (i)', py_name='iLevel'),
        DgsProperty('rCenterX', 'r', 'DGS field rCenterX (r)', py_name='rCenterX'),
        DgsProperty('rCenterY', 'r', 'DGS field rCenterY (r)', py_name='rCenterY'),
        DgsProperty('sSymNam', 'a:40', 'DGS field sSymNam (a:40)', py_name='sSymNam'),
        DgsProperty('pDataObj', 'p', 'DGS field pDataObj (p)', py_name='pDataObj'),
        DgsProperty('iRot', 'i', 'DGS field iRot (i)', py_name='iRot'),
        DgsProperty('rSizeX', 'r', 'DGS field rSizeX (r)', py_name='rSizeX'),
        DgsProperty('rSizeY', 'r', 'DGS field rSizeY (r)', py_name='rSizeY'),
        DgsProperty('sAttr:SIZEROW', 'i', 'DGS field sAttr:SIZEROW (i)', py_name='sAttr_SIZEROW'),
        DgsProperty('sAttr:0', 'a', 'DGS field sAttr:0 (a)', py_name='sAttr_0'),
        DgsProperty('sAttr:1', 'a', 'DGS field sAttr:1 (a)', py_name='sAttr_1'),
        DgsProperty('sAttr:2', 'a', 'DGS field sAttr:2 (a)', py_name='sAttr_2'),
    ]

    def __init__(self) -> None:
        self.ID: str = ""
        self.loc_name: str = ""
        self.fold_id: str = ""
        self.iCol: int = 0
        self.iVis: int = 0
        self.iLevel: int = 0
        self.rCenterX: float = 0.0
        self.rCenterY: float = 0.0
        self.sSymNam: str = ""
        self.pDataObj: str = ""
        self.iRot: int = 0
        self.rSizeX: float = 0.0
        self.rSizeY: float = 0.0
        self.sAttr_SIZEROW: int = 0
        self.sAttr_0: str = ""
        self.sAttr_1: str = ""
        self.sAttr_2: str = ""


class IntGrfcon(DGSElement):
    element_type = 'IntGrfcon'
    properties_list = [
        DgsProperty('ID', 'a:40', 'DGS field ID (a:40)', py_name='ID'),
        DgsProperty('loc_name', 'a:40', 'DGS field loc_name (a:40)', py_name='loc_name'),
        DgsProperty('fold_id', 'p', 'DGS field fold_id (p)', py_name='fold_id'),
        DgsProperty('rX:SIZEROW', 'i', 'DGS field rX:SIZEROW (i)', py_name='rX_SIZEROW'),
        DgsProperty('rX:0', 'r', 'DGS field rX:0 (r)', py_name='rX_0'),
        DgsProperty('rX:1', 'r', 'DGS field rX:1 (r)', py_name='rX_1'),
        DgsProperty('rX:2', 'r', 'DGS field rX:2 (r)', py_name='rX_2'),
        DgsProperty('rX:3', 'r', 'DGS field rX:3 (r)', py_name='rX_3'),
        DgsProperty('rY:SIZEROW', 'i', 'DGS field rY:SIZEROW (i)', py_name='rY_SIZEROW'),
        DgsProperty('rY:0', 'r', 'DGS field rY:0 (r)', py_name='rY_0'),
        DgsProperty('rY:1', 'r', 'DGS field rY:1 (r)', py_name='rY_1'),
        DgsProperty('rY:2', 'r', 'DGS field rY:2 (r)', py_name='rY_2'),
        DgsProperty('rY:3', 'r', 'DGS field rY:3 (r)', py_name='rY_3'),
        DgsProperty('rX:4', 'r', 'DGS field rX:4 (r)', py_name='rX_4'),
        DgsProperty('rX:5', 'r', 'DGS field rX:5 (r)', py_name='rX_5'),
        DgsProperty('rX:6', 'r', 'DGS field rX:6 (r)', py_name='rX_6'),
        DgsProperty('rX:7', 'r', 'DGS field rX:7 (r)', py_name='rX_7'),
        DgsProperty('rX:8', 'r', 'DGS field rX:8 (r)', py_name='rX_8'),
        DgsProperty('rX:9', 'r', 'DGS field rX:9 (r)', py_name='rX_9'),
        DgsProperty('rY:4', 'r', 'DGS field rY:4 (r)', py_name='rY_4'),
        DgsProperty('rY:5', 'r', 'DGS field rY:5 (r)', py_name='rY_5'),
        DgsProperty('rY:6', 'r', 'DGS field rY:6 (r)', py_name='rY_6'),
        DgsProperty('rY:7', 'r', 'DGS field rY:7 (r)', py_name='rY_7'),
        DgsProperty('rY:8', 'r', 'DGS field rY:8 (r)', py_name='rY_8'),
        DgsProperty('rY:9', 'r', 'DGS field rY:9 (r)', py_name='rY_9'),
    ]

    def __init__(self) -> None:
        self.ID: str = ""
        self.loc_name: str = ""
        self.fold_id: str = ""
        self.rX_SIZEROW: int = 0
        self.rX_0: float = 0.0
        self.rX_1: float = 0.0
        self.rX_2: float = 0.0
        self.rX_3: float = 0.0
        self.rY_SIZEROW: int = 0
        self.rY_0: float = 0.0
        self.rY_1: float = 0.0
        self.rY_2: float = 0.0
        self.rY_3: float = 0.0
        self.rX_4: float = 0.0
        self.rX_5: float = 0.0
        self.rX_6: float = 0.0
        self.rX_7: float = 0.0
        self.rX_8: float = 0.0
        self.rX_9: float = 0.0
        self.rY_4: float = 0.0
        self.rY_5: float = 0.0
        self.rY_6: float = 0.0
        self.rY_7: float = 0.0
        self.rY_8: float = 0.0
        self.rY_9: float = 0.0


class IntGrfnet(DGSElement):
    element_type = 'IntGrfnet'
    properties_list = [
        DgsProperty('ID', 'a:40', 'DGS field ID (a:40)', py_name='ID'),
        DgsProperty('loc_name', 'a:40', 'DGS field loc_name (a:40)', py_name='loc_name'),
        DgsProperty('fold_id', 'p', 'DGS field fold_id (p)', py_name='fold_id'),
        DgsProperty('snap_on', 'i', 'DGS field snap_on (i)', py_name='snap_on'),
        DgsProperty('grid_on', 'i', 'DGS field grid_on (i)', py_name='grid_on'),
        DgsProperty('ortho_on', 'i', 'DGS field ortho_on (i)', py_name='ortho_on'),
        DgsProperty('pDataFolder', 'p', 'DGS field pDataFolder (p)', py_name='pDataFolder'),
    ]

    def __init__(self) -> None:
        self.ID: str = ""
        self.loc_name: str = ""
        self.fold_id: str = ""
        self.snap_on: int = 0
        self.grid_on: int = 0
        self.ortho_on: int = 0
        self.pDataFolder: str = ""


class RelFuse(DGSElement):
    element_type = 'RelFuse'
    properties_list = [
        DgsProperty('ID', 'a:40', 'DGS field ID (a:40)', py_name='ID'),
        DgsProperty('loc_name', 'a', 'DGS field loc_name (a)', py_name='loc_name'),
        DgsProperty('fold_id', 'p', 'DGS field fold_id (p)', py_name='fold_id'),
        DgsProperty('typ_id', 'p', 'DGS field typ_id (p)', py_name='typ_id'),
        DgsProperty('chr_name', 'a', 'DGS field chr_name (a)', py_name='chr_name'),
        DgsProperty('aUsage', 'a', 'DGS field aUsage (a)', py_name='aUsage'),
        DgsProperty('nphase', 'i', 'DGS field nphase (i)', py_name='nphase'),
        DgsProperty('on_off', 'i', 'DGS field on_off (i)', py_name='on_off'),
        DgsProperty('outserv', 'i', 'DGS field outserv (i)', py_name='outserv'),
    ]

    def __init__(self) -> None:
        self.ID: str = ""
        self.loc_name: str = ""
        self.fold_id: str = ""
        self.typ_id: str = ""
        self.chr_name: str = ""
        self.aUsage: str = ""
        self.nphase: int = 3
        self.on_off: int = 0
        self.outserv: int = 0


class StaCubic(DGSElement):
    element_type = 'StaCubic'
    properties_list = [
        DgsProperty('ID', 'a:40', 'DGS field ID (a:40)', py_name='ID'),
        DgsProperty('loc_name', 'a:40', 'DGS field loc_name (a:40)', py_name='loc_name'),
        DgsProperty('fold_id', 'p', 'DGS field fold_id (p)', py_name='fold_id'),
        DgsProperty('chr_name', 'a:20', 'DGS field chr_name (a:20)', py_name='chr_name'),
        DgsProperty('obj_bus', 'i', 'DGS field obj_bus (i)', py_name='obj_bus'),
        DgsProperty('obj_id', 'p', 'DGS field obj_id (p)', py_name='obj_id'),
        DgsProperty('for_name', 'a:50', 'DGS field for_name (a:50)', py_name='for_name'),
        DgsProperty('it2p1', 'i', 'DGS field it2p1 (i)', py_name='it2p1'),
        DgsProperty('it2p2', 'i', 'DGS field it2p2 (i)', py_name='it2p2'),
        DgsProperty('it2p3', 'i', 'DGS field it2p3 (i)', py_name='it2p3'),
    ]

    def __init__(self) -> None:
        self.ID: str = ""
        self.loc_name: str = ""
        self.fold_id: str = ""
        self.chr_name: str = ""
        self.obj_bus: int = 0
        self.obj_id: str = ""
        self.for_name: str = ""
        self.it2p1: int = 0
        self.it2p2: int = 0
        self.it2p3: int = 0


class StaSwitch(DGSElement):
    element_type = 'StaSwitch'
    properties_list = [
        DgsProperty('ID', 'a:40', 'DGS field ID (a:40)', py_name='ID'),
        DgsProperty('loc_name', 'a:40', 'DGS field loc_name (a:40)', py_name='loc_name'),
        DgsProperty('fold_id', 'p', 'DGS field fold_id (p)', py_name='fold_id'),
        DgsProperty('on_off', 'i', 'DGS field on_off (i)', py_name='on_off'),
        DgsProperty('typ_id', 'p', 'DGS field typ_id (p)', py_name='typ_id'),
        DgsProperty('iUse', 'i', 'DGS field iUse (i)', py_name='iUse'),
        DgsProperty('for_name', 'a:50', 'DGS field for_name (a:50)', py_name='for_name'),
        DgsProperty('aUsage', 'a', 'DGS field aUsage (a)', py_name='aUsage'),
    ]

    def __init__(self) -> None:
        self.ID: str = ""
        self.loc_name: str = ""
        self.fold_id: str = ""
        self.on_off: int = 0
        self.typ_id: str = ""
        self.iUse: int = 0
        self.for_name: str = ""
        self.aUsage: str = ""


class TypAsmo(DGSElement):
    element_type = 'TypAsmo'
    properties_list = [
        DgsProperty('ID', 'a:40', 'DGS field ID (a:40)', py_name='ID'),
        DgsProperty('loc_name', 'a', 'DGS field loc_name (a)', py_name='loc_name'),
        DgsProperty('fold_id', 'p', 'DGS field fold_id (p)', py_name='fold_id'),
        DgsProperty('i_mode', 'i', 'DGS field i_mode (i)', py_name='i_mode'),
        DgsProperty('aiazn', 'r', 'DGS field aiazn (r)', py_name='aiazn'),
        DgsProperty('amazn', 'r', 'DGS field amazn (r)', py_name='amazn'),
        DgsProperty('amkzn', 'r', 'DGS field amkzn (r)', py_name='amkzn'),
        DgsProperty('anend', 'r', 'DGS field anend (r)', py_name='anend'),
        DgsProperty('cosn', 'r', 'DGS field cosn (r)', py_name='cosn'),
        DgsProperty('effic', 'r', 'DGS field effic (r)', py_name='effic'),
        DgsProperty('frequ', 'r', 'DGS field frequ (r)', py_name='frequ'),
        DgsProperty('i_cage', 'i', 'DGS field i_cage (i)', py_name='i_cage'),
        DgsProperty('nppol', 'i', 'DGS field nppol (i)', py_name='nppol'),
        DgsProperty('pgn', 'r', 'DGS field pgn (r)', py_name='pgn'),
        DgsProperty('sgn', 'r', 'DGS field sgn (r)', py_name='sgn'),
        DgsProperty('nslty', 'i', 'DGS field nslty (i)', py_name='nslty'),
        DgsProperty('rstr', 'r', 'DGS field rstr (r)', py_name='rstr'),
        DgsProperty('xm', 'r', 'DGS field xm (r)', py_name='xm'),
        DgsProperty('ugn', 'r', 'DGS field ugn (r)', py_name='ugn'),
        DgsProperty('xmrtr', 'r', 'DGS field xmrtr (r)', py_name='xmrtr'),
        DgsProperty('xstr', 'r', 'DGS field xstr (r)', py_name='xstr'),
    ]

    def __init__(self) -> None:
        self.ID: str = ""
        self.loc_name: str = ""
        self.fold_id: str = ""
        self.i_mode: int = 0
        self.aiazn: float = 0.0
        self.amazn: float = 0.0
        self.amkzn: float = 0.0
        self.anend: float = 0.0
        self.cosn: float = 0.0
        self.effic: float = 0.0
        self.frequ: float = 0.0
        self.i_cage: int = 0
        self.nppol: int = 0
        self.pgn: float = 0.0
        self.ugn: float = 0.0
        self.xmrtr: float = 0.0
        self.xstr: float = 0.0
        self.sgn: float = 0.0
        self.nslty: int = 0
        self.rstr: float = 0.0
        self.xm: float = 0.0


class TypFuse(DGSElement):
    element_type = 'TypFuse'
    properties_list = [
        DgsProperty('ID', 'a:40', 'DGS field ID (a:40)', py_name='ID'),
        DgsProperty('loc_name', 'a', 'DGS field loc_name (a)', py_name='loc_name'),
        DgsProperty('fold_id', 'p', 'DGS field fold_id (p)', py_name='fold_id'),
        DgsProperty('frq', 'r', 'DGS field frq (r)', py_name='frq'),
        DgsProperty('irat', 'r', 'DGS field irat (r)', py_name='irat'),
        DgsProperty('urat', 'r', 'DGS field urat (r)', py_name='urat'),
    ]

    def __init__(self) -> None:
        self.ID: str = ""
        self.loc_name: str = ""
        self.fold_id: str = ""
        self.frq: float = 0.0
        self.irat: float = 0.0
        self.urat: float = 0.0


class TypLne(DGSElement):
    element_type = 'TypLne'
    properties_list = [
        DgsProperty('ID', 'a:40', 'DGS field ID (a:40)', py_name='ID'),
        DgsProperty('loc_name', 'a:40', 'DGS field loc_name (a:40)', py_name='loc_name'),
        DgsProperty('fold_id', 'p', 'DGS field fold_id (p)', py_name='fold_id'),
        DgsProperty('uline', 'r', 'DGS field uline (r)', py_name='uline'),
        DgsProperty('sline', 'r', 'DGS field sline (r)', py_name='sline'),
        DgsProperty('aohl_', 'a:3', 'DGS field aohl_ (a:3)', py_name='aohl_'),
        DgsProperty('rline', 'r', 'DGS field rline (r)', py_name='rline'),
        DgsProperty('xline', 'r', 'DGS field xline (r)', py_name='xline'),
        DgsProperty('cline', 'r', 'DGS field cline (r)', py_name='cline'),
        DgsProperty('rline0', 'r', 'DGS field rline0 (r)', py_name='rline0'),
        DgsProperty('xline0', 'r', 'DGS field xline0 (r)', py_name='xline0'),
        DgsProperty('cline0', 'r', 'DGS field cline0 (r)', py_name='cline0'),
        DgsProperty('rtemp', 'r', 'DGS field rtemp (r)', py_name='rtemp'),
        DgsProperty('Ithr', 'r', 'DGS field Ithr (r)', py_name='Ithr'),
        DgsProperty('chr_name', 'a:20', 'DGS field chr_name (a:20)', py_name='chr_name'),
        DgsProperty('nlnph', 'i', 'Phases:1:2:3', py_name='nlnph'),
        DgsProperty('nneutral', 'i', 'DGS field nneutral (i)', py_name='nneutral'),
        DgsProperty('for_name', 'a:50', 'DGS field for_name (a:50)', py_name='for_name'),
        DgsProperty('InomAir', 'r', 'DGS field InomAir (r)', py_name='InomAir'),
        DgsProperty('cohl_', 'i', 'DGS field cohl_ (i)', py_name='cohl_'),
        DgsProperty('tmax', 'r', 'DGS field tmax (r)', py_name='tmax'),
        DgsProperty('systp', 'i', 'DGS field systp (i)', py_name='systp'),
        DgsProperty('frnom', 'r', 'DGS field frnom (r)', py_name='frnom'),
        DgsProperty('mlei', 'a:2', 'DGS field mlei (a:2)', py_name='mlei'),
        DgsProperty('bline', 'r', 'DGS field bline (r)', py_name='bline'),
        DgsProperty('bline0', 'r', 'DGS field bline0 (r)', py_name='bline0'),
    ]

    def __init__(self) -> None:
        self.ID: str = ""
        self.loc_name: str = ""
        self.fold_id: str = ""
        self.uline: float = 0.0
        self.sline: float = 0.0
        self.aohl_: str = "cab"  # allowed values are "cab" and "ohl"
        self.rline: float = 0.0
        self.xline: float = 0.0
        self.cline: float = 0.0
        self.rline0: float = 0.0
        self.xline0: float = 0.0
        self.cline0: float = 0.0
        self.rtemp: float = 20.0
        self.Ithr: float = 0.0
        self.chr_name: str = ""
        self.nlnph: int = 3
        self.nneutral: int = 0
        self.for_name: str = ""
        self.InomAir: float = 0.0
        self.cohl_: int = 0
        self.tmax: float = 80.0
        self.systp: int = 0
        self.frnom: float = 0.0
        self.mlei: str = ""
        self.bline: float = 0.0
        self.bline0: float = 0.0


class TypLod(DGSElement):
    element_type = 'TypLod'
    properties_list = [
        DgsProperty('ID', 'a:40', 'DGS field ID (a:40)', py_name='ID'),
        DgsProperty('loc_name', 'a:40', 'DGS field loc_name (a:40)', py_name='loc_name'),
        DgsProperty('fold_id', 'p', 'DGS field fold_id (p)', py_name='fold_id'),
        DgsProperty('kpu', 'r', 'DGS field kpu (r)', py_name='kpu'),
        DgsProperty('kqu', 'r', 'DGS field kqu (r)', py_name='kqu'),
        DgsProperty('systp', 'i', 'DGS field systp (i)', py_name='systp'),
        DgsProperty('phtech', 'i', 'DGS field phtech (i)', py_name='phtech'),
        DgsProperty('for_name', 'a:50', 'DGS field for_name (a:50)', py_name='for_name'),
        DgsProperty('aP', 'r', 'DGS field aP (r)', py_name='aP'),
        DgsProperty('bP', 'r', 'DGS field bP (r)', py_name='bP'),
        DgsProperty('kpu0', 'r', 'DGS field kpu0 (r)', py_name='kpu0'),
        DgsProperty('kpu1', 'r', 'DGS field kpu1 (r)', py_name='kpu1'),
        DgsProperty('aQ', 'r', 'DGS field aQ (r)', py_name='aQ'),
        DgsProperty('bQ', 'r', 'DGS field bQ (r)', py_name='bQ'),
        DgsProperty('kqu0', 'r', 'DGS field kqu0 (r)', py_name='kqu0'),
        DgsProperty('kqu1', 'r', 'DGS field kqu1 (r)', py_name='kqu1'),
    ]

    def __init__(self) -> None:
        self.ID: str = ""
        self.loc_name: str = ""
        self.fold_id: str = ""
        self.kpu: float = 0.0
        self.kqu: float = 0.0
        self.systp: int = 0
        self.phtech: int = 0
        self.for_name: str = ""
        self.aP: float = 0.0
        self.bP: float = 0.0
        self.kpu0: float = 0.0
        self.kpu1: float = 0.0
        self.aQ: float = 0.0
        self.bQ: float = 0.0
        self.kqu0: float = 0.0
        self.kqu1: float = 0.0


class TypSym(DGSElement):
    element_type = 'TypSym'

    # We comment out the dynamic stuff because it will trigger errors at import
    properties_list = [
        DgsProperty('ID', 'a:40', 'DGS field ID (a:40)', py_name='ID'),
        DgsProperty('loc_name', 'a:40', 'DGS field loc_name (a:40)', py_name='loc_name'),
        DgsProperty('fold_id', 'p', 'DGS field fold_id (p)', py_name='fold_id'),
        DgsProperty('sgn', 'r', 'DGS field sgn (r)', py_name='sgn'),
        DgsProperty('ugn', 'r', 'Rated voltage in kV', py_name='ugn'),
        DgsProperty('cosn', 'r', 'DGS field cosn (r)', py_name='cosn'),
        # DgsProperty('xd', 'r', 'DGS field xd (r)', py_name='xd'),
        # DgsProperty('xq', 'r', 'DGS field xq (r)', py_name='xq'),
        # DgsProperty('xdsss', 'r', 'DGS field xdsss (r)', py_name='xdsss'),
        # DgsProperty('rstr', 'r', 'DGS field rstr (r)', py_name='rstr'),
        # DgsProperty('xdsat', 'r', 'DGS field xdsat (r)', py_name='xdsat'),
        # DgsProperty('satur', 'i', 'DGS field satur (i)', py_name='satur'),
        DgsProperty('Q_min', 'r', 'DGS field Q_min (r)', py_name='Q_min'),
        DgsProperty('Q_max', 'r', 'DGS field Q_max (r)', py_name='Q_max'),
        DgsProperty('q_min', 'r', 'DGS field q_min (r)', py_name='q_min'),
        DgsProperty('q_max', 'r', 'DGS field q_max (r)', py_name='q_max'),
        DgsProperty('for_name', 'a:50', 'DGS field for_name (a:50)', py_name='for_name'),
        DgsProperty('nphase', 'i', 'DGS field nphase (i)', py_name='nphase'),
        # DgsProperty('nslty', 'i', 'DGS field nslty (i)', py_name='nslty'),
        # DgsProperty('x0sy', 'r', 'DGS field x0sy (r)', py_name='x0sy'),
        # DgsProperty('r0sy', 'r', 'DGS field r0sy (r)', py_name='r0sy'),
        # DgsProperty('x2sy', 'r', 'DGS field x2sy (r)', py_name='x2sy'),
        # DgsProperty('r2sy', 'r', 'DGS field r2sy (r)', py_name='r2sy'),
        # DgsProperty('iopt_data', 'i', 'DGS field iopt_data (i)', py_name='iopt_data'),
        # DgsProperty('xds', 'r', 'DGS field xds (r)', py_name='xds'),
        # DgsProperty('xqs', 'r', 'DGS field xqs (r)', py_name='xqs'),
        # DgsProperty('xl', 'r', 'DGS field xl (r)', py_name='xl'),
        # DgsProperty('xdss', 'r', 'DGS field xdss (r)', py_name='xdss'),
        # DgsProperty('xqss', 'r', 'DGS field xqss (r)', py_name='xqss'),
        # DgsProperty('xrlq', 'r', 'DGS field xrlq (r)', py_name='xrlq'),
        # DgsProperty('tds', 'r', 'DGS field tds (r)', py_name='tds'),
        # DgsProperty('tqs', 'r', 'DGS field tqs (r)', py_name='tqs'),
        # DgsProperty('tdss', 'r', 'DGS field tdss (r)', py_name='tdss'),
        # DgsProperty('tqss', 'r', 'DGS field tqss (r)', py_name='tqss'),
    ]

    def __init__(self) -> None:
        self.ID: str = ""
        self.loc_name: str = ""
        self.fold_id: str = ""
        self.sgn: float = 0.1
        self.ugn: float = 0.0
        self.cosn: float = 0.0
        self.xd: float = 0.0
        self.xq: float = 0.0
        self.xdsss: float = 0.0
        self.rstr: float = 0.0
        self.xdsat: float = 0.0
        self.satur: int = 0
        self.Q_min: float = 0.0
        self.Q_max: float = 0.0
        self.q_min: float = 0.0
        self.q_max: float = 0.0
        self.for_name: str = ""
        self.nphase: int = 3
        self.nslty: int = 0
        self.x0sy: float = 0.0
        self.r0sy: float = 0.0
        self.x2sy: float = 0.0
        self.r2sy: float = 0.0
        self.iopt_data: int = 0
        self.xds: float = 0.0
        self.xqs: float = 0.0
        self.xl: float = 0.0
        self.xdss: float = 0.0
        self.xqss: float = 0.0
        self.xrlq: float = 0.0
        self.tds: float = 0.0
        self.tqs: float = 0.0
        self.tdss: float = 0.0
        self.tqss: float = 0.0


class TypTr2(DGSElement):
    element_type = 'TypTr2'
    properties_list = [
        DgsProperty('ID', 'a:40', 'Unique identifier for DGS file', py_name='ID'),
        DgsProperty('loc_name', 'a:40', 'Name', py_name='loc_name'),
        DgsProperty('fold_id', 'p', 'In Folder', py_name='fold_id'),
        DgsProperty('strn', 'r', 'Rated Power in MVA', py_name='strn'),
        DgsProperty('frnom', 'r', 'Nominal Frequency in Hz', py_name='frnom'),
        DgsProperty('utrn_h', 'r', 'Rated Voltage: HV-Side in kV', py_name='utrn_h'),
        DgsProperty('utrn_l', 'r', 'Rated Voltage: LV-Side in kV', py_name='utrn_l'),
        DgsProperty('uktr', 'r', 'Positive Sequence Impedance: Short-Circuit Voltage uk in %', py_name='uktr'),
        DgsProperty('pcutr', 'r', 'Positive Sequence Impedance: Copper Losses in kW', py_name='pcutr'),
        DgsProperty('uk0tr', 'r', 'Zero Sequence Impedance: Short-Circuit Voltage uk0 in %', py_name='uk0tr'),
        DgsProperty('ur0tr', 'r', 'Zero Sequence Impedance: SHC-Voltage (Re(uk0)) uk0r in %', py_name='ur0tr'),
        DgsProperty('tr2cn_h', 'a:2', 'Vector Group: HV-Side:Y :YN:Z :ZN:D', py_name='tr2cn_h'),
        DgsProperty('tr2cn_l', 'a:2', 'Vector Group: LV-Side:Y :YN:Z :ZN:D', py_name='tr2cn_l'),
        DgsProperty('nt2ag', 'r', 'Vector Group: Phase Shift in *30deg', py_name='nt2ag'),
        DgsProperty('curmg', 'r', 'Magnetizing Impedance: No Load Current in %', py_name='curmg'),
        DgsProperty('pfe', 'r', 'Magnetizing Impedance: No Load Losses in kW', py_name='pfe'),
        DgsProperty('zx0hl_n', 'r', 'Zero Sequence Magnetizing Impedance: Mag. Impedance/uk0', py_name='zx0hl_n'),
        DgsProperty('tap_side', 'i', 'Tap Changer 1: at Side:HV:LV', py_name='tap_side'),
        DgsProperty('dutap', 'r', 'Additional Voltage per Tap in %', py_name='dutap'),
        DgsProperty('phitr', 'r', 'Phase of du in deg', py_name='phitr'),
        DgsProperty('nntap0', 'i', 'Neutral Position', py_name='nntap0'),
        DgsProperty('ntpmn', 'i', 'Minimum Position', py_name='ntpmn'),
        DgsProperty('ntpmx', 'i', 'Maximum Position', py_name='ntpmx'),
        DgsProperty('manuf', 'a:20', 'Manufacturer', py_name='manuf'),
        DgsProperty('chr_name', 'a:20', 'Characteristic Name', py_name='chr_name'),
        DgsProperty('for_name', 'a:50', 'DGS field for_name (a:50)', py_name='for_name'),
        DgsProperty('nt2ph', 'i', 'DGS field nt2ph (i)', py_name='nt2ph'),
        DgsProperty('itapch', 'i', 'DGS field itapch (i)', py_name='itapch'),
    ]

    def __init__(self) -> None:
        self.ID: str = ""
        self.loc_name: str = ""
        self.fold_id: str = ""
        self.strn: float = 0.0
        self.frnom: float = 0.0
        self.utrn_h: float = 0.0
        self.utrn_l: float = 0.0
        self.uktr: float = 0.0
        self.pcutr: float = 0.0
        self.uk0tr: float = 0.0
        self.ur0tr: float = 0.0
        self.tr2cn_h: str = "D"  # Y,YN,Z,ZN,D.
        self.tr2cn_l: str = "Y"
        self.nt2ag: float = 0.0
        self.curmg: float = 0.0
        self.pfe: float = 0.0
        self.zx0hl_n: float = 0.0
        self.tap_side: int = 0
        self.dutap: float = 0.0
        self.phitr: float = 0.0
        self.nntap0: int = 0
        self.ntpmn: int = 0
        self.ntpmx: int = 0
        self.manuf: str = ""
        self.chr_name: str = ""
        self.for_name: str = ""
        self.nt2ph: int = 3  # 3-phase
        self.itapch: int = 0


class TypTr3(DGSElement):
    element_type = 'TypTr3'
    properties_list = [
        DgsProperty('ID', 'a:40', 'DGS field ID (a:40)', py_name='ID'),
        DgsProperty('loc_name', 'a', 'DGS field loc_name (a)', py_name='loc_name'),
        DgsProperty('fold_id', 'p', 'DGS field fold_id (p)', py_name='fold_id'),
        DgsProperty('curm3', 'r', 'DGS field curm3 (r)', py_name='curm3'),
        DgsProperty('du3tp_h', 'r', 'DGS field du3tp_h (r)', py_name='du3tp_h'),
        DgsProperty('du3tp_l', 'r', 'DGS field du3tp_l (r)', py_name='du3tp_l'),
        DgsProperty('du3tp_m', 'r', 'DGS field du3tp_m (r)', py_name='du3tp_m'),
        DgsProperty('n3tmn_h', 'i', 'DGS field n3tmn_h (i)', py_name='n3tmn_h'),
        DgsProperty('n3tmn_l', 'i', 'DGS field n3tmn_l (i)', py_name='n3tmn_l'),
        DgsProperty('n3tmn_m', 'i', 'DGS field n3tmn_m (i)', py_name='n3tmn_m'),
        DgsProperty('n3tmx_h', 'i', 'DGS field n3tmx_h (i)', py_name='n3tmx_h'),
        DgsProperty('n3tmx_l', 'i', 'DGS field n3tmx_l (i)', py_name='n3tmx_l'),
        DgsProperty('n3tmx_m', 'i', 'DGS field n3tmx_m (i)', py_name='n3tmx_m'),
        DgsProperty('n3tp0_h', 'i', 'DGS field n3tp0_h (i)', py_name='n3tp0_h'),
        DgsProperty('n3tp0_l', 'i', 'DGS field n3tp0_l (i)', py_name='n3tp0_l'),
        DgsProperty('n3tp0_m', 'i', 'DGS field n3tp0_m (i)', py_name='n3tp0_m'),
        DgsProperty('nt3ag_h', 'r', 'DGS field nt3ag_h (r)', py_name='nt3ag_h'),
        DgsProperty('nt3ag_l', 'r', 'DGS field nt3ag_l (r)', py_name='nt3ag_l'),
        DgsProperty('nt3ag_m', 'r', 'DGS field nt3ag_m (r)', py_name='nt3ag_m'),
        DgsProperty('pcut3_h', 'r', 'DGS field pcut3_h (r)', py_name='pcut3_h'),
        DgsProperty('pcut3_l', 'r', 'DGS field pcut3_l (r)', py_name='pcut3_l'),
        DgsProperty('pcut3_m', 'r', 'DGS field pcut3_m (r)', py_name='pcut3_m'),
        DgsProperty('pfe', 'r', 'DGS field pfe (r)', py_name='pfe'),
        DgsProperty('ph3tr_h', 'r', 'DGS field ph3tr_h (r)', py_name='ph3tr_h'),
        DgsProperty('ph3tr_l', 'r', 'DGS field ph3tr_l (r)', py_name='ph3tr_l'),
        DgsProperty('ph3tr_m', 'r', 'DGS field ph3tr_m (r)', py_name='ph3tr_m'),
        DgsProperty('strn3_h', 'r', 'DGS field strn3_h (r)', py_name='strn3_h'),
        DgsProperty('strn3_l', 'r', 'DGS field strn3_l (r)', py_name='strn3_l'),
        DgsProperty('strn3_m', 'r', 'DGS field strn3_m (r)', py_name='strn3_m'),
        DgsProperty('tr3cn_h', 'a', 'DGS field tr3cn_h (a)', py_name='tr3cn_h'),
        DgsProperty('tr3cn_l', 'a', 'DGS field tr3cn_l (a)', py_name='tr3cn_l'),
        DgsProperty('tr3cn_m', 'a', 'DGS field tr3cn_m (a)', py_name='tr3cn_m'),
        DgsProperty('uk0hl', 'r', 'DGS field uk0hl (r)', py_name='uk0hl'),
        DgsProperty('uk0hm', 'r', 'DGS field uk0hm (r)', py_name='uk0hm'),
        DgsProperty('uk0ml', 'r', 'DGS field uk0ml (r)', py_name='uk0ml'),
        DgsProperty('uktr3_h', 'r', 'DGS field uktr3_h (r)', py_name='uktr3_h'),
        DgsProperty('uktr3_l', 'r', 'DGS field uktr3_l (r)', py_name='uktr3_l'),
        DgsProperty('uktr3_m', 'r', 'DGS field uktr3_m (r)', py_name='uktr3_m'),
        DgsProperty('ur0hl', 'r', 'DGS field ur0hl (r)', py_name='ur0hl'),
        DgsProperty('ur0hm', 'r', 'DGS field ur0hm (r)', py_name='ur0hm'),
        DgsProperty('ur0ml', 'r', 'DGS field ur0ml (r)', py_name='ur0ml'),
        DgsProperty('utrn3_h', 'r', 'DGS field utrn3_h (r)', py_name='utrn3_h'),
        DgsProperty('utrn3_l', 'r', 'DGS field utrn3_l (r)', py_name='utrn3_l'),
        DgsProperty('utrn3_m', 'r', 'DGS field utrn3_m (r)', py_name='utrn3_m'),
        DgsProperty('for_name', 'a:50', 'DGS field for_name (a:50)', py_name='for_name'),
        DgsProperty('itapos', 'i', 'DGS field itapos (i)', py_name='itapos'),
        DgsProperty('i3loc', 'i', 'DGS field i3loc (i)', py_name='i3loc'),
    ]

    def __init__(self) -> None:
        self.ID: str = ""
        self.loc_name: str = ""
        self.fold_id: str = ""
        self.curm3: float = 0.0
        self.du3tp_h: float = 0.0
        self.du3tp_l: float = 0.0
        self.du3tp_m: float = 0.0
        self.n3tmn_h: int = 0
        self.n3tmn_l: int = 0
        self.n3tmn_m: int = 0
        self.n3tmx_h: int = 0
        self.n3tmx_l: int = 0
        self.n3tmx_m: int = 0
        self.n3tp0_h: int = 0
        self.n3tp0_l: int = 0
        self.n3tp0_m: int = 0
        self.nt3ag_h: float = 0.0
        self.nt3ag_l: float = 0.0
        self.nt3ag_m: float = 0.0
        self.pcut3_h: float = 0.0
        self.pcut3_l: float = 0.0
        self.pcut3_m: float = 0.0
        self.pfe: float = 0.0
        self.ph3tr_h: float = 0.0
        self.ph3tr_l: float = 0.0
        self.ph3tr_m: float = 0.0
        self.strn3_h: float = 0.0
        self.strn3_l: float = 0.0
        self.strn3_m: float = 0.0
        self.tr3cn_h: str = ""
        self.tr3cn_l: str = ""
        self.tr3cn_m: str = ""
        self.uk0hl: float = 0.0
        self.uk0hm: float = 0.0
        self.uk0ml: float = 0.0
        self.uktr3_h: float = 0.0
        self.uktr3_l: float = 0.0
        self.uktr3_m: float = 0.0
        self.ur0hl: float = 0.0
        self.ur0hm: float = 0.0
        self.ur0ml: float = 0.0
        self.utrn3_h: float = 0.0
        self.utrn3_l: float = 0.0
        self.utrn3_m: float = 0.0
        self.for_name: str = ""
        self.itapos: int = 0
        self.i3loc: int = 0
