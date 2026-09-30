from pathlib import Path

from VeraGridEngine.IO.file_open import determine_file_type
from VeraGridEngine.IO.others.pandapower_parser import PANDAPOWER_AVAILABLE
from VeraGridEngine.enumerations import FileType
from VeraGrid.Gui.Main.SubClasses.io import IoMain


def test_determine_file_type_accepts_dotted_grid_names() -> None:
    """
    File-type detection must use the real extension, not every suffix in the name.
    """
    assert determine_file_type("5Bus_PST_FACTS_Fig4.10.gridcal") == FileType.VeraGrid
    assert determine_file_type("5Bus_PST_FACTS_Fig4.10(Pt).gridcal") == FileType.VeraGrid
    assert determine_file_type("scenario.v1.dgridcal") == FileType.VeraGrid_delta
    assert determine_file_type("case.2024.rawx") == FileType.PSSE_rawx


def test_determine_file_type_keeps_supported_compound_extensions() -> None:
    """
    Compound extensions that are meaningful formats still need to be recognized.
    """
    assert determine_file_type("network.v1.xiidm.bz2") == FileType.Iidm


def test_determine_file_type_detects_anarede_pwf() -> None:
    """ANAREDE PWF files must remain accepted by the generic opener."""
    assert determine_file_type("case.pwf") == FileType.PWF


def test_gui_accepts_pwf_extension_without_case_sensitivity() -> None:
    """Drag-and-drop must accept both common PWF filename casings."""
    io_main = IoMain.__new__(IoMain)
    io_main.accepted_extensions = [".pwf"]

    assert io_main.check_extension("case.pwf")
    assert io_main.check_extension("case.PWF")


def test_determine_file_type_detects_eurostag_files() -> None:
    assert determine_file_type("case1.ech") == FileType.Eurostag
    assert determine_file_type("case1.dta") == FileType.Eurostag
    assert determine_file_type(["case1.ech", "case1.dta"]) == FileType.Eurostag
    assert determine_file_type(["case1.ech", "case1.dta", "case1.lf"]) == FileType.Eurostag


def test_determine_file_type_detects_pandapower_json_fixture() -> None:
    if not PANDAPOWER_AVAILABLE:
        return

    fixture = Path(__file__).resolve().parents[1] / "data" / "grids" / "state-estimation" / "finalized.json"
    assert determine_file_type(str(fixture)) == FileType.PandaPower
