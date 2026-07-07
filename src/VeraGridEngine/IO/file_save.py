# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
import os
import re
import tempfile
import zipfile
from datetime import datetime
from typing import Union, List, Any, Dict

from VeraGridEngine.IO.file_open import determine_file_type
from VeraGridEngine.IO.cim.cgmes.cgmes_create_instances import create_cgmes_headers
from VeraGridEngine.IO.cim.cgmes.veragrid_to_cgmes import veragrid_to_cgmes
from VeraGridEngine.IO.cim.cgmes.cgmes_export import CimExporter
from VeraGridEngine.IO.cim.cgmes.cgmes_data_parser import CgmesDataParser
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.data_logger import DataLogger
from VeraGridEngine.IO.veragrid.json_parser import save_json_file_v3
from VeraGridEngine.IO.veragrid.excel_interface import (save_excel_v4)
from VeraGridEngine.IO.veragrid.pack_unpack import gather_model_as_data_frames
from VeraGridEngine.IO.dgs.veragrid_to_dgs import circuit_to_dgs
from VeraGridEngine.IO.matpower.veragrid_to_matpower import write_matpower_case_file
from VeraGridEngine.IO.raw.raw_parser_writer import write_raw
from VeraGridEngine.IO.raw.veragrid_to_raw import veragrid_to_raw
from VeraGridEngine.IO.ucte.veragrid_to_ucte import write_ucte
from VeraGridEngine.IO.cim.cim16.cim_parser import CIMExport
from VeraGridEngine.IO.cim.cgmes.cgmes_circuit import CgmesCircuit
from VeraGridEngine.IO.veragrid.zip_interface import save_veragrid_data_to_zip, save_veragrid_multiverse_data_to_zip
from VeraGridEngine.IO.veragrid.sqlite_interface import save_data_frames_to_sqlite
from VeraGridEngine.IO.veragrid.h5_interface import save_h5
from VeraGridEngine.IO.raw.rawx_parser_writer import write_rawx
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import CgmesProfileType
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Devices.multiverse import MultiVerse
from VeraGridEngine.Simulations.driver_template import DriverToSave
from VeraGridEngine.Simulations.PowerFlow.power_flow_results import PowerFlowResults
from VeraGridEngine.enumerations import (CGMESVersions, SimulationTypes, FileType,
                                         PsseTopologyExportMode, PsseExportMode, DgsExportMode,
                                         MatpowerExportMode, UcteExportMode, CgmesExportMode)
from VeraGridEngine.Compilers.circuit_to_data import compile_numerical_circuit_at


class FileSavingOptions:
    """
    Store the extra data required by the richer file-export paths.
    """

    def __init__(self,
                 file_type: FileType | None = None,
                 sessions_data: List[DriverToSave] = None,
                 dictionary_of_json_files: Dict[str, Dict[str, Any]] = None,
                 cgmes_boundary_set: str = "",
                 cgmes_version: CGMESVersions = CGMESVersions.v2_4_15,
                 cgmes_profiles: Union[None, List[CgmesProfileType]] = None,
                 cgmes_one_file_per_profile: bool = False,
                 cgmes_map_areas_like_raw: bool = False,
                 raw_version: str = "33",
                 psse_topology_mode: PsseTopologyExportMode = PsseTopologyExportMode.BusBranch,
                 psse_export_mode: PsseExportMode = PsseExportMode.SingleFile,
                 dgs_export_mode: DgsExportMode = DgsExportMode.SingleFile,
                 matpower_export_mode: MatpowerExportMode = MatpowerExportMode.SingleFile,
                 ucte_export_mode: UcteExportMode = UcteExportMode.SingleFile,
                 cgmes_export_mode: CgmesExportMode = CgmesExportMode.SingleFile,
                 t_idx: int | None = None):
        """
        Build one file-save options container.

        :param file_type: Explicit file type override.
        :param sessions_data: Session payloads to persist with VeraGrid files.
        :param dictionary_of_json_files: Extra JSON payloads to embed.
        :param cgmes_boundary_set: CGMES boundary set zip file path.
        :param cgmes_version: CGMES export version.
        :param cgmes_profiles: CGMES profile list to export.
        :param cgmes_one_file_per_profile: Export one CGMES file per profile when ``True``.
        :param cgmes_map_areas_like_raw: Reuse RAW-like area mapping for CGMES.
        :param raw_version: Version to use when exporting RAW/RAWX files.
        :param psse_topology_mode: RAW topology export strategy for PSSE 34+.
        :param psse_export_mode: PSSE single-file or batch-zip export strategy.
        :param dgs_export_mode: DGS single-file or batch-zip export strategy.
        :param matpower_export_mode: MATPOWER single-file or batch-zip export strategy.
        :param ucte_export_mode: UCTE single-file or batch-zip export strategy.
        :param cgmes_export_mode: CGMES single-file or batch-zip export strategy.
        :param t_idx: Optional time index used by file formats that support snapshot/profile exports.
        :return: None.
        """

        self.file_type: FileType | None = file_type

        self.sessions_data: List[DriverToSave] = list() if sessions_data is None else sessions_data

        self.dictionary_of_json_files = dict() if dictionary_of_json_files is None else dictionary_of_json_files

        self.cgmes_version: CGMESVersions = cgmes_version

        self.cgmes_boundary_set: str = cgmes_boundary_set

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
        self.psse_topology_mode: PsseTopologyExportMode = psse_topology_mode
        self.psse_export_mode: PsseExportMode = psse_export_mode
        self.dgs_export_mode: DgsExportMode = dgs_export_mode
        self.matpower_export_mode: MatpowerExportMode = matpower_export_mode
        self.ucte_export_mode: UcteExportMode = ucte_export_mode
        self.cgmes_export_mode: CgmesExportMode = cgmes_export_mode
        self.t_idx: int | None = t_idx

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


def save_veragrid_multiverse(file_name: str,
                             multiverse: MultiVerse,
                             options: FileSavingOptions,
                             text_func=None,
                             progress_func=None) -> Logger:
    """
    Save the circuit information in zip format
    If a multiverse is passed in the options, it is "commited" before saving
    :return: logger with information
    """

    logger = Logger()

    if multiverse is not None:
        # this is to make the leaf the actual diff for saving
        multiverse.commit_current()

        active_grid_idtag: str | None = None
        if multiverse.current_node is not None:
            active_grid_idtag = multiverse.current_node.circuit.idtag
        else:
            pass

        save_veragrid_multiverse_data_to_zip(filename_zip=file_name,
                                             multiverse=multiverse,
                                             json_files=options.dictionary_of_json_files,
                                             active_grid_idtag=active_grid_idtag,
                                             active_sessions_data=options.sessions_data,
                                             text_func=text_func,
                                             progress_func=progress_func,
                                             logger=logger)
    else:
        logger.add_error("No multiverse data to save")

    return logger


def save_veragrid_circuit(circuit: MultiCircuit,
                          file_name: str,
                          options: FileSavingOptions,
                          text_func=None,
                          progress_func=None) -> Logger:
    """
    Save the circuit information in zip format
    If a multiverse is passed in the options, it is "commited" before saving
    :return: logger with information
    """

    logger = Logger()

    save_veragrid_data_to_zip(filename_zip=file_name,
                              circuit=circuit,
                              sessions_data=options.sessions_data,
                              json_files=options.dictionary_of_json_files,
                              text_func=text_func,
                              progress_func=progress_func,
                              logger=logger)

    return logger


def save_veragrid_delta(circuit: MultiCircuit,
                        file_name: str,
                        options: FileSavingOptions,
                        text_func=None,
                        progress_func=None) -> Logger:
    """
    Save the circuit information in zip format
    If a multiverse is passed in the options, it is "commited" before saving
    :return: logger with information
    """

    logger = Logger()

    save_veragrid_data_to_zip(filename_zip=file_name,
                              circuit=circuit,
                              sessions_data=options.sessions_data,
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


def save_cgmes_single(circuit: MultiCircuit,
                      file_name: str,
                      options: FileSavingOptions,
                      text_func=None,
                      progress_func=None) -> Logger:
    """
    Save one CGMES export artifact for one snapshot or one time-series point.

    :param circuit: Circuit to export.
    :param file_name: Target file path.
    :param options: Export options.
    :param text_func: Optional progress-text callback.
    :param progress_func: Optional progress-value callback.
    :return: Logger with export messages.
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
    nc = compile_numerical_circuit_at(circuit, t_idx=options.t_idx)
    pf_results = options.get_power_flow_results()
    cgmes_logger = DataLogger()
    cgmes_circuit = veragrid_to_cgmes(gc_model=circuit,
                                      num_circ=nc,
                                      cgmes_model=cgmes_circuit,
                                      pf_results=pf_results,
                                      logger=cgmes_logger,
                                      t_idx=options.t_idx)

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


def compose_cgmes_batch_folder_name(t_idx: int, time_label: str) -> str:
    """
    Compose one deterministic folder name for a CGMES batch-export member set.

    :param t_idx: Time index of the exported profile point.
    :param time_label: Human-readable time label.
    :return: Sanitized folder name.
    """
    safe_time_label: str = re.sub(r"[^0-9A-Za-z._-]+", "_", time_label).strip("_")

    if safe_time_label == "":
        safe_time_label = "time"
    else:
        pass

    return f"t{t_idx:05d}_{safe_time_label}"


def save_cgmes_batch_zip(circuit: MultiCircuit,
                         file_name: str,
                         options: FileSavingOptions,
                         text_func=None,
                         progress_func=None) -> Logger:
    """
    Export every time-series point into one ZIP archive with one CGMES export set per step.

    :param circuit: Circuit to export.
    :param file_name: Target ZIP path.
    :param options: Export options.
    :param text_func: Optional progress-text callback.
    :param progress_func: Optional progress-value callback.
    :return: Logger with export messages.
    """
    logger = Logger()

    if options.cgmes_boundary_set == "":
        logger.add_error(msg="Missing Boundary set path.")
        return logger
    else:
        pass

    if not circuit.has_time_series:
        logger.add_error(msg="CGMES batch export requires time-series data.")
        return logger
    else:
        pass

    total_steps: int = circuit.get_time_number()
    if total_steps <= 0:
        logger.add_error(msg="CGMES batch export requires at least one time-series point.")
        return logger
    else:
        pass

    _, zip_extension = os.path.splitext(file_name)
    if zip_extension.lower() == ".zip":
        zip_file_name: str = file_name
    else:
        zip_file_name = file_name + ".zip"

    with tempfile.TemporaryDirectory() as temp_dir:
        with zipfile.ZipFile(zip_file_name, "w", zipfile.ZIP_DEFLATED) as zip_ptr:
            for t_idx in range(total_steps):
                if text_func is not None:
                    text_func(f"Exporting CGMES profile [{t_idx}] {circuit.time_profile[t_idx]}...")
                else:
                    pass

                if progress_func is not None:
                    progress_value: float = (100.0 * float(t_idx)) / float(total_steps)
                    progress_func(progress_value)
                else:
                    pass

                time_label: str = str(circuit.time_profile[t_idx])
                batch_folder_name: str = compose_cgmes_batch_folder_name(t_idx=t_idx,
                                                                         time_label=time_label)
                export_dir: str = os.path.join(temp_dir, batch_folder_name)
                os.mkdir(export_dir)

                temp_options = FileSavingOptions(
                    file_type=options.file_type,
                    sessions_data=options.sessions_data,
                    dictionary_of_json_files=options.dictionary_of_json_files,
                    cgmes_boundary_set=options.cgmes_boundary_set,
                    cgmes_version=options.cgmes_version,
                    cgmes_profiles=options.cgmes_profiles,
                    cgmes_one_file_per_profile=options.cgmes_one_file_per_profile,
                    cgmes_map_areas_like_raw=options.cgmes_map_areas_like_raw,
                    raw_version=options.raw_version,
                    psse_topology_mode=options.psse_topology_mode,
                    psse_export_mode=options.psse_export_mode,
                    dgs_export_mode=options.dgs_export_mode,
                    cgmes_export_mode=CgmesExportMode.SingleFile,
                    t_idx=t_idx
                )
                temp_options.type_selected = options.type_selected

                temp_file_name: str = os.path.join(export_dir, os.path.basename(zip_file_name))
                logger += save_cgmes_single(circuit=circuit,
                                            file_name=temp_file_name,
                                            options=temp_options,
                                            text_func=text_func,
                                            progress_func=progress_func)

                for generated_name in sorted(os.listdir(export_dir)):
                    generated_path: str = os.path.join(export_dir, generated_name)
                    if os.path.isfile(generated_path):
                        arc_name: str = os.path.join(batch_folder_name, generated_name)
                        zip_ptr.write(generated_path, arcname=arc_name)
                    else:
                        pass

    if progress_func is not None:
        progress_func(100.0)
    else:
        pass

    return logger


def save_cgmes(circuit: MultiCircuit,
               file_name: str,
               options: FileSavingOptions,
               text_func=None,
               progress_func=None) -> Logger:
    """
    Save the circuit information in CGMES format.

    :param circuit: Circuit to export.
    :param file_name: Target file path.
    :param options: Export options.
    :param text_func: Optional progress-text callback.
    :param progress_func: Optional progress-value callback.
    :return: Logger with export messages.
    """
    if options.cgmes_export_mode == CgmesExportMode.BatchZip:
        return save_cgmes_batch_zip(circuit=circuit,
                                    file_name=file_name,
                                    options=options,
                                    text_func=text_func,
                                    progress_func=progress_func)
    else:
        return save_cgmes_single(circuit=circuit,
                                 file_name=file_name,
                                 options=options,
                                 text_func=text_func,
                                 progress_func=progress_func)


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
                  options: FileSavingOptions,
                  text_func=None,
                  progress_func=None) -> Logger:
    """
    Save the circuit information in PSSE RAW format.

    :param circuit: Circuit to export.
    :param file_name: Target file path.
    :param options: Export options, including the optional profile selector.
    :param text_func: Optional progress-text callback.
    :param progress_func: Optional progress-value callback.
    :return: Logger with export messages.
    """
    if options.psse_export_mode == PsseExportMode.BatchZip:
        return save_psse_batch_zip(circuit=circuit,
                                   file_name=file_name,
                                   options=options,
                                   text_func=text_func,
                                   progress_func=progress_func)
    else:
        logger = Logger()
        raw_version: int = int(options.raw_version)

        # Forward the selected time index so the RAW writer exports either the
        # snapshot state or one explicit time-series point.
        raw_circuit = veragrid_to_raw(circuit,
                                      version=raw_version,
                                      logger=logger,
                                      topology_mode=options.psse_topology_mode,
                                      t_idx=options.t_idx)
        logger += write_raw(file_name, raw_circuit, version=raw_version)
        return logger


def save_psse_rawx(circuit: MultiCircuit,
                   file_name: str,
                   options: FileSavingOptions,
                   text_func=None,
                   progress_func=None) -> Logger:
    """
    Save the circuit information in PSSE RAWX format.

    :param circuit: Circuit to export.
    :param file_name: Target file path.
    :param options: Export options, including the optional profile selector.
    :param text_func: Optional progress-text callback.
    :param progress_func: Optional progress-value callback.
    :return: Logger with export messages.
    """
    if options.psse_export_mode == PsseExportMode.BatchZip:
        return save_psse_batch_zip(circuit=circuit,
                                   file_name=file_name,
                                   options=options,
                                   text_func=text_func,
                                   progress_func=progress_func)
    else:
        logger = Logger()

        # RAWX shares the same intermediate RAW circuit, so the time selector
        # must be forwarded here as well.
        raw_circuit = veragrid_to_raw(circuit,
                                      version=int(options.raw_version),
                                      logger=logger,
                                      topology_mode=options.psse_topology_mode,
                                      t_idx=options.t_idx)
        logger += write_rawx(file_name, raw_circuit)
        return logger


def compose_psse_batch_file_name(base_name: str,
                                 t_idx: int,
                                 time_label: str,
                                 extension: str) -> str:
    """
    Compose one deterministic file name for a PSSE batch export member.

    :param base_name: Base archive name without extension.
    :param t_idx: Time index of the exported profile point.
    :param time_label: Human-readable time label.
    :param extension: PSSE file extension, including the leading dot.
    :return: Sanitized internal file name.
    """
    safe_time_label: str = re.sub(r"[^0-9A-Za-z._-]+", "_", time_label).strip("_")

    if safe_time_label == "":
        safe_time_label = "time"
    else:
        pass

    return f"{base_name}_t{t_idx:05d}_{safe_time_label}{extension}"


def save_psse_batch_zip(circuit: MultiCircuit,
                        file_name: str,
                        options: FileSavingOptions,
                        text_func=None,
                        progress_func=None) -> Logger:
    """
    Export every time-series point into one ZIP archive with one PSSE file per step.

    :param circuit: Circuit to export.
    :param file_name: Target ZIP path.
    :param options: Export options, including version, topology and internal PSSE format.
    :param text_func: Optional progress-text callback.
    :param progress_func: Optional progress-value callback.
    :return: Logger with export messages.
    """
    logger = Logger()

    if not circuit.has_time_series:
        logger.add_error(msg="PSS/e batch export requires time-series data.")
        return logger
    else:
        pass

    total_steps: int = circuit.get_time_number()
    if total_steps <= 0:
        logger.add_error(msg="PSS/e batch export requires at least one time-series point.")
        return logger
    else:
        pass

    raw_version: int = int(options.raw_version)
    zip_extension: str
    _, zip_extension = os.path.splitext(file_name)
    if zip_extension.lower() == ".zip":
        zip_file_name: str = file_name
    else:
        zip_file_name = file_name + ".zip"

    if options.file_type == FileType.PSSE_rawx:
        internal_extension: str = ".rawx"
    else:
        internal_extension = ".raw"

    archive_base_name: str = os.path.splitext(os.path.basename(zip_file_name))[0]

    # Reuse one temporary file path for every time step. Each generated file is
    # zipped immediately afterwards, so only one export artifact exists on disk
    # at a time while the worker thread runs.
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file_name: str = os.path.join(temp_dir, "psse_batch_export" + internal_extension)

        with zipfile.ZipFile(zip_file_name, "w", zipfile.ZIP_DEFLATED) as zip_ptr:
            for t_idx in range(total_steps):
                if text_func is not None:
                    text_func(f"Exporting PSS/e profile [{t_idx}] {circuit.time_profile[t_idx]}...")
                else:
                    pass

                if progress_func is not None:
                    progress_value: float = (100.0 * float(t_idx)) / float(total_steps)
                    progress_func(progress_value)
                else:
                    pass

                raw_circuit = veragrid_to_raw(circuit,
                                              version=raw_version,
                                              logger=logger,
                                              topology_mode=options.psse_topology_mode,
                                              t_idx=t_idx)

                if options.file_type == FileType.PSSE_rawx:
                    logger += write_rawx(temp_file_name, raw_circuit)
                else:
                    logger += write_raw(temp_file_name, raw_circuit, version=raw_version)

                time_label: str = str(circuit.time_profile[t_idx])
                internal_file_name: str = compose_psse_batch_file_name(base_name=archive_base_name,
                                                                       t_idx=t_idx,
                                                                       time_label=time_label,
                                                                       extension=internal_extension)
                zip_ptr.write(temp_file_name, arcname=internal_file_name)

    if progress_func is not None:
        progress_func(100.0)
    else:
        pass

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


def compose_dgs_batch_file_name(base_name: str,
                                t_idx: int,
                                time_label: str) -> str:
    """
    Compose one deterministic file name for a DGS batch-export member.

    :param base_name: Base archive name without extension.
    :param t_idx: Time index of the exported profile point.
    :param time_label: Human-readable time label.
    :return: Sanitized internal file name.
    """
    safe_time_label: str = re.sub(r"[^0-9A-Za-z._-]+", "_", time_label).strip("_")

    if safe_time_label == "":
        safe_time_label = "time"
    else:
        pass

    return f"{base_name}_t{t_idx:05d}_{safe_time_label}.dgs"


def save_dgs_batch_zip(circuit: MultiCircuit,
                       file_name: str,
                       text_func=None,
                       progress_func=None) -> Logger:
    """
    Export every time-series point into one ZIP archive with one DGS file per step.

    :param circuit: Circuit to export.
    :param file_name: Target ZIP path.
    :param text_func: Optional progress-text callback.
    :param progress_func: Optional progress-value callback.
    :return: Logger with export messages.
    """
    logger = Logger()

    if not circuit.has_time_series:
        logger.add_error(msg="DGS batch export requires time-series data.")
        return logger
    else:
        pass

    total_steps: int = circuit.get_time_number()
    if total_steps <= 0:
        logger.add_error(msg="DGS batch export requires at least one time-series point.")
        return logger
    else:
        pass

    _, zip_extension = os.path.splitext(file_name)
    if zip_extension.lower() == ".zip":
        zip_file_name: str = file_name
    else:
        zip_file_name = file_name + ".zip"

    archive_base_name: str = os.path.splitext(os.path.basename(zip_file_name))[0]

    # Reuse one temporary file path for every time step. Each generated file is
    # zipped immediately afterwards, so only one export artifact exists on disk
    # at a time while the worker thread runs.
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file_name: str = os.path.join(temp_dir, "dgs_batch_export.dgs")

        with zipfile.ZipFile(zip_file_name, "w", zipfile.ZIP_DEFLATED) as zip_ptr:
            for t_idx in range(total_steps):
                if text_func is not None:
                    text_func(f"Exporting DGS profile [{t_idx}] {circuit.time_profile[t_idx]}...")
                else:
                    pass

                if progress_func is not None:
                    progress_value: float = (100.0 * float(t_idx)) / float(total_steps)
                    progress_func(progress_value)
                else:
                    pass

                dgs = circuit_to_dgs(grid=circuit, t_idx=t_idx)
                dgs.write_dgs(path=temp_file_name)

                time_label: str = str(circuit.time_profile[t_idx])
                internal_file_name: str = compose_dgs_batch_file_name(base_name=archive_base_name,
                                                                      t_idx=t_idx,
                                                                      time_label=time_label)
                zip_ptr.write(temp_file_name, arcname=internal_file_name)

    if progress_func is not None:
        progress_func(100.0)
    else:
        pass

    return logger


def save_dgs(circuit: MultiCircuit,
             file_name: str,
             options: FileSavingOptions,
             text_func=None,
             progress_func=None) -> Logger:
    """
    Save the circuit information in DGS format.

    :param circuit: Circuit to export.
    :param file_name: Target file path.
    :param options: Export options, including the optional profile selector.
    :param text_func: Optional progress-text callback.
    :param progress_func: Optional progress-value callback.
    :return: Logger with export messages.
    """
    if options.dgs_export_mode == DgsExportMode.BatchZip:
        return save_dgs_batch_zip(circuit=circuit,
                                  file_name=file_name,
                                  text_func=text_func,
                                  progress_func=progress_func)
    else:
        logger = Logger()

        # Forward the selected time index so the DGS writer exports either the
        # snapshot state or one explicit time-series point.
        dgs = circuit_to_dgs(grid=circuit, t_idx=options.t_idx)
        dgs.write_dgs(path=file_name)
        return logger


def compose_matpower_batch_file_name(base_name: str,
                                     t_idx: int,
                                     time_label: str) -> str:
    """
    Compose one deterministic file name for a MATPOWER batch-export member.

    :param base_name: Base archive name without extension.
    :param t_idx: Time index of the exported profile point.
    :param time_label: Human-readable time label.
    :return: Sanitized internal file name.
    """
    safe_time_label: str = re.sub(r"[^0-9A-Za-z._-]+", "_", time_label).strip("_")

    if safe_time_label == "":
        safe_time_label = "time"
    else:
        pass

    return f"{base_name}_t{t_idx:05d}_{safe_time_label}.m"


def save_matpower_batch_zip(circuit: MultiCircuit,
                            file_name: str,
                            text_func=None,
                            progress_func=None) -> Logger:
    """
    Export every time-series point into one ZIP archive with one MATPOWER file per step.

    :param circuit: Circuit to export.
    :param file_name: Target ZIP path.
    :param text_func: Optional progress-text callback.
    :param progress_func: Optional progress-value callback.
    :return: Logger with export messages.
    """
    logger = Logger()

    if not circuit.has_time_series:
        logger.add_error(msg="MATPOWER batch export requires time-series data.")
        return logger
    else:
        pass

    total_steps: int = circuit.get_time_number()
    if total_steps <= 0:
        logger.add_error(msg="MATPOWER batch export requires at least one time-series point.")
        return logger
    else:
        pass

    _, zip_extension = os.path.splitext(file_name)
    if zip_extension.lower() == ".zip":
        zip_file_name: str = file_name
    else:
        zip_file_name = file_name + ".zip"

    archive_base_name: str = os.path.splitext(os.path.basename(zip_file_name))[0]

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file_name: str = os.path.join(temp_dir, "matpower_batch_export.m")

        with zipfile.ZipFile(zip_file_name, "w", zipfile.ZIP_DEFLATED) as zip_ptr:
            for t_idx in range(total_steps):
                if text_func is not None:
                    text_func(f"Exporting MATPOWER profile [{t_idx}] {circuit.time_profile[t_idx]}...")
                else:
                    pass

                if progress_func is not None:
                    progress_value: float = (100.0 * float(t_idx)) / float(total_steps)
                    progress_func(progress_value)
                else:
                    pass

                time_label: str = str(circuit.time_profile[t_idx])
                internal_file_name: str = compose_matpower_batch_file_name(base_name=archive_base_name,
                                                                           t_idx=t_idx,
                                                                           time_label=time_label)
                case_name: str = os.path.splitext(internal_file_name)[0]
                write_matpower_case_file(file_name=temp_file_name,
                                         circuit=circuit,
                                         t_idx=t_idx,
                                         logger=logger,
                                         case_name=case_name)
                zip_ptr.write(temp_file_name, arcname=internal_file_name)

    if progress_func is not None:
        progress_func(100.0)
    else:
        pass

    return logger


def save_matpower(circuit: MultiCircuit,
                  file_name: str,
                  options: FileSavingOptions,
                  text_func=None,
                  progress_func=None) -> Logger:
    """
    Save the circuit information in MATPOWER format.

    :param circuit: Circuit to export.
    :param file_name: Target file path.
    :param options: Export options, including the optional profile selector.
    :param text_func: Optional progress-text callback.
    :param progress_func: Optional progress-value callback.
    :return: Logger with export messages.
    """
    if options.matpower_export_mode == MatpowerExportMode.BatchZip:
        return save_matpower_batch_zip(circuit=circuit,
                                       file_name=file_name,
                                       text_func=text_func,
                                       progress_func=progress_func)
    else:
        return write_matpower_case_file(file_name=file_name,
                                        circuit=circuit,
                                        t_idx=options.t_idx)


def compose_ucte_batch_file_name(base_name: str,
                                 t_idx: int,
                                 time_label: str) -> str:
    """
    Compose one deterministic file name for a UCTE batch-export member.

    :param base_name: Base archive name without extension.
    :param t_idx: Time index of the exported profile point.
    :param time_label: Human-readable time label.
    :return: Sanitized internal file name.
    """
    safe_time_label: str = re.sub(r"[^0-9A-Za-z._-]+", "_", time_label).strip("_")

    if safe_time_label == "":
        safe_time_label = "time"
    else:
        pass

    return f"{base_name}_t{t_idx:05d}_{safe_time_label}.uct"


def save_ucte_batch_zip(circuit: MultiCircuit,
                        file_name: str,
                        text_func=None,
                        progress_func=None) -> Logger:
    """
    Export every time-series point into one ZIP archive with one UCTE file per step.

    :param circuit: Circuit to export.
    :param file_name: Target ZIP path.
    :param text_func: Optional progress-text callback.
    :param progress_func: Optional progress-value callback.
    :return: Logger with export messages.
    """
    logger: Logger = Logger()

    if not circuit.has_time_series:
        logger.add_error(msg="UCTE batch export requires time-series data.")
        return logger
    else:
        pass

    total_steps: int = circuit.get_time_number()
    if total_steps <= 0:
        logger.add_error(msg="UCTE batch export requires at least one time-series point.")
        return logger
    else:
        pass

    _, zip_extension = os.path.splitext(file_name)
    if zip_extension.lower() == ".zip":
        zip_file_name: str = file_name
    else:
        zip_file_name = file_name + ".zip"

    archive_base_name: str = os.path.splitext(os.path.basename(zip_file_name))[0]

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file_name: str = os.path.join(temp_dir, "ucte_batch_export.uct")

        with zipfile.ZipFile(zip_file_name, "w", zipfile.ZIP_DEFLATED) as zip_ptr:
            t_idx: int
            for t_idx in range(total_steps):
                if text_func is not None:
                    text_func(f"Exporting UCTE profile [{t_idx}] {circuit.time_profile[t_idx]}...")
                else:
                    pass

                if progress_func is not None:
                    progress_value: float = (100.0 * float(t_idx)) / float(total_steps)
                    progress_func(progress_value)
                else:
                    pass

                time_label: str = str(circuit.time_profile[t_idx])
                internal_file_name: str = compose_ucte_batch_file_name(base_name=archive_base_name,
                                                                       t_idx=t_idx,
                                                                       time_label=time_label)
                write_ucte(file_name=temp_file_name,
                           circuit=circuit,
                           t_idx=t_idx,
                           logger=logger)
                zip_ptr.write(temp_file_name, arcname=internal_file_name)

    if progress_func is not None:
        progress_func(100.0)
    else:
        pass

    return logger


def save_ucte(circuit: MultiCircuit,
              file_name: str,
              options: FileSavingOptions,
              text_func=None,
              progress_func=None) -> Logger:
    """
    Save the circuit information in UCTE format.

    :param circuit: Circuit to export.
    :param file_name: Target file path.
    :param options: Export options, including the optional profile selector.
    :param text_func: Optional progress-text callback.
    :param progress_func: Optional progress-value callback.
    :return: Logger with export messages.
    """
    if options.ucte_export_mode == UcteExportMode.BatchZip:
        return save_ucte_batch_zip(circuit=circuit,
                                   file_name=file_name,
                                   text_func=text_func,
                                   progress_func=progress_func)
    else:
        return write_ucte(file_name=file_name,
                          circuit=circuit,
                          t_idx=options.t_idx)


class FileSave:
    """
    FileSave
    """

    def __init__(self,
                 circuit: MultiCircuit,
                 file_name: str,
                 options: FileSavingOptions | None = None,
                 multiverse: MultiVerse | None = None,
                 text_func=None,
                 progress_func=None):
        """
        File saver
        :param circuit: MultiCircuit
        :param file_name: file name to save to
        :param options: FileSavingOptions (optional)
        :param multiverse: Multiverse instance
        :param text_func: Pointer to the text function
        :param progress_func: Pointer to the progress function
        """
        self.circuit = circuit

        self.multiverse: MultiVerse | None = multiverse

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

        if self.options.file_type == FileType.VeraGrid_xlsx4 or self.options.file_type == FileType.generic_excel:
            logger = save_veragrid_excel(
                circuit=self.circuit,
                file_name=self.file_name
            )

        elif self.options.file_type == FileType.VeraGrid:
            if self.multiverse is None:
                logger = save_veragrid_circuit(
                    circuit=self.circuit,
                    file_name=self.file_name,
                    options=self.options,
                    text_func=self.text_func,
                    progress_func=self.progress_func
                )
            else:
                logger = save_veragrid_multiverse(
                    file_name=self.file_name,
                    multiverse=self.multiverse,
                    options=self.options,
                    text_func=self.text_func,
                    progress_func=self.progress_func
                )

        elif self.options.file_type == FileType.VeraGridScenario:
            logger = save_veragrid_circuit(
                circuit=self.circuit,
                file_name=self.file_name,
                options=self.options,
                text_func=self.text_func,
                progress_func=self.progress_func
            )

        elif self.options.file_type == FileType.VeraGrid_delta:
            logger = save_veragrid_delta(
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
                file_name=self.file_name,
                options=self.options,
                text_func=self.text_func,
                progress_func=self.progress_func,
            )

        elif self.options.file_type == FileType.PSSE_raw:

            logger = save_psse_raw(
                circuit=self.circuit,
                file_name=self.file_name,
                options=self.options,
                text_func=self.text_func,
                progress_func=self.progress_func,
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
                options=self.options,
                text_func=self.text_func,
                progress_func=self.progress_func,
            )

        elif self.options.file_type == FileType.Matpower:
            logger = save_matpower(
                circuit=self.circuit,
                file_name=self.file_name,
                options=self.options,
                text_func=self.text_func,
                progress_func=self.progress_func,
            )

        elif self.options.file_type == FileType.UCTE:
            logger = save_ucte(
                circuit=self.circuit,
                file_name=self.file_name,
                options=self.options,
                text_func=self.text_func,
                progress_func=self.progress_func,
            )

        else:
            logger = Logger()
            logger.add_error('File path extension not understood', self.file_name)

        return logger
