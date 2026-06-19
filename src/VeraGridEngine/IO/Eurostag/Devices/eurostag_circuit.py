from __future__ import annotations

from pathlib import Path

from VeraGridEngine.IO.Eurostag.Devices.branch import EurostagCouplingDevice, EurostagLine
from VeraGridEngine.IO.Eurostag.Devices.eurostag_base import read_text_with_fallback
from VeraGridEngine.IO.Eurostag.Devices.general_parameters import EurostagGeneralParameters
from VeraGridEngine.IO.Eurostag.Devices.generator import EurostagDynamicGenerator, EurostagGenerator
from VeraGridEngine.IO.Eurostag.Devices.load import EurostagCapacitorBank, EurostagLoad
from VeraGridEngine.IO.Eurostag.Devices.node import EurostagNode
from VeraGridEngine.IO.Eurostag.Devices.slack_bus import EurostagSlackBus
from VeraGridEngine.IO.Eurostag.Devices.transformer import EurostagType1Transformer, EurostagType8Transformer
from VeraGridEngine.basic_structures import Logger


class EurostagCircuit:
    def __init__(self):
        self.name = ""
        self.ech_file_name = ""
        self.dta_file_name = ""

        self.general_parameters: EurostagGeneralParameters | None = None
        self.nodes: list[EurostagNode] = []
        self.slack_buses: list[EurostagSlackBus] = []
        self.lines: list[EurostagLine] = []
        self.coupling_devices: list[EurostagCouplingDevice] = []
        self.loads: list[EurostagLoad] = []
        self.capacitor_banks: list[EurostagCapacitorBank] = []
        self.generators: list[EurostagGenerator] = []
        self.dynamic_generators: list[EurostagDynamicGenerator] = []
        self.type1_transformers: list[EurostagType1Transformer] = []
        self.type8_transformers: list[EurostagType8Transformer] = []

        self.Sbase = 100.0
        self.logger = Logger()

    @staticmethod
    def check_file_extension(f_name: str) -> bool:
        lower_name = f_name.lower()
        return lower_name.endswith(".ech") or lower_name.endswith(".dta")

    def read_files(self, ech_file: str | Path, dta_file: str | Path, logger: Logger | None = None) -> None:
        if logger is not None:
            self.logger = logger

        ech_path = Path(ech_file)
        dta_path = Path(dta_file)
        self.name = ech_path.stem
        self.ech_file_name = ech_path.name
        self.dta_file_name = dta_path.name

        self._parse_ech_file(ech_path)
        self._parse_dta_file(dta_path)
        self._apply_slack_bus_data()

        if self.general_parameters is not None and self.general_parameters.base_power > 0.0:
            self.Sbase = self.general_parameters.base_power

    def _parse_ech_file(self, file_path: Path) -> None:
        rows = read_text_with_fallback(file_path).splitlines()
        idx = 0

        while idx < len(rows):
            line = rows[idx]

            if line.startswith(EurostagType8Transformer.PREFIX):
                elm, idx = EurostagType8Transformer.from_lines(rows, idx)
                self.type8_transformers.append(elm)
                continue

            if line.startswith(EurostagType1Transformer.PREFIX):
                elm = EurostagType1Transformer()
                elm.parse_line(line)
                self.type1_transformers.append(elm)
            elif line.startswith(EurostagCouplingDevice.PREFIX):
                elm = EurostagCouplingDevice()
                elm.parse_line(line)
                self.coupling_devices.append(elm)
            elif line.startswith(EurostagLine.PREFIX):
                elm = EurostagLine()
                elm.parse_line(line)
                self.lines.append(elm)
            elif line.startswith(EurostagGenerator.PREFIX):
                elm = EurostagGenerator()
                elm.parse_line(line)
                self.generators.append(elm)
            elif line.startswith(EurostagLoad.PREFIX):
                elm = EurostagLoad()
                elm.parse_line(line)
                self.loads.append(elm)
            elif line.startswith(EurostagCapacitorBank.PREFIX):
                elm = EurostagCapacitorBank()
                elm.parse_line(line)
                self.capacitor_banks.append(elm)
            elif line.startswith(EurostagSlackBus.PREFIX):
                elm = EurostagSlackBus()
                elm.parse_line(line)
                self.slack_buses.append(elm)
            elif line.startswith(EurostagGeneralParameters.PREFIX):
                elm = EurostagGeneralParameters()
                elm.parse_line(line)
                self.general_parameters = elm
            elif line[:1] == EurostagNode.PREFIX:
                elm = EurostagNode()
                elm.parse_line(line)
                self.nodes.append(elm)

            idx += 1

    def _parse_dta_file(self, file_path: Path) -> None:
        rows = read_text_with_fallback(file_path).splitlines()
        idx = 0

        while idx < len(rows):
            line = rows[idx]
            if line.startswith(EurostagDynamicGenerator.PREFIX):
                elm, idx = EurostagDynamicGenerator.from_lines(rows, idx)
                if elm.name != "":
                    self.dynamic_generators.append(elm)
                continue
            idx += 1

    def _apply_slack_bus_data(self) -> None:
        nodes_by_name = {node.name: node for node in self.nodes}
        for slack in self.slack_buses:
            node = nodes_by_name.get(slack.name)
            if node is None:
                continue
            node.is_slack = True
            node.initial_angle = slack.phase_angle
