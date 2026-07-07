from VeraGridEngine.IO.file_open import determine_file_type
from VeraGridEngine.enumerations import FileType


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


def test_determine_file_type_detects_eurostag_files() -> None:
    assert determine_file_type("case1.ech") == FileType.Eurostag
    assert determine_file_type("case1.dta") == FileType.Eurostag
    assert determine_file_type(["case1.ech", "case1.dta"]) == FileType.Eurostag
    assert determine_file_type(["case1.ech", "case1.dta", "case1.lf"]) == FileType.Eurostag
