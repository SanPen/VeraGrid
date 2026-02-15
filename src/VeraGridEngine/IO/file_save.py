# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
import os
from datetime import datetime
from typing import Union, List, Any, Dict, TYPE_CHECKING

from VeraGridEngine.IO.file_open import determine_file_type
from VeraGridEngine.IO.cim.cgmes.cgmes_create_instances import create_cgmes_headers
from VeraGridEngine.IO.cim.cgmes.veragrid_to_cgmes import veragrid_to_cgmes
from VeraGridEngine.IO.cim.cgmes.cgmes_export import CimExporter
from VeraGridEngine.IO.cim.cgmes.cgmes_data_parser import CgmesDataParser
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.data_logger import DataLogger
from VeraGridEngine.IO.veragrid.json_parser import save_json_file_v3
from VeraGridEngine.IO.veragrid.excel_interface import (save_excel_v4)
from VeraGridEngine.IO.veragrid.pack_unpack import (gather_model_as_data_frames, gather_model_as_jsons)
from VeraGridEngine.IO.dgs.veragrid_to_dgs import circuit_to_dgs
from VeraGridEngine.IO.raw.raw_parser_writer import write_raw
from VeraGridEngine.IO.raw.veragrid_to_raw import veragrid_to_raw
from VeraGridEngine.IO.cim.cim16.cim_parser import CIMExport
from VeraGridEngine.IO.cim.cgmes.cgmes_circuit import CgmesCircuit
from VeraGridEngine.IO.veragrid.zip_interface import save_veragrid_data_to_zip
from VeraGridEngine.IO.veragrid.sqlite_interface import save_data_frames_to_sqlite
from VeraGridEngine.IO.veragrid.h5_interface import save_h5
from VeraGridEngine.IO.raw.rawx_parser_writer import write_rawx
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import CgmesProfileType
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Simulations.driver_template import DriverToSave
from VeraGridEngine.Simulations.PowerFlow.power_flow_results import PowerFlowResults
from VeraGridEngine.enumerations import CGMESVersions, SimulationTypes, FileType
from VeraGridEngine.Compilers.circuit_to_data import compile_numerical_circuit_at

if TYPE_CHECKING:
    from VeraGridEngine.Simulations.types import DRIVER_OBJECTS


class FileSavingOptions:
    """
    This class is to store the extra stuff that needs to be passed to save more complex files
    """

    def __init__(self,
                 cgmes_boundary_set: str = "",
                 simulation_drivers: List[DRIVER_OBJECTS] = None,
                 sessions_data: List[DriverToSave] = None,
                 dictionary_of_json_files: Dict[str, Dict[str, Any]] = None,
                 cgmes_version: CGMESVersions = CGMESVersions.v2_4_15,
                 cgmes_profiles: Union[None, List[CgmesProfileType]] = None,
                 cgmes_one_file_per_profile: bool = False,
                 cgmes_map_areas_like_raw: bool = False,
                 raw_version: str = "33",
                 file_type: FileType | None = None):
        """
        Constructor
        :param cgmes_boundary_set: CGMES boundary set zip file path
        :param simulation_drivers: List of Simulation Drivers
        :param sessions_data: List of sessions_data
        :param dictionary_of_json_files: Dictionary of json files
        :param cgmes_version: Version to use with CGMES
        :param cgmes_profiles: CGMES profile list to export
        :param cgmes_one_file_per_profile: use one file per profile?
        :param cgmes_map_areas_like_raw: use map areas like raw?
        :param raw_version: Version to use when exporting raw/rawx files
        """

        self.cgmes_version: CGMESVersions = cgmes_version

        self.cgmes_boundary_set: str = cgmes_boundary_set

        self.sessions_data: List[DriverToSave] = list() if sessions_data is None else sessions_data

        self.dictionary_of_json_files = dict() if dictionary_of_json_files is None else dictionary_of_json_files

        # File type description as it appears in the file saving dialogue i.e. VeraGrid zip (*.veragrid)
        self.type_selected: str = ""

        # CGMES profile list
        self.cgmes_profiles = [CgmesProfileType.EQ,
                               CgmesProfileType.OP,
                               CgmesProfileType.SC,
                               CgmesProfileType.TP,
                               CgmesProfileType.SV,
                               CgmesProfileType.SSH,
                               CgmesProfileType.DY,
                               CgmesProfileType.DL,
                               CgmesProfileType.GL] if cgmes_profiles is None else cgmes_profiles

        # use one file per profile?
        self.cgmes_one_file_per_profile = cgmes_one_file_per_profile

        self.cgmes_map_areas_like_raw = cgmes_map_areas_like_raw

        self.raw_version = raw_version

        self.file_type: FileType | None = file_type

    def get_power_flow_results(self) -> Union[None, PowerFlowResults]:
        """
        Try to extract the power flow results
        :return: None or PowerFlowResults
        """
        for data in self.sessions_data:
            if data.tpe == SimulationTypes.PowerFlow_run and isinstance(data.results, PowerFlowResults):
                return data.results

        return None


def save_veragrid_excel(circuit: MultiCircuit, file_name: str) -> Logger:
    """
    Save the circuit information in excel format
    :param circuit: MultiCircuit
    :param file_name: file name to save to
    :return: logger with information
    """

    logger = save_excel_v4(circuit, file_name)

    return logger


def save_veragrid(circuit: MultiCircuit,
                  file_name: str,
                  options: FileSavingOptions,
                  text_func=None,
                  progress_func=None) -> Logger:
    """
    Save the circuit information in zip format
    :return: logger with information
    """

    logger = Logger()

    dfs = gather_model_as_data_frames(circuit,
                                      logger=logger,
                                      legacy=False)

    model_data = gather_model_as_jsons(circuit)

    save_veragrid_data_to_zip(dfs=dfs,
                              filename_zip=file_name,
                              model_data=model_data,
                              sessions_data=options.sessions_data,
                              diagrams=circuit.diagrams,
                              json_files=options.dictionary_of_json_files,
                              text_func=text_func,
                              progress_func=progress_func,
                              logger=logger)

    return logger


def save_veragrid_sqlite(circuit: MultiCircuit,
                         file_name: str,
                         text_func=None,
                         progress_func=None) -> Logger:
    """
    Save the circuit information in sqlite
    :return: logger with information
    """

    logger = Logger()

    dfs = gather_model_as_data_frames(circuit, logger=logger, legacy=True)

    save_data_frames_to_sqlite(dfs,
                               file_path=file_name,
                               text_func=text_func,
                               progress_func=progress_func)

    return logger


def save_electrical_json_v3(circuit: MultiCircuit,
                            file_name: str,
                            options: FileSavingOptions) -> Logger:
    """
    Save the circuit information in json format
    :return:logger with information
    """

    logger = save_json_file_v3(file_name,
                               circuit,
                               options.sessions_data)
    return logger


def save_cim(circuit: MultiCircuit, file_name: str, ) -> Logger:
    """
    Save the circuit information in CIM format
    :return: logger with information
    """

    cim = CIMExport(circuit)
    cim.save(file_name=file_name)

    return cim.logger


def save_cgmes(circuit: MultiCircuit,
               file_name: str,
               options: FileSavingOptions,
               text_func=None,
               progress_func=None) -> Logger:
    """
    Save the circuit information in CGMES format
    :return: logger with information
    """
    logger = Logger()
    if options.cgmes_boundary_set == "":
        logger.add_error(msg="Missing Boundary set path.")
        return logger
    # CGMES version should be given in the settings
    cgmes_circuit = CgmesCircuit(cgmes_version=options.cgmes_version,
                                 text_func=text_func,
                                 progress_func=progress_func,
                                 logger=logger)

    data_parser = CgmesDataParser(text_func=text_func,
                                  progress_func=progress_func,
                                  logger=logger)

    data_parser.load_files(files=[options.cgmes_boundary_set])

    cgmes_circuit.parse_files(data_parser=data_parser)

    profiles_to_export = options.cgmes_profiles
    one_file_per_profile = options.cgmes_one_file_per_profile
    nc = compile_numerical_circuit_at(circuit)
    pf_results = options.get_power_flow_results()
    cgmes_logger = DataLogger()
    cgmes_circuit = veragrid_to_cgmes(gc_model=circuit,
                                      num_circ=nc,
                                      cgmes_model=cgmes_circuit,
                                      pf_results=pf_results,
                                      logger=cgmes_logger)

    fn, _ = os.path.splitext(os.path.basename(file_name))
    filename_in_parts = fn.split('_')

    model_version = "001"
    scenario_time = "2024-01-01T19:30:00Z"
    if filename_in_parts.__len__() == 5:
        try:
            dt = datetime.strptime(filename_in_parts[0], "%Y%m%dT%H%MZ")
            scenario_time = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            logger.add_error(msg="Invalid datetime format in the filename!",
                             value=filename_in_parts[0],
                             comment="Scenario time set to default value."
                             )
        model_version = filename_in_parts[4]

    cgmes_circuit = create_cgmes_headers(cgmes_model=cgmes_circuit,
                                         mas_names=circuit.get_modelling_authority_names().astype(str),
                                         profiles_to_export=profiles_to_export,
                                         version=model_version,
                                         desc="Test description.",
                                         scenario_time=scenario_time,
                                         logger=cgmes_logger)

    cim_exporter = CimExporter(cgmes_circuit=cgmes_circuit,
                               profiles_to_export=profiles_to_export,
                               one_file_per_profile=one_file_per_profile)
    cim_exporter.export(file_name)

    # record the cgmes events in the normal logger
    logger += cgmes_logger.get_logger()

    return logger


def save_veragrid_h5(circuit: MultiCircuit,
                     file_name: str,
                     text_func=None,
                     progress_func=None) -> Logger:
    """
    Save the circuit information in CIM format
    :return: logger with information
    """

    logger = save_h5(circuit=circuit,
                     file_path=file_name,
                     text_func=text_func,
                     prog_func=progress_func)

    return logger


def save_psse_raw(circuit: MultiCircuit,
                  file_name: str,
                  options: FileSavingOptions) -> Logger:
    """
    Save the circuit information in json format
    :return:logger with information
    """
    logger = Logger()
    raw_circuit = veragrid_to_raw(circuit, logger=logger)
    logger += write_raw(file_name, raw_circuit, version=int(options.raw_version))
    return logger


def save_psse_rawx(circuit: MultiCircuit, file_name: str) -> Logger:
    """
    Save the circuit information in json format
    :return:logger with information
    """
    logger = Logger()
    raw_circuit = veragrid_to_raw(circuit, logger=logger)
    logger += write_rawx(file_name, raw_circuit)
    return logger


def save_newton(circuit: MultiCircuit,
                file_name: str) -> Logger:
    """
    Save the circuit information in sqlite
    :return: logger with information
    """

    logger = Logger()
    try:
        from VeraGridEngine.Compilers.circuit_to_newton_pa import to_newton_pa, npa

        time_series = circuit.time_profile is not None

        if time_series:
            t_idx = list(range(circuit.get_time_number()))
        else:
            t_idx = None

        newton_grid, _ = to_newton_pa(circuit, use_time_series=time_series, time_indices=t_idx)

        npa.FileHandler().save(newton_grid, file_name)
    except ImportError:
        logger.add_error(msg="Error while trying to import newton package!", )

    return logger


def save_pgm(circuit: MultiCircuit, file_name: str) -> Logger:
    """
    Save to Power Grid Model format
    :return: logger with information
    """
    from VeraGridEngine.Compilers.circuit_to_pgm import save_pgm
    logger = Logger()

    save_pgm(filename=file_name,
             circuit=circuit,
             logger=logger,
             time_series=circuit.has_time_series)

    return logger


def save_dgs(circuit: MultiCircuit, file_name: str) -> Logger:
    """

    :return:
    """
    logger = Logger()
    dgs = circuit_to_dgs(grid=circuit)
    dgs.write_dgs(path=file_name)
    return logger


class FileSave:
    """
    FileSave
    """

    def __init__(self,
                 circuit: MultiCircuit,
                 file_name: str,
                 options: FileSavingOptions | None = None,
                 text_func=None,
                 progress_func=None):
        """
        File saver
        :param circuit: MultiCircuit
        :param file_name: file name to save to
        :param options: FileSavingOptions (optional)
        :param text_func: Pointer to the text function
        :param progress_func: Pointer to the progress function
        """
        self.circuit = circuit

        self.file_name = file_name

        self.options = FileSavingOptions() if options is None else options

        self.text_func = text_func

        self.progress_func = progress_func

        if self.options.file_type is None:
            self.options.file_type = determine_file_type(file_name=self.file_name)

    def save(self) -> Logger:
        """
        Save the file in the corresponding format
        :return: logger with information
        """
        logger = Logger()

        if self.options.file_type == FileType.VeraGrid_xlsx4:
            logger = save_veragrid_excel(
                circuit=self.circuit,
                file_name=self.file_name
            )

        elif self.options.file_type == FileType.VeraGrid:
            logger = save_veragrid(
                circuit=self.circuit,
                file_name=self.file_name,
                options=self.options,
                text_func=self.text_func,
                progress_func=self.progress_func
            )

        elif self.options.file_type == FileType.VeraGrid_sqlite:
            save_veragrid_sqlite(
                circuit=self.circuit,
                file_name=self.file_name,
            )

        elif self.options.file_type == FileType.VeraGrid_ejson3:
            logger = save_electrical_json_v3(
                circuit=self.circuit,
                file_name=self.file_name,
                options=self.options,
            )

        elif self.options.file_type == FileType.CGMES:
            logger = save_cgmes(
                circuit=self.circuit,
                file_name=self.file_name,
                options=self.options,
                text_func=self.text_func,
                progress_func=self.progress_func
            )

        elif self.options.file_type == FileType.CIM:
            logger = save_cim(
                circuit=self.circuit,
                file_name=self.file_name,
            )

        elif self.options.file_type == FileType.VeraGrid_h5:
            logger = save_veragrid_h5(
                circuit=self.circuit,
                file_name=self.file_name,
            )

        elif self.options.file_type == FileType.PSSE_rawx:
            logger = save_psse_rawx(
                circuit=self.circuit,
                file_name=self.file_name
            )

        elif self.options.file_type == FileType.PSSE_raw:

            logger = save_psse_raw(
                circuit=self.circuit,
                file_name=self.file_name,
                options=self.options,
            )

        elif self.options.file_type == FileType.PGM:
            logger = save_pgm(
                circuit=self.circuit,
                file_name=self.file_name,
            )

        elif self.options.file_type == FileType.DGS:
            logger = save_dgs(
                circuit=self.circuit,
                file_name=self.file_name,
            )

        else:
            logger = Logger()
            logger.add_error('File path extension not understood', self.file_name)

        return logger
