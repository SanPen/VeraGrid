from pathlib import Path

import numpy as np

from VeraGridEngine.api import open_file
from VeraGridEngine.IO.Eurostag import EurostagCircuit
from VeraGridEngine.Simulations.PowerFlow.power_flow_driver import PowerFlowDriver
from VeraGridEngine.Simulations.PowerFlow.power_flow_options import PowerFlowOptions, SolverType
from VeraGridEngine.enumerations import TapModuleControl


EUROSTAG_FIXTURES = Path(__file__).resolve().parents[2] / "data" / "grids" / "Eurostag"


def test_eurostag_case1_auto_resolves_matching_dta() -> None:
    circuit = open_file(str(EUROSTAG_FIXTURES / "case1" / "case1.ech"))

    assert circuit.get_bus_number() == 11
    assert circuit.get_transformers2w_number() == 4
    assert circuit.get_switches_number() == 0

    buses = {bus.code: bus for bus in circuit.buses}
    assert buses["NHVCEQ"].is_slack
    assert abs(buses["NHVCEQ"].Va0) < 1e-12
    assert abs(buses["NGENA1"].Vm0 - 1.0) < 1e-12

    generators = {gen.name: gen for gen in circuit.generators}
    assert generators["GENA1"].Snom == 1150.0
    assert generators["GENA1"].control_mode.name == "V"
    assert generators["GENA1"].control_bus.code == "NGENA1"

    transformers = {tr.code: tr for tr in circuit.transformers2w}
    assert transformers["NHVA1_NHVA2_1"].Vsc == 10.0
    assert transformers["NHVA1_NHVA2_1"].tap_module_control_mode == TapModuleControl.fixed


def test_eurostag_breaker_case_imports_couplers_as_switches() -> None:
    folder = EUROSTAG_FIXTURES / "breaker_case"
    circuit = open_file([str(folder / "breaker_case.ech"), str(folder / "breaker_case.dta"), str(folder / "breaker_case.lf")])

    assert circuit.get_switches_number() == 4
    assert circuit.get_transformers2w_number() == 7

    switches = {switch.code: switch for switch in circuit.get_switches()}
    assert switches["NHVD1_NHVD2_1"].active
    assert not switches["NHVD1_NHVD2_2"].active


def test_eurostag_circuit_keeps_parsed_record_fields() -> None:
    folder = EUROSTAG_FIXTURES / "case1"
    eurostag_grid = EurostagCircuit()
    eurostag_grid.read_files(folder / "case1.ech", folder / "case1.dta")

    nodes = {node.name: node for node in eurostag_grid.nodes}
    assert nodes["NGENA1"].area == "A"
    assert nodes["NHVCEQ"].is_slack
    assert abs(nodes["NHVCEQ"].initial_angle) < 1e-12

    lines = {line.code: line for line in eurostag_grid.lines}
    assert lines["NHVA1_NHVA3_1"].semi_shunt_conductance == 0.0
    assert lines["NHVA1_NHVA3_1"].semi_shunt_susceptance == 0.27869

    generators = {gen.name: gen for gen in eurostag_grid.generators}
    assert generators["GENA1"].regulated_node_name == "NGENA1"
    assert generators["GENA1"].reactive_sharing_coefficient == 1.0

    transformers = {tr.code: tr for tr in eurostag_grid.type8_transformers}
    assert transformers["NHVA1_NHVA2_1"].saturation_exponent == 7.0
    assert transformers["NHVA1_NHVA2_1"].get_current_leakage_impedance() == 10.0


def test_eurostag_ieee14_import_converges() -> None:
    folder = EUROSTAG_FIXTURES / "ieee14"
    circuit = open_file([str(folder / "fech.ech"), str(folder / "fdta.dta")])

    assert circuit.get_bus_number() == 14
    assert circuit.get_lines_number() == 17
    assert circuit.get_transformers2w_number() == 3

    transformers = {tr.code: tr for tr in circuit.transformers2w}
    assert np.isclose(transformers["BUS    4_BUS    7_1"].tap_module, 0.9803913043478261)
    assert np.isclose(transformers["BUS    4_BUS    9_1"].tap_module, 0.961536231884058)
    assert np.isclose(transformers["BUS    5_BUS    6_1"].tap_module, 0.9433768115942028)

    opts = PowerFlowOptions(
        solver_type=SolverType.NR,
        verbose=0,
        control_q=False,
        retry_with_other_methods=False,
    )
    driver = PowerFlowDriver(circuit, opts)
    driver.run()

    assert driver.results.converged
