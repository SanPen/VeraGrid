from pathlib import Path

from VeraGridEngine.IO.others.anarede import PWFParser, _split_sections


def test_mini_4bus_records_are_mapped_to_native_objects() -> None:
    """Check DBAR, DGBT, DGER, and DLIN against the external parser fixture."""
    data_directory: Path = Path(__file__).resolve().parents[2] / "data" / "grids" / "ANAREDE"
    parser = PWFParser(str(data_directory / "mini_4bus.pwf"))
    network = parser.network

    assert len(network.buses) == 4
    assert [(bus.type, bus.voltage, bus.angle) for bus in network.buses] == [
        (2, 1.0, 0.0),
        (1, 1.02, -5.0),
        (0, 1.0, -8.0),
        (0, 0.99, -10.0),
    ]
    assert {(load.bus, load.active_power, load.reactive_power)
            for load in network.loads} == {(3, 30.0, 15.0), (4, 20.0, 8.0)}
    assert [(generator.number, generator.max_active_gen)
            for generator in network.generators] == [(1, 120.0), (2, 80.0)]
    assert len(network.lines) == 1
    assert (network.lines[0].from_bus, network.lines[0].to_bus) == (1, 3)
    assert (network.lines[0].r, network.lines[0].x) == (0.015, 0.08)
    assert len(network.transformers) == 1
    assert (network.transformers[0].from_bus, network.transformers[0].to_bus) == (2, 4)
    assert network.transformers[0].tap == 0.98


def test_mini_4bus_converts_to_multicircuit() -> None:
    """Check that the parsed native records become VeraGrid devices."""
    data_directory: Path = Path(__file__).resolve().parents[2] / "data" / "grids" / "ANAREDE"
    grid = PWFParser(str(data_directory / "mini_4bus.pwf")).to_veragrid()

    assert len(grid.buses) == 4
    assert len(grid.lines) == 1
    assert len(grid.transformers2w) == 1
    assert len(grid.loads) == 2
    assert len(grid.generators) == 2


def test_mini_dc_reconstructs_hvdc_line() -> None:
    """Check the DELO/DCBA/DCLI/DCNV/DCCV join into HvdcLine."""
    data_directory: Path = Path(__file__).resolve().parents[2] / "data" / "grids" / "ANAREDE"
    grid = PWFParser(str(data_directory / "mini_dc.pwf")).to_veragrid()

    assert len(grid.hvdc_lines) == 1
    hvdc = grid.hvdc_lines[0]
    assert hvdc.bus_from.name == "LOAD A"
    assert hvdc.bus_to.name == "LOAD B"
    assert hvdc.Pset == 80.0
    assert hvdc.r == 5.0
    assert hvdc.dc_link_voltage == 500.0
    assert hvdc.active


def test_mini_dc_delo_is_not_read_as_a_load() -> None:
    """Check that the DELO record is represented only by the HVDC object."""
    data_directory: Path = Path(__file__).resolve().parents[2] / "data" / "grids" / "ANAREDE"
    network = PWFParser(str(data_directory / "mini_dc.pwf")).network

    assert [(load.bus, load.active_power, load.reactive_power)
            for load in network.loads] == [(3, 30.0, 15.0), (4, 20.0, 8.0)]


def test_ieee14_real_file_parses_and_converts() -> None:
    """Smoke-test the supplied real IEEE-14 ANAREDE file."""
    data_directory: Path = Path(__file__).resolve().parents[2] / "data" / "grids" / "ANAREDE"
    parser = PWFParser(str(data_directory / "ieee14.pwf"))
    network = parser.network
    grid = parser.to_veragrid()

    assert len(network.buses) == 14
    assert len(network.lines) == 17
    assert len(network.transformers) == 3
    assert len(network.loads) == 11
    assert len(grid.buses) == 14
    assert len(grid.areas) == 1
    assert len(grid.zones) == 1
    assert all(bus.area is grid.areas[0] for bus in grid.buses)
    assert all(bus.zone is grid.zones[0] for bus in grid.buses)
    assert len(grid.lines) == 17
    assert len(grid.transformers2w) == 3
    assert len(grid.loads) == 11


def test_latin1_pwfs_are_read_without_utf8_errors(tmp_path: Path) -> None:
    """ANAREDE text with Latin-1 metadata must remain readable."""
    data_directory: Path = Path(__file__).resolve().parents[2] / "data" / "grids" / "ANAREDE"
    source: bytes = (data_directory / "mini_4bus.pwf").read_bytes()
    latin1_source: bytes = source.replace(
        b"Rede sintetica", "Rede com acentuação".encode("latin-1")
    )
    path: Path = tmp_path / "latin1.pwf"
    path.write_bytes(latin1_source)

    assert len(PWFParser(str(path)).network.buses) == 4


def test_utf8_metadata_can_be_recovered_after_latin1_default(tmp_path: Path) -> None:
    """Use chardet recovery when UTF-8 metadata would be mojibake as Latin-1."""
    path: Path = tmp_path / "utf8.pwf"
    path.write_bytes("TITU\nRede com acentuação\n99999\nFIM\n".encode("utf-8"))

    _, sections = _split_sections(str(path), {"TITU": "case title"})

    assert sections["TITU"][1] == "Rede com acentuação"
