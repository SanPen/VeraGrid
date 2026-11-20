# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Reference-case tests that compare CGMES import/export against the IEEE 14 RAW benchmark."""

import os
from io import BytesIO
from pathlib import Path
from xml.etree import ElementTree
from zipfile import ZipFile

import numpy as np
import pandas as pd

import VeraGridEngine.api as gce
from VeraGridEngine.IO.file_open import FileOpen, FileOpenOptions
from VeraGridEngine.IO.cim.cgmes.cgmes_circuit import CgmesCircuit
from VeraGridEngine.IO.cim.cgmes.cgmes_create_instances import create_cgmes_sub_load_area
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import CgmesProfileType
from VeraGridEngine.IO.cim.cgmes.cgmes_export import CimExporter
from VeraGridEngine.data_logger import DataLogger

pd.set_option("display.max_colwidth", None)


def test_cgmes_24_export_resolves_load_area(tmp_path: Path) -> None:
    """The EQ export must define the LoadArea referenced by each SubLoadArea."""
    root: Path = Path(__file__).resolve().parents[4]
    grid = gce.open_file(str(root / "src/tests/data/grids/RAW/IEEE 14 bus.raw"))
    output: Path = tmp_path / "ieee14.zip"
    gce.save_cgmes_file(grid=grid, filename=str(output),
                        cgmes_boundary_set_path=str(root / "src/VeraGrid/data/ENTSOe_boundary_set.zip"),
                        cgmes_version=gce.CGMESVersions.v2_4_15, pf_results=gce.power_flow(grid))

    with ZipFile(output) as archive:
        eq_name: str = next(name for name in archive.namelist() if "_EQ_" in name)
        eq = ElementTree.fromstring(archive.read(eq_name))

    cim: str = "{http://iec.ch/TC57/2013/CIM-schema-cim16#}"
    rdf: str = "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}"
    area_ids: set[str] = {area.attrib[rdf + "ID"] for area in eq.findall(cim + "LoadArea")}
    references: list[str] = [link.attrib[rdf + "resource"][1:]
                             for link in eq.findall(cim + "SubLoadArea/" + cim + "SubLoadArea.LoadArea")]
    assert references
    assert all(reference in area_ids for reference in references)
    assert eq.find(cim + "LoadArea/" + cim + "IdentifiedObject.name") is not None


def test_cgmes_24_eq_only_resolves_load_area() -> None:
    """EQ-only export retains the LoadArea identity without OP attributes."""
    model: CgmesCircuit = CgmesCircuit(cgmes_version=gce.CGMESVersions.v2_4_15)
    create_cgmes_sub_load_area(model, gce.CGMESVersions.v2_4_15, DataLogger())
    exporter: CimExporter = CimExporter(model, [CgmesProfileType.EQ], False)
    stream: BytesIO = BytesIO()
    exporter.serialize(stream, "EQ")
    eq = ElementTree.fromstring(stream.getvalue())
    cim: str = "{http://iec.ch/TC57/2013/CIM-schema-cim16#}"
    rdf: str = "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}"
    area = eq.find(cim + "LoadArea")
    reference = eq.find(cim + "SubLoadArea/" + cim + "SubLoadArea.LoadArea")
    assert area is not None
    assert reference is not None
    assert reference.attrib[rdf + "resource"] == "#" + area.attrib[rdf + "ID"]
    assert len(area) == 0


def test_cgmes_export_sv_status_values(tmp_path: Path) -> None:
    """Export active and inactive equipment status in the SV profile."""
    root: Path = Path(__file__).resolve().parents[4]
    grid = gce.open_file(str(root / "src/tests/data/grids/RAW/IEEE 14 bus.raw"))
    grid.loads[0].active = False
    results = gce.power_flow(grid)
    for version in (gce.CGMESVersions.v2_4_15, gce.CGMESVersions.v3_0_0):
        output: Path = tmp_path / f"status_{version.value}.zip"
        gce.save_cgmes_file(grid=grid, filename=str(output),
                            cgmes_boundary_set_path=str(root / "src/VeraGrid/data/ENTSOe_boundary_set.zip"),
                            cgmes_version=version, pf_results=results)
        with ZipFile(output) as archive:
            sv_name: str = next(name for name in archive.namelist() if "_SV_" in name)
            sv = ElementTree.fromstring(archive.read(sv_name))

        if version == gce.CGMESVersions.v2_4_15:
            cim: str = "{http://iec.ch/TC57/2013/CIM-schema-cim16#}"
        else:
            cim = "{http://iec.ch/TC57/CIM100#}"
        statuses = sv.findall(cim + "SvStatus")
        values: list[str | None] = [status.findtext(cim + "SvStatus.inService") for status in statuses]
        assert "true" in values
        assert "false" in values
        assert all(value in ("true", "false") for value in values)
        assert all(status.find(cim + "SvStatus.ConductingEquipment") is not None for status in statuses)


def test_ieee14_cgmes() -> None:
    """Export IEEE 14 from RAW to CGMES, re-import it, and match the benchmark voltage profile."""

    file_open_1 = FileOpen(
        file_name=os.path.join("data", "grids", "RAW", "IEEE 14 bus.raw"),
        options=FileOpenOptions(
            file_type=gce.FileType.PSSE_raw,
            cgmes_map_areas_like_raw=True,
            cgmes_try_to_map_dc_to_hvdc_line=True,
            psse_adjust_taps_to_discrete_positions=True,
        ),
    )
    grid_1 = file_open_1.open()
    numerical_circuit_1 = gce.compile_numerical_circuit_at(grid_1)
    power_flow_results_1 = gce.power_flow(grid_1)

    gce.detect_substations(grid=grid_1)

    boundary_set = os.path.join(
        "data", "grids", "CGMES_2_4_15",
        "TestConfigurations_packageCASv2.0", "MicroGrid", "BaseCase_BC",
        "CGMES_v2.4.15_MicroGridTestConfiguration_BD_v2.zip",
    )
    output_cgmes_path = os.path.join("data", "output", "IEEE14_test_ieee_export.zip")

    gce.save_cgmes_file(grid=grid_1,
                        filename=output_cgmes_path,
                        cgmes_boundary_set_path=boundary_set,
                        cgmes_version=gce.CGMESVersions.v2_4_15,
                        pf_results=power_flow_results_1)

    file_open_2 = FileOpen(
        file_name=[output_cgmes_path, boundary_set],
        options=FileOpenOptions(
            cgmes_map_areas_like_raw=True,
            cgmes_try_to_map_dc_to_hvdc_line=True,
            psse_adjust_taps_to_discrete_positions=True,
            file_type=gce.FileType.CGMES,
            cgmes_version=gce.CGMESVersions.v2_4_15,
        ),
    )
    grid_2 = file_open_2.open()
    numerical_circuit_2 = gce.compile_numerical_circuit_at(grid_2)
    power_flow_results_2 = gce.power_flow(grid_2)

    structures_match, structure_logger = numerical_circuit_1.compare(numerical_circuit_2)
    if not structures_match:
        print("\n\tTUC 17.1 is NOT OK\n")
        structure_logger.print("CGMES roundtrip comparison with the original")
        output_dir = os.path.join("data", "output")
        os.makedirs(output_dir, exist_ok=True)
        structure_logger.to_xlsx(os.path.join(output_dir, "tuc_17_1_ieee14.xlsx"))
    else:
        print("TUC 17.1 is OK")

    file_open_3 = FileOpen(
        file_name=[os.path.join("data", "grids", "CGMES_2_4_15", "IEEE 14 bus.zip"), boundary_set],
        options=FileOpenOptions(
            cgmes_map_areas_like_raw=True,
            cgmes_try_to_map_dc_to_hvdc_line=True,
            psse_adjust_taps_to_discrete_positions=True,
            file_type=gce.FileType.CGMES,
            cgmes_version=gce.CGMESVersions.v2_4_15,
        ),
    )
    grid_3 = file_open_3.open()
    numerical_circuit_3 = gce.compile_numerical_circuit_at(grid_3)
    power_flow_results_3 = gce.power_flow(grid_3)

    cim_converter_match, cim_converter_logger = numerical_circuit_1.compare(numerical_circuit_3)
    if not cim_converter_match:
        cim_converter_logger.print("CGMES cim-converter comparison with the original")
        output_dir = os.path.join("data", "output")
        os.makedirs(output_dir, exist_ok=True)
        cim_converter_logger.to_xlsx(os.path.join(output_dir, "tuc_17_1_ieee14_cim_converter.xlsx"))
    else:
        print("TUC Cimconverter 17.1 ok")

    results_folder = os.path.join("data", "results")
    reference_results = "IEEE 14 bus.sav.xlsx"
    voltage_reference = pd.read_excel(os.path.join(results_folder, reference_results),
                                      sheet_name="Vabs", index_col=0)
    voltage_psse = voltage_reference.values[:, 0]
    voltage_gc = np.abs(power_flow_results_1.voltage)
    voltage_gc = voltage_gc[:len(voltage_psse)]
    raw_matches_reference = np.allclose(voltage_gc, voltage_psse, atol=1e-6)
    assert raw_matches_reference

    voltage_reference = pd.read_excel(os.path.join("data", "results", "IEEE 14 bus.sav.xlsx"),
                                      sheet_name="Vabs", index_col=0)

    bus_df_1 = power_flow_results_1.get_bus_df()
    bus_df_2 = power_flow_results_2.get_bus_df()
    bus_df_3 = power_flow_results_3.get_bus_df()
    diff_12 = bus_df_1 - bus_df_2
    diff_13 = bus_df_1 - bus_df_3

    grid_1_ok = np.allclose(bus_df_1["Vm"].values, voltage_reference.values[:, 0])
    print("\nGrid 1 (PSSe raw)", "Vm ok:", grid_1_ok)
    print(power_flow_results_1.get_bus_df())

    grid_2_ok = np.allclose(bus_df_2["Vm"].values, voltage_reference.values[:, 0])
    print("\nGrid 2 (CGMES - round-tripped)", "Vm ok:", grid_2_ok)
    print(power_flow_results_2.get_bus_df())

    print("\nDifference raw to VeraGrid CGMES")
    print(diff_12)
    print("max err:", np.max(np.abs(diff_12.values)))

    print("\nDifference raw to Cim-converter CGMES")
    print(diff_13)
    print("max err:", np.max(np.abs(diff_13.values)))

    assert grid_1_ok
    assert grid_2_ok
