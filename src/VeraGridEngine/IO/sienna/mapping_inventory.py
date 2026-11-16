# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Explicit Sienna v0.4 static-adapter mapping decisions."""

from __future__ import annotations

from enum import Enum

from VeraGridEngine.IO.sienna.devices.schema_object import SiennaObjectKind
from VeraGridEngine.IO.sienna.devices.schema_registry import get_sienna_object_parsers


class SiennaMappingStatus(Enum):
    """Describe the static VeraGrid conversion outcome for one schema kind."""

    CONVERTED = "converted"
    NESTED_VALUE = "nested_value"
    NO_STATIC_EQUIVALENT = "no_static_equivalent"
    DYNAMIC_DEFERRED = "dynamic_deferred"


class SiennaMappingDecision:
    """Store one audit decision without using a dynamic mapping payload."""

    __slots__ = ("kind", "source_module", "target", "status", "reason")

    def __init__(self, kind: SiennaObjectKind, source_module: str, target: str,
                 status: SiennaMappingStatus, reason: str) -> None:
        """Store the schema source and the verified adapter outcome.

        :param kind: Registered Sienna schema kind.
        :param source_module: Fixed-slot parser module for the kind.
        :param target: VeraGrid target or the deliberately absent domain.
        :param status: Static-adapter outcome.
        :param reason: Auditable explanation of the outcome.
        :return: None.
        """
        self.kind: SiennaObjectKind = kind
        self.source_module: str = source_module
        self.target: str = target
        self.status: SiennaMappingStatus = status
        self.reason: str = reason


def _get_converted_targets() -> dict[SiennaObjectKind, str]:
    """Return the non-dynamic kinds with a static circuit conversion.

    :return: Direct Sienna-kind to VeraGrid-device targets.
    """
    return dict({
        SiennaObjectKind.ACBus: "Bus", SiennaObjectKind.Arc: "branch endpoints",
        SiennaObjectKind.Area: "Area", SiennaObjectKind.DCBus: "Bus",
        SiennaObjectKind.DiscreteControlledACBranch: "Line",
        SiennaObjectKind.EnergyReservoirStorage: "Battery", SiennaObjectKind.ExponentialLoad: "Load",
        SiennaObjectKind.FACTSControlDevice: "ControllableShunt", SiennaObjectKind.FixedAdmittance: "Shunt",
        SiennaObjectKind.GenericArcImpedance: "Line", SiennaObjectKind.HybridSystem: "Generator",
        SiennaObjectKind.HydroDispatch: "Generator", SiennaObjectKind.HydroPumpTurbine: "Battery",
        SiennaObjectKind.HydroTurbine: "Generator", SiennaObjectKind.InterruptiblePowerLoad: "Load",
        SiennaObjectKind.InterruptibleStandardLoad: "Load", SiennaObjectKind.Line: "Line",
        SiennaObjectKind.LoadZone: "Zone", SiennaObjectKind.MotorLoad: "Load",
        SiennaObjectKind.PowerLoad: "Load", SiennaObjectKind.RenewableDispatch: "Generator",
        SiennaObjectKind.RenewableNonDispatch: "StaticGenerator", SiennaObjectKind.SeriesCompensator: "SeriesReactance",
        SiennaObjectKind.ShiftablePowerLoad: "Load", SiennaObjectKind.Source: "ExternalGrid",
        SiennaObjectKind.StandardLoad: "Load", SiennaObjectKind.SwitchedAdmittance: "ControllableShunt",
        SiennaObjectKind.SynchronousCondenser: "Generator", SiennaObjectKind.ThermalStandard: "Generator",
        SiennaObjectKind.ThreeWindingTransformer: "Transformer3W",
        SiennaObjectKind.TransformerCircuit: "Transformer2W/Transformer3W",
        SiennaObjectKind.TwoWindingTransformer: "Transformer2W",
    })


def get_sienna_mapping_inventory() -> tuple[SiennaMappingDecision, ...]:
    """Return one explicit decision for every registered Sienna v0.4 kind.

    Dynamic kinds are deliberately marked deferred.  Every remaining kind is
    either converted, used only by a parent schema record, or rejected because
    the static VeraGrid circuit has no ownership-preserving equivalent.

    :return: Immutable ordered decisions in ``SiennaObjectKind`` order.
    """
    parsers: dict[SiennaObjectKind, object] = get_sienna_object_parsers()
    decisions: list[SiennaMappingDecision] = list()
    for kind in SiennaObjectKind:
        parser: object | None = parsers.get(kind, None)
        if parser is None:
            raise ValueError(f"No parser is registered for {kind.name}")
        else:
            source_module: str = parser.__module__
            decisions.append(_make_mapping_decision(kind=kind, source_module=source_module))
    return tuple(decisions)


def _make_mapping_decision(kind: SiennaObjectKind, source_module: str) -> SiennaMappingDecision:
    """Classify one registered kind against the static circuit model.

    :param kind: Registered Sienna schema kind.
    :param source_module: Parser module, used to isolate the dynamic domain.
    :return: Concrete audit decision.
    """
    converted_targets: dict[SiennaObjectKind, str] = _get_converted_targets()
    converted_target: str | None = converted_targets.get(kind, None)
    if ".dynamics." in source_module:
        return SiennaMappingDecision(kind=kind, source_module=source_module, target="dynamics adapter",
                                     status=SiennaMappingStatus.DYNAMIC_DEFERRED,
                                     reason="Deferred by the static-adapter scope.")
    elif converted_target is not None:
        return SiennaMappingDecision(kind=kind, source_module=source_module, target=converted_target,
                                     status=SiennaMappingStatus.CONVERTED,
                                     reason="Converted by sienna_to_veragrid and emitted canonically when exportable.")
    elif ".common." in source_module:
        return SiennaMappingDecision(kind=kind, source_module=source_module, target="parent Sienna record",
                                     status=SiennaMappingStatus.NESTED_VALUE,
                                     reason="Value object has no independent VeraGrid device ownership.")
    else:
        return SiennaMappingDecision(kind=kind, source_module=source_module, target="static circuit catalog",
                                     status=SiennaMappingStatus.NO_STATIC_EQUIVALENT,
                                     reason="No ownership-preserving static VeraGrid circuit target; conversion rejects it explicitly.")


def get_non_dynamic_mapping_decisions() -> tuple[SiennaMappingDecision, ...]:
    """Return the static-adapter decisions requested for the current scope.

    :return: Decisions excluding dynamic schema kinds.
    """
    decisions: tuple[SiennaMappingDecision, ...] = get_sienna_mapping_inventory()
    return tuple(decision for decision in decisions
                 if decision.status is not SiennaMappingStatus.DYNAMIC_DEFERRED)
