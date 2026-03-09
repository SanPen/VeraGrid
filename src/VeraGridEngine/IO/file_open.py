# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
import os
import json

from collections.abc import Callable
from typing import Union, List, Tuple

from VeraGridEngine.IO.cim.cgmes.cgmes_data_parser import CgmesDataParser
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import CgmesRecoveryMode
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.data_logger import DataLogger
from VeraGridEngine.IO.veragrid.excel_interface import (load_from_xls, interpret_excel_v3, interprete_excel_v2)
from VeraGridEngine.IO.veragrid.pack_unpack import (parse_veragrid_data)
from VeraGridEngine.IO.matpower.legacy.matpower_parser import interpret_data_v1
from VeraGridEngine.IO.matpower.matpower_circuit import MatpowerCircuit
from VeraGridEngine.IO.matpower.matpower_to_veragrid import matpower_to_veragrid
from VeraGridEngine.IO.dgs.dgs_to_veragrid import dgs_to_circuit
from VeraGridEngine.IO.others.dpx_parser import load_dpx
from VeraGridEngine.IO.others.ipa_parser import load_iPA
from VeraGridEngine.IO.veragrid.json_parser import parse_json, parse_json_data_v3
from VeraGridEngine.IO.raw.raw_parser_writer import read_raw
from VeraGridEngine.IO.raw.raw_to_veragrid import psse_to_veragrid
from VeraGridEngine.IO.epc.epc_parser import PowerWorldParser
from VeraGridEngine.IO.cim.cim16.cim_parser import CIMImport
from VeraGridEngine.IO.cim.cgmes.cgmes_circuit import CgmesCircuit
from VeraGridEngine.IO.cim.cgmes.cgmes_to_veragrid import cgmes_to_veragrid
from VeraGridEngine.IO.veragrid.zip_interface import get_frames_from_zip
from VeraGridEngine.IO.veragrid.sqlite_interface import open_data_frames_from_sqlite
from VeraGridEngine.IO.veragrid.h5_interface import open_h5
from VeraGridEngine.IO.raw.rawx_parser_writer import parse_rawx
from VeraGridEngine.IO.others.pypsa_parser import parse_pypsa_netcdf, parse_pypsa_hdf5
from VeraGridEngine.IO.others.pandapower_parser import Panda2VeraGrid
from VeraGridEngine.IO.ucte.devices.ucte_circuit import UcteCircuit
from VeraGridEngine.IO.ucte.ucte_to_veragrid import convert_ucte_to_veragrid
from VeraGridEngine.IO.others.rte_parser import rte2veragrid
from VeraGridEngine.IO.others.anarede import PWFParser
from VeraGridEngine.IO.iidm.iidm_parser_pypowsybl import IidmParser
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.enumerations import CGMESVersions, CgmesTopologyMode, FileType


class FileOpenOptions:
    """
    This class is to store the extra stuff that needs to be passed to open more complex files
    """

    def __init__(self,
                 # General
                 file_type: FileType | None = None,
                 crash_on_errors: bool = True,
                 # CGMEs
                 cgmes_version: CGMESVersions | None = None,
                 cgmes_map_areas_like_raw: bool = False,
                 cgmes_try_to_map_dc_to_hvdc_line: bool = True,
                 cgmes_topology_mode: CgmesTopologyMode = CgmesTopologyMode.Auto,
                 cgmes_create_busbar_section_for_every_connectivity_node: bool = False,
                 # PSSe
                 psse_adjust_taps_to_discrete_positions: bool = False,
                 psse_use_short_names: bool = True,
                 psse_flatten_virtual_taps: bool = False,
                 cgmes_recovery_mode: CgmesRecoveryMode = CgmesRecoveryMode.Auto):
        """
        :param file_type: FileType to load, none is unsure
        :param crash_on_errors: Mainly debug feature to allow finding the exact crash issue when loading files
        :param cgmes_version: CGMES version to load
        :param cgmes_map_areas_like_raw: If active the CGMEs mapping will be:
                                            GeographicalRegion <-> Area
                                            SubGeographicalRegion <-> Zone
                                        Otherwise:
                                            GeographicalRegion <-> Country
                                            SubGeographicalRegion <-> Community
        :param cgmes_try_to_map_dc_to_hvdc_line: Converters and DC lines in CGMES are attempted to be converted
                                            to the simplified HvdcLine objects in VeraGrid
        :param cgmes_topology_mode: CGMES topology conversion mode.
                                    Auto: decide from model content.
                                    ConnectivityNode: import node-breaker view.
                                    TopologicalNode: import bus-branch view.
        :param cgmes_create_busbar_section_for_every_connectivity_node: If true, create a BusBar for each
                                                                         ConnectivityNode similarly to powsybl.
        :param psse_adjust_taps_to_discrete_positions: Modify the tap angle and module to the discrete positions
        """

        # General
        self.file_type: FileType | None = file_type
        self.crash_on_errors = crash_on_errors

        # CGMES options
        self.cgmes_version: CGMESVersions | None = cgmes_version
        self.cgmes_map_areas_like_raw = cgmes_map_areas_like_raw
        self.cgmes_try_to_map_dc_to_hvdc_line = cgmes_try_to_map_dc_to_hvdc_line
        self.cgmes_topology_mode: CgmesTopologyMode = cgmes_topology_mode
        self.cgmes_create_busbar_section_for_every_connectivity_node = (
            cgmes_create_busbar_section_for_every_connectivity_node
        )
        self.cgmes_recovery_mode: CgmesRecoveryMode = cgmes_recovery_mode

        # PSS/e options
        self.psse_adjust_taps_to_discrete_positions = psse_adjust_taps_to_discrete_positions
        self.psse_use_short_names = psse_use_short_names
        self.psse_flatten_virtual_taps = psse_flatten_virtual_taps




def open_cgmes(files: List[str] | str,
               version: CGMESVersions | None = None,
               cgmes_map_areas_like_raw: bool = False,
               try_to_map_dc_to_hvdc_line: bool = False,
               cgmes_topology_mode: CgmesTopologyMode = CgmesTopologyMode.Auto,
               cgmes_create_busbar_section_for_every_connectivity_node: bool = False,
               text_func: Union[None, Callable] = None,
               progress_func: Union[None, Callable] = None,
               cgmes_logger: DataLogger = DataLogger(),
               cgmes_recovery_mode: CgmesRecoveryMode = CgmesRecoveryMode.Auto) -> Tuple[MultiCircuit, CgmesCircuit]:
    """
    Load cgmes files
    :param files: file or list of files
    :param version:
    :param cgmes_map_areas_like_raw:
    :param try_to_map_dc_to_hvdc_line:
    :param cgmes_topology_mode:
    :param cgmes_create_busbar_section_for_every_connectivity_node:
    :param text_func:
    :param progress_func:
    :param cgmes_logger:
    :param cgmes_recovery_mode:
    :return:
    """

    data_parser = CgmesDataParser(
        text_func=text_func,
        progress_func=progress_func,
        logger=cgmes_logger
    )

    if isinstance(files, str):
        data_parser.load_files(files=[files])
    elif isinstance(files, list):
        data_parser.load_files(files=files)
    else:
        raise ValueError("Onli file names or list of files are supported")

    cgmes_version = data_parser.cgmes_version if version is None else version
    if cgmes_version is None:
        cgmes_version = CGMESVersions.v3_0_0

    cgmes_circuit = CgmesCircuit(
        cgmes_version=cgmes_version,
        text_func=text_func,
        cgmes_map_areas_like_raw=cgmes_map_areas_like_raw,
        cgmes_recovery_mode=cgmes_recovery_mode,
        progress_func=progress_func,
        logger=cgmes_logger
    )
    cgmes_circuit.parse_files(data_parser=data_parser)
    circuit = cgmes_to_veragrid(
        cgmes_model=cgmes_circuit,
        map_dc_to_hvdc_line=try_to_map_dc_to_hvdc_line,
        cgmes_topology_mode=cgmes_topology_mode,
        create_busbar_section_for_every_connectivity_node=(
            cgmes_create_busbar_section_for_every_connectivity_node
        ),
        logger=cgmes_logger
    )

    return circuit, cgmes_circuit


def open_ucte(files: List[str] | str,
              text_func: Union[None, Callable] = None,
              progress_func: Union[None, Callable] = None,
              logger: Logger = Logger()) -> MultiCircuit:
    """

    :param files: files or list of files
    :param text_func:
    :param progress_func:
    :param logger:
    :return:
    """
    ucte_grid = UcteCircuit()

    if isinstance(files, str):
        ucte_grid.parse_file(files=[files], logger=logger)
    elif isinstance(files, list):
        ucte_grid.parse_file(files=files, logger=logger)
    else:
        raise ValueError("Only file names or list of files are supported")

    circuit = convert_ucte_to_veragrid(ucte_grid=ucte_grid, logger=logger)
    return circuit


def determine_file_type(file_name: List[str] | str) -> FileType | None:
    """
    Try to determine the type of file
    The result is stored in self.file_type
    :param file_name: file path(s) with the extension
    """
    if isinstance(file_name, list):

        looks_like_ucte = False
        for f in file_name:
            _, file_extension = os.path.splitext(f)
            if file_extension.lower() in ['.xml', '.zip']:
                looks_like_ucte = False

            elif file_extension.lower() in ['.ucte']:
                looks_like_ucte = True

            else:
                looks_like_ucte = False

        if looks_like_ucte:

            return FileType.UCTE

        else:
            return None  # needs further clarification

    else:

        name, file_extension = os.path.splitext(file_name)
        # print(name, file_extension)
        if file_extension.lower() in ['.xls', '.xlsx']:

            return FileType.generic_excel

        elif file_extension.lower() in ['.gridcal', '.veragrid']:

            # open file content
            return FileType.VeraGrid

        elif file_extension.lower() in ['.dgridcal', '.dveragrid']:

            # open file content
            return FileType.VeraGrid_delta

        elif file_extension.lower() == '.sqlite':

            # open file content
            return FileType.VeraGrid_sqlite

        elif file_extension.lower() == '.dgs':
            return FileType.DGS

        elif file_extension.lower() == '.gch5':
            return FileType.VeraGrid_h5

        elif file_extension.lower() in ['.m', '.matpower']:
            return FileType.Matpower

        elif file_extension.lower() == '.dpx':
            return FileType.DPX

        elif file_extension.lower() == '.pwf':
            return FileType.PWF

        elif file_extension.lower() == '.json':
            return FileType.VeraGrid_json

        elif file_extension.lower() == '.ejson3':
            return FileType.VeraGrid_ejson3

        elif file_extension.lower() == '.raw':
            return FileType.PSSE_raw

        elif file_extension.lower() == '.rawx':
            return FileType.PSSE_rawx

        elif file_extension.lower() == '.epc':
            return FileType.EPC

        elif file_extension.lower() in ['.xml', '.zip']:
            # inconclusive
            return None

        elif file_extension.lower() == '.hdf5':
            return FileType.PyPsa_h5

        elif file_extension.lower() == '.nc':
            return FileType.PyPsa

        elif file_extension.lower() == '.p':
            return FileType.PandaPower

        elif file_extension.lower() == '.uct' or file_extension.lower() == '.ucte':
            return FileType.UCTE

        elif file_extension.lower() == '.iidm' or file_extension.lower() == '.xiidm':
            return FileType.Iidm
        else:
            return None


class FileOpen:
    """
    File open interface
    """

    def __init__(self,
                 file_name: Union[str, List[str]],
                 previous_circuit: Union[MultiCircuit, None] = None,
                 options: FileOpenOptions | None = None):
        """
        File open handler
        :param file_name: name of the file
        :param previous_circuit: previous circuit, to generate diffs
        :param options: FileOpenOptions
        """
        self.file_name: Union[str, List[str]] = file_name

        self.circuit: Union[MultiCircuit, None] = None

        self.options: FileOpenOptions = options if options is not None else FileOpenOptions()

        self.cgmes_circuit: Union[CgmesCircuit, None] = None

        self.json_files = dict()

        self.logger = Logger()

        self.cgmes_logger = DataLogger()

        self._previous_circuit = previous_circuit

        # Determine if the file exists
        if isinstance(self.file_name, str):
            if not os.path.exists(self.file_name):
                raise Exception("File not found :( \n{}".format(self.file_name))
        elif isinstance(self.file_name, list):
            for fname in self.file_name:
                if not os.path.exists(fname):
                    raise Exception("File not found :( \n{}".format(fname))
        else:
            raise Exception("file_name type not supported :( \n{}".format(self.file_name))

        # determine the file type
        self.file_type: FileType | None = self.options.file_type

        if self.file_type is None:
            # Try to determine the type
            self.file_type = determine_file_type(file_name=self.file_name)

    def open(self,
             text_func: Union[None, Callable] = None,
             progress_func: Union[None, Callable] = None) -> Union[MultiCircuit, None]:
        """
        Load VeraGrid compatible file
        :param text_func: pointer to function that prints the names
        :param progress_func: pointer to function that prints the progress 0~100
        :return: MultiCircuit
        """
        self.logger = Logger()

        # --- VeraGrid Core & Excel Variants ---
        if self.file_type == FileType.VeraGrid:
            # open file content
            data_dictionary, self.json_files = get_frames_from_zip(self.file_name,
                                                                   text_func=text_func,
                                                                   progress_func=progress_func,
                                                                   logger=self.logger)
            # interpret file content
            if data_dictionary is not None:
                self.circuit = parse_veragrid_data(data=data_dictionary,
                                                   text_func=text_func,
                                                   progress_func=progress_func,
                                                   logger=self.logger)
            else:
                self.logger.add("Error while reading the file :(")
                return None

        # --- VeraGrid Data Serialization ---
        elif self.file_type == FileType.VeraGrid_delta:
            # open file content
            data_dictionary, self.json_files = get_frames_from_zip(self.file_name,
                                                                   text_func=text_func,
                                                                   progress_func=progress_func,
                                                                   logger=self.logger)
            # interpret file content
            if data_dictionary is not None:
                self.circuit = parse_veragrid_data(data=data_dictionary,
                                                   previous_circuit=self._previous_circuit,
                                                   text_func=text_func,
                                                   progress_func=progress_func,
                                                   logger=self.logger)
            else:
                self.logger.add("Error while reading the file :(")
                return None
        elif self.file_type == FileType.VeraGrid_ejson3:
            with open(self.file_name, encoding="utf-8") as f:
                data = json.load(f)
                self.circuit = parse_json_data_v3(data, self.logger)

        elif self.file_type == FileType.VeraGrid_xlsx1:
            data_dictionary = load_from_xls(self.file_name, self.logger)
            self.circuit = interpret_data_v1(data_dictionary, self.logger)

        elif self.file_type == FileType.VeraGrid_xlsx2:
            data_dictionary = load_from_xls(self.file_name, self.logger)
            self.circuit = interprete_excel_v2(data_dictionary, logger=self.logger)

        elif self.file_type == FileType.VeraGrid_xlsx3:
            data_dictionary = load_from_xls(self.file_name, self.logger)
            self.circuit = interpret_excel_v3(data_dictionary, logger=self.logger)

        elif self.file_type == FileType.VeraGrid_xlsx4:
            data_dictionary = load_from_xls(self.file_name, self.logger)
            if data_dictionary is not None:
                self.circuit = parse_veragrid_data(data=data_dictionary,
                                                   text_func=text_func,
                                                   progress_func=progress_func,
                                                   logger=self.logger)
            else:
                self.logger.add("Error while reading the file :(")
                return None

        elif self.file_type == FileType.generic_excel:
            data_dictionary = load_from_xls(self.file_name, self.logger)

            # Pass the table-like data dictionary to objects in this circuit
            if 'version' not in data_dictionary:
                self.circuit = interpret_data_v1(data_dictionary, self.logger)

            elif data_dictionary['version'] == 2.0:
                self.circuit = interprete_excel_v2(data_dictionary, logger=self.logger)

            elif data_dictionary['version'] == 3.0:
                self.circuit = interpret_excel_v3(data_dictionary, logger=self.logger)

            elif data_dictionary['version'] == 4.0:
                if data_dictionary is not None:
                    self.circuit = parse_veragrid_data(data=data_dictionary,
                                                       text_func=text_func,
                                                       progress_func=progress_func,
                                                       logger=self.logger)
                else:
                    self.logger.add("Error while reading the file :(")
                    return None
            else:
                self.logger.add('The excel file could not be processed')
                return None

        elif self.file_type == FileType.VeraGrid_sqlite:
            # open file content
            data_dictionary = open_data_frames_from_sqlite(self.file_name,
                                                           text_func=text_func,
                                                           progress_func=progress_func)
            # interpret file content
            if data_dictionary is not None:
                self.circuit = parse_veragrid_data(data_dictionary, logger=self.logger)
            else:
                self.logger.add("Error while reading the file :(")
                return None

        elif self.file_type == FileType.VeraGrid_h5:
            self.circuit = open_h5(self.file_name, text_func=text_func, prog_func=progress_func)

        elif self.file_type == FileType.VeraGrid_json:
            self.circuit = parse_json(self.file_name)

        # --- Common Power Flow Formats ---
        elif self.file_type == FileType.Matpower:
            m_grid = MatpowerCircuit()
            m_grid.read_file(file_name=self.file_name)
            self.circuit = matpower_to_veragrid(m_grid, self.logger)

        elif self.file_type == FileType.DPX:
            self.circuit, log = load_dpx(self.file_name)
            self.logger += log

        elif self.file_type == FileType.PWF:
            parser = PWFParser(self.file_name)
            self.circuit = parser.to_veragrid()
            self.logger += parser.logger

        elif self.file_type == FileType.EPC:
            parser = PowerWorldParser(self.file_name)
            self.circuit = parser.circuit
            self.logger += parser.logger

        # --- Python Modeling Frameworks ---
        elif self.file_type == FileType.PyPsa:
            self.circuit = parse_pypsa_netcdf(self.file_name, self.logger)

        elif self.file_type == FileType.PyPsa_h5:
            self.circuit = parse_pypsa_hdf5(self.file_name, self.logger)

        elif self.file_type == FileType.PandaPower:
            self.circuit = Panda2VeraGrid(self.file_name, self.logger).get_multicircuit()

        # --- Commercial & Industrial Standards ---
        elif self.file_type == FileType.PSSE_raw:
            pss_grid = read_raw(self.file_name,
                                text_func=text_func,
                                progress_func=progress_func,
                                logger=self.logger)
            self.circuit = psse_to_veragrid(
                psse_circuit=pss_grid,
                logger=self.logger,
                adjust_taps_to_discrete_positions=self.options.psse_adjust_taps_to_discrete_positions,
                use_short_names=self.options.psse_use_short_names,
                flatten_virtual_taps=self.options.psse_flatten_virtual_taps
            )

        elif self.file_type == FileType.PSSE_rawx:
            pss_grid = parse_rawx(self.file_name, logger=self.logger)
            self.circuit = psse_to_veragrid(
                psse_circuit=pss_grid,
                logger=self.logger,
                adjust_taps_to_discrete_positions=self.options.psse_adjust_taps_to_discrete_positions,
                use_short_names=self.options.psse_use_short_names,
                flatten_virtual_taps=self.options.psse_flatten_virtual_taps
            )

        elif self.file_type == FileType.DGS:
            self.circuit = dgs_to_circuit(self.file_name, logger=self.logger)

        # --- European Grid Standards & RTE ---
        elif self.file_type == FileType.Iidm:
            parser = IidmParser(self.file_name, self.logger)
            self.circuit = parser.parse()

        elif self.file_type == FileType.CGMES:
            self.circuit, self.cgmes_circuit = open_cgmes(
                files=self.file_name,
                version=self.options.cgmes_version,  # will be determined inside if possible
                cgmes_map_areas_like_raw=self.options.cgmes_map_areas_like_raw,
                try_to_map_dc_to_hvdc_line=self.options.cgmes_try_to_map_dc_to_hvdc_line,
                cgmes_topology_mode=self.options.cgmes_topology_mode,
                cgmes_create_busbar_section_for_every_connectivity_node=(
                    self.options.cgmes_create_busbar_section_for_every_connectivity_node
                ),
                cgmes_recovery_mode=self.options.cgmes_recovery_mode,
                text_func=text_func,
                progress_func=progress_func,
                cgmes_logger=self.cgmes_logger
            )

        elif self.file_type == FileType.UCTE:
            self.circuit = open_ucte(files=self.file_name,
                                     text_func=text_func,
                                     progress_func=progress_func,
                                     logger=self.logger)

        elif self.file_type == FileType.RTE_xml:
            self.circuit, is_valid_rte = rte2veragrid(self.file_name, self.logger)

        elif self.file_type == FileType.CIM:
            parser = CIMImport(text_func=text_func, progress_func=progress_func)
            self.circuit = parser.load_cim_file(self.file_name)
            self.logger += parser.logger

        elif self.file_type == FileType.IPA:
            self.circuit = load_iPA(self.file_name)

        else:
            # This acts as a safety net if a new member is added to the Enum later
            pass

        return self.circuit

    def check_json_type(self, file_name):
        """
        Check the json file type from its internal data
        :param file_name: file path
        :return: data['type'] | 'Not json file' | 'Unknown json file'
        """

        if not os.path.exists(file_name):
            return 'Not json file'

        _, file_extension = os.path.splitext(file_name)

        if file_extension.lower() == '.json':
            with open(self.file_name, encoding="utf-8") as f:
                data = json.load(f)
                return data['type'] if 'type' in data else 'Unknown json file'
        else:
            return 'Not json file'
