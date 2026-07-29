from __future__ import annotations

import numpy as np
from PySide6 import QtCore, QtWidgets

from VeraGrid.Gui.DeviceEditors.AdmittanceMatrixEditor.admittance_matrix_editor import (
    AdmittanceMatrixEditorWidget,
    AdmittanceMatrixTableModel,
    project_admittance_matrix_to_phase_state,
)
from VeraGrid.Gui.DeviceEditors.LineLocationsEditor.line_locations_editor import (
    LineLocationsTableModel,
    build_line_locations_csv_text,
    parse_line_locations_text,
)
from VeraGridEngine.Devices.admittance_matrix import AdmittanceMatrix
from VeraGridEngine.Devices.Branches.line_locations import LineLocations


def _build_demo_admittance_matrix() -> AdmittanceMatrix:
    """
    Build one three-phase admittance matrix for editor tests.

    :return: Configured admittance matrix.
    """
    admittance_matrix: AdmittanceMatrix = AdmittanceMatrix(size=3)
    admittance_matrix.phN = False
    admittance_matrix.phA = True
    admittance_matrix.phB = True
    admittance_matrix.phC = True
    admittance_matrix.values = np.array(
        [
            [1.0 + 2.0j, 3.0 + 4.0j, 5.0 + 6.0j],
            [7.0 + 8.0j, 9.0 + 10.0j, 11.0 + 12.0j],
            [13.0 + 14.0j, 15.0 + 16.0j, 17.0 + 18.0j],
        ],
        dtype=complex,
    )
    return admittance_matrix


def test_admittance_matrix_model_preserves_surviving_entries() -> None:
    """
    Verify that toggling phases resizes the matrix without scrambling matching rows and columns.
    """
    app: QtWidgets.QApplication | None = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    else:
        pass

    model: AdmittanceMatrixTableModel = AdmittanceMatrixTableModel(
        admittance_matrix=_build_demo_admittance_matrix(),
    )

    model.set_phase_enabled("B", False)
    reduced_matrix: AdmittanceMatrix = model.to_admittance_matrix()

    assert reduced_matrix.size == 2
    assert reduced_matrix.phA is True
    assert reduced_matrix.phB is False
    assert reduced_matrix.phC is True
    assert reduced_matrix.values[0, 0] == 1.0 + 2.0j
    assert reduced_matrix.values[0, 1] == 5.0 + 6.0j
    assert reduced_matrix.values[1, 0] == 13.0 + 14.0j
    assert reduced_matrix.values[1, 1] == 17.0 + 18.0j

    model.set_phase_enabled("N", True)
    expanded_matrix: AdmittanceMatrix = model.to_admittance_matrix()

    assert expanded_matrix.size == 3
    assert expanded_matrix.phN is True
    assert expanded_matrix.phA is True
    assert expanded_matrix.phB is False
    assert expanded_matrix.phC is True
    assert expanded_matrix.values[1, 1] == 1.0 + 2.0j
    assert expanded_matrix.values[1, 2] == 5.0 + 6.0j
    assert expanded_matrix.values[2, 1] == 13.0 + 14.0j
    assert expanded_matrix.values[2, 2] == 17.0 + 18.0j
    assert expanded_matrix.values[0, 0] == 0.0 + 0.0j


def test_project_admittance_matrix_to_phase_state_keeps_selected_abc_subset() -> None:
    """
    Verify that projecting a full ABC matrix to an ABC subset preserves the expected entries.
    """
    source_matrix: AdmittanceMatrix = AdmittanceMatrix(size=4)
    source_matrix.phN = False
    source_matrix.phA = True
    source_matrix.phB = True
    source_matrix.phC = True
    source_matrix.values = np.array(
        [
            [0.0 + 0.0j, 0.0 + 0.0j, 0.0 + 0.0j, 0.0 + 0.0j],
            [0.0 + 0.0j, 1.0 + 1.0j, 2.0 + 2.0j, 3.0 + 3.0j],
            [0.0 + 0.0j, 4.0 + 4.0j, 5.0 + 5.0j, 6.0 + 6.0j],
            [0.0 + 0.0j, 7.0 + 7.0j, 8.0 + 8.0j, 9.0 + 9.0j],
        ],
        dtype=complex,
    )

    projected_matrix: AdmittanceMatrix = project_admittance_matrix_to_phase_state(
        admittance_matrix=source_matrix,
        phase_state={"N": False, "A": True, "B": False, "C": True},
    )

    assert projected_matrix.size == 2
    assert projected_matrix.phN is False
    assert projected_matrix.phA is True
    assert projected_matrix.phB is False
    assert projected_matrix.phC is True
    assert projected_matrix.values[0, 0] == 1.0 + 1.0j
    assert projected_matrix.values[0, 1] == 3.0 + 3.0j
    assert projected_matrix.values[1, 0] == 7.0 + 7.0j
    assert projected_matrix.values[1, 1] == 9.0 + 9.0j


def test_admittance_matrix_editor_widget_exposes_ys_and_ysh_tables(qt_app: object) -> None:
    """
    Verify that the admittance editor widget exposes dedicated UI tables for ``ys`` and ``ysh``.
    """
    _qt_app: object = qt_app
    ys_matrix: AdmittanceMatrix = _build_demo_admittance_matrix()
    ysh_matrix: AdmittanceMatrix = _build_demo_admittance_matrix()

    widget: AdmittanceMatrixEditorWidget = AdmittanceMatrixEditorWidget(
        ys_admittance_matrix=ys_matrix,
        ysh_admittance_matrix=ysh_matrix,
        title="Admittance matrices",
        description="Dual-table test",
    )

    assert widget.ui.matrixTableView.model() is not None
    assert widget.ui.yshTableView.model() is not None
    assert widget.ui.yshTableView.isHidden() is False
    assert "ys" in widget.get_admittance_matrices()
    assert "ysh" in widget.get_admittance_matrices()

    widget.close()


def test_line_locations_model_roundtrip_and_remove_rows() -> None:
    """
    Verify that the line-locations model preserves values and renumbers rows after deletion.
    """
    app: QtWidgets.QApplication | None = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    else:
        pass

    line_locations: LineLocations = LineLocations()
    line_locations.add(sequence=0, latitude=10.0, longitude=20.0, altitude=5.0, idtag="a")
    line_locations.add(sequence=1, latitude=11.0, longitude=21.0, altitude=6.0, idtag="b")
    line_locations.add(sequence=2, latitude=12.0, longitude=22.0, altitude=7.0, idtag="c")

    model: LineLocationsTableModel = LineLocationsTableModel(line_locations=line_locations)
    model.remove_rows(row_indices=[1])
    roundtrip_value: LineLocations = model.to_line_locations()

    assert model.rowCount() == 2
    assert roundtrip_value.get_locations()[0].seq == 0
    assert roundtrip_value.get_locations()[0].lat == 10.0
    assert roundtrip_value.get_locations()[1].seq == 1
    assert roundtrip_value.get_locations()[1].lat == 12.0
    assert roundtrip_value.get_locations()[1].long == 22.0
    assert roundtrip_value.get_locations()[1].alt == 7.0
    assert roundtrip_value.get_locations()[1].idtag == "c"


def test_parse_line_locations_text_supports_headerless_coordinates_and_csv_roundtrip() -> None:
    """
    Verify that coordinate text can be imported without sequence columns and exported again as CSV.
    """
    parsed_rows: list[list[object]] = parse_line_locations_text(
        "10.5,20.5,5.0\n11.5,21.5,6.0,tag-b\n"
    )

    assert parsed_rows[0] == [0, 10.5, 20.5, 5.0, ""]
    assert parsed_rows[1] == [1, 11.5, 21.5, 6.0, "tag-b"]

    line_locations: LineLocations = LineLocations()
    line_locations.add(sequence=0, latitude=10.5, longitude=20.5, altitude=5.0, idtag="")
    line_locations.add(sequence=1, latitude=11.5, longitude=21.5, altitude=6.0, idtag="tag-b")
    csv_text: str = build_line_locations_csv_text(line_locations=line_locations)

    assert "sequence,latitude,longitude,altitude,idtag" in csv_text
    assert "0,10.5,20.5,5.0," in csv_text
    assert "1,11.5,21.5,6.0,tag-b" in csv_text
