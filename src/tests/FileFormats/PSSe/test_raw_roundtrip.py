# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import os
from pathlib import Path

from VeraGridEngine.enumerations import SimulationTypes
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.Simulations.driver_template import DriverToSave
from VeraGridEngine.IO.file_open import FileOpenOptions
from VeraGridEngine.IO.file_save import FileSavingOptions, FileSave, FileType
import VeraGridEngine.api as gc

TESTS_ROOT: Path = Path(__file__).resolve().parents[2]
DATA_ROOT: Path = TESTS_ROOT / "data"
OUTPUT_ROOT: Path = DATA_ROOT / "output" / "raw_export_result"


def get_grid_path(file_name: str) -> str:
    """
    Build the absolute path to a RAW/RAWX test grid.
    :param file_name: file base name
    :return: absolute file path
    """
    return str(DATA_ROOT / "grids" / "RAW" / file_name)


def get_export_path(file_name: str) -> str:
    """
    Build the absolute path for a roundtrip export artifact.
    :param file_name: file base name
    :return: absolute file path
    """
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    return str(OUTPUT_ROOT / file_name)


def run_import_export_test(import_path: str, export_fname: str, version=33):
    """

    :param import_path:
    :param export_fname:
    :return:
    """
    logger = Logger()

    # RAW model import to MultiCircuit
    circuit_1 = gc.FileOpen(file_name=import_path, options=FileOpenOptions()).open()
    nc_1 = gc.compile_numerical_circuit_at(circuit_1)

    # pf_options = PowerFlowOptions()
    pf_results = gc.power_flow(circuit_1)

    pf_session_data = DriverToSave(name="powerflow results",
                                   tpe=SimulationTypes.PowerFlow_run,
                                   results=pf_results,
                                   logger=logger)
    export_suffix: str = Path(export_fname).suffix.lower()

    if export_suffix == ".raw":
        export_file_type: FileType = FileType.PSSE_raw
    elif export_suffix == ".rawx":
        export_file_type = FileType.PSSE_rawx
    else:
        raise ValueError(f"Unsupported PSSE export suffix: {export_suffix}")

    options = FileSavingOptions(file_type=export_file_type)
    options.raw_version = version
    options.sessions_data.append(pf_session_data)

    raw_export = FileSave(circuit=circuit_1,
                          file_name=export_fname,
                          options=options)
    raw_export.save()

    circuit_2 = gc.FileOpen(file_name=export_fname, options=FileOpenOptions()).open()
    nc_2 = gc.compile_numerical_circuit_at(circuit_2)

    ok, logger = circuit_1.compare_circuits(circuit_2)

    if not ok:
        logger.print()

    ok, logger = nc_1.compare(nc_2=nc_2, tol=1e-6)

    if ok:
        print("\nNumerical circuits are identical")
    else:
        logger.print()

    assert ok




def test_raw_ieee_14_roundtrip():
    """

    :return:
    """
    test_grid_name = 'IEEE 14 bus.raw'
    raw_path = get_grid_path(test_grid_name)
    export_name = get_export_path(test_grid_name)
    run_import_export_test(import_path=raw_path, export_fname=export_name, version=33)


def test_raw_ieee_30_roundtrip():
    """

    :return:
    """
    test_grid_name = 'IEEE 30 bus.raw'
    raw_path = get_grid_path(test_grid_name)
    export_name = get_export_path(test_grid_name)
    run_import_export_test(import_path=raw_path, export_fname=export_name, version=33)


def test_raw_ieee_14_fs_ss_roundtrip():
    """

    :return:
    """
    test_grid_name = 'IEEE_14_v35_3_nudox_1_hvdc_desf_rates_fs_ss.raw'
    raw_path = get_grid_path(test_grid_name)
    export_name = get_export_path(test_grid_name)
    run_import_export_test(import_path=raw_path, export_fname=export_name, version=35)


# def test_raw_ieee_14_fs_ss_wo_pst_roundtrip():
#     """
#
#     :return:
#     """
#     script_path = os.path.abspath(__file__)
#     test_grid_name = 'IEEE_14_v35_3_nudox_1_hvdc_desf_rates_fs_ss_wo_pst.raw'
#     raw_path = os.path.join('data', 'grids', 'RAW', test_grid_name)
#     export_name = os.path.join('data', 'output', 'raw_export_result', test_grid_name)
#     run_import_export_test(import_path=raw_path, export_fname=export_name, version=35)
#
#
# def test_raw_ieee_14_fs_ss_wo_pst_sws_roundtrip():
#     """
#
#     :return:
#     """
#     script_path = os.path.abspath(__file__)
#     test_grid_name = 'IEEE_14_v35_3_nudox_1_hvdc_desf_rates_fs_ss_wo_pst_SWS.raw'
#     raw_path = os.path.join('data', 'grids', 'RAW', test_grid_name)
#     export_name = os.path.join('data', 'output', 'raw_export_result', test_grid_name)
#     run_import_export_test(import_path=raw_path, export_fname=export_name, version=35)


def test_rawx_roundtrip():
    test_grid_name = 'IEEE 14 bus.rawx'
    raw_path = get_grid_path(test_grid_name)
    export_name = get_export_path(test_grid_name)
    run_import_export_test(import_path=raw_path, export_fname=export_name)
