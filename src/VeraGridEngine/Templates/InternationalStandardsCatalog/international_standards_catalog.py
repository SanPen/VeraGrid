# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Typed catalog of international-standard RMS dynamic models."""

from __future__ import annotations

from typing import Sequence

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.enumerations import DeviceType, InternationalStandardModel
from VeraGridEngine.Templates.Rms.international_standards import build_international_standard_template


class InternationalStandardTemplateDescriptor:
    """Describe one draggable international-standard RMS model."""

    __slots__ = ("_model", "_display_label", "_category_path", "_module_folder", "_device_type")

    def __init__(
            self,
            model: InternationalStandardModel,
            display_label: str,
            category_path: Sequence[str],
            module_folder: str,
            device_type: DeviceType | None = None,
    ) -> None:
        """Store the stable catalog metadata for one RMS model.

        :param model: Enumerated model used for type-explicit materialization.
        :param display_label: Human-facing Dynamic Editor label.
        :param category_path: Nested branch below International standards.
        :param module_folder: Physical subpackage containing the model module.
        :param device_type: MultiCircuit device type represented by a complete
            device model, or ``None`` when the template is a control component.
        :return: None.
        """
        self._model: InternationalStandardModel = model
        self._display_label: str = display_label
        self._category_path: tuple[str, ...] = tuple(category_path)
        self._module_folder: str = module_folder
        self._device_type: DeviceType | None = device_type

    @property
    def model(self) -> InternationalStandardModel:
        """Return the international-standard model identifier.

        :return: Enumerated model identifier.
        """
        return self._model

    @property
    def display_label(self) -> str:
        """Return the label displayed in the Dynamic Editor library.

        :return: Human-facing model label.
        """
        return self._display_label

    @property
    def category_path(self) -> Sequence[str]:
        """Return the ordered Dynamic Editor category path.

        :return: Immutable category sequence.
        """
        return self._category_path

    @property
    def module_folder(self) -> str:
        """Return the physical model-family package name.

        :return: Subpackage below international_standards.
        """
        return self._module_folder

    @property
    def device_type(self) -> DeviceType | None:
        """Return the MultiCircuit device type represented by the template.

        Control and protection templates return ``None`` because they are
        building blocks inside a device model rather than device templates.

        :return: Associated device type, or ``None`` for non-device models.
        """
        return self._device_type

    @property
    def template_key(self) -> str:
        """Return the stable serialization-independent catalog key.

        :return: Standard model code used by the existing model enum.
        """
        return self._model.value

    @property
    def search_text(self) -> str:
        """Return searchable model, family, and module terms.

        :return: Space-separated case-insensitive search text.
        """
        category_text: str = " ".join(self._category_path)
        return f"{self._display_label} {self._model.name} {self._model.value} {category_text}".strip()

    @property
    def module_relative_path(self) -> str:
        """Return the model path relative to international_standards.

        :return: Slash-separated Python source path.
        """
        return f"{self._module_folder}/{self._model.value}.py"


def get_international_standard_template_descriptors() -> Sequence[InternationalStandardTemplateDescriptor]:
    """Return every supported international-standard RMS model in family order.

    The ordered registry is authoritative for the Dynamic Editor tree and
    mirrors the physical subpackage organization of the model files.

    :return: Immutable ordered descriptor sequence.
    """
    descriptors: list[InternationalStandardTemplateDescriptor] = list()

    # Synchronous machines are kept together in both the filesystem and the editor tree.
    descriptors.extend(list((
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.GENSAL,
            display_label="GENSAL",
            category_path=("Synchronous machines",),
            module_folder="synchronous_machines",
            device_type=DeviceType.GeneratorDevice,
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.GENROU,
            display_label="GENROU",
            category_path=("Synchronous machines",),
            module_folder="synchronous_machines",
            device_type=DeviceType.GeneratorDevice,
        ),
    )))

    # Induction machines are kept together in both the filesystem and the editor tree.
    descriptors.extend(list((
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.CIMTR1,
            display_label="CIMTR1",
            category_path=("Induction machines",),
            module_folder="induction_machines",
            device_type=DeviceType.GeneratorDevice,
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.CIMW,
            display_label="CIMW",
            category_path=("Induction machines",),
            module_folder="induction_machines",
            device_type=DeviceType.LoadDevice,
        ),
    )))

    # Governors are kept together in both the filesystem and the editor tree.
    descriptors.extend(list((
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.GGOV1,
            display_label="GGOV1",
            category_path=("Governors",),
            module_folder="governors",
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.GOVHYDRO4,
            display_label="GOVHYDRO4",
            category_path=("Governors",),
            module_folder="governors",
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.GOVSTEAM1,
            display_label="GOVSTEAM1",
            category_path=("Governors",),
            module_folder="governors",
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.GOVSTEAMEU,
            display_label="GOVSTEAMEU",
            category_path=("Governors",),
            module_folder="governors",
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.HYGOV,
            display_label="HYGOV",
            category_path=("Governors",),
            module_folder="governors",
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.IEEEG1,
            display_label="IEEEG1",
            category_path=("Governors",),
            module_folder="governors",
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.IEEEG2,
            display_label="IEEEG2",
            category_path=("Governors",),
            module_folder="governors",
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.TGOV1,
            display_label="TGOV1",
            category_path=("Governors",),
            module_folder="governors",
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.TGOV3,
            display_label="TGOV3",
            category_path=("Governors",),
            module_folder="governors",
        ),
    )))

    # Excitation systems are kept together in both the filesystem and the editor tree.
    descriptors.extend(list((
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.AC1A,
            display_label="AC1A",
            category_path=("Excitation systems",),
            module_folder="excitation_systems",
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.AC1C,
            display_label="AC1C",
            category_path=("Excitation systems",),
            module_folder="excitation_systems",
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.AC6A,
            display_label="AC6A",
            category_path=("Excitation systems",),
            module_folder="excitation_systems",
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.AC6C,
            display_label="AC6C",
            category_path=("Excitation systems",),
            module_folder="excitation_systems",
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.AC7B,
            display_label="AC7B",
            category_path=("Excitation systems",),
            module_folder="excitation_systems",
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.AC7C,
            display_label="AC7C",
            category_path=("Excitation systems",),
            module_folder="excitation_systems",
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.AC8B,
            display_label="AC8B",
            category_path=("Excitation systems",),
            module_folder="excitation_systems",
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.AC8C,
            display_label="AC8C",
            category_path=("Excitation systems",),
            module_folder="excitation_systems",
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.BBSEX1,
            display_label="BBSEX1",
            category_path=("Excitation systems",),
            module_folder="excitation_systems",
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.DC1A,
            display_label="DC1A",
            category_path=("Excitation systems",),
            module_folder="excitation_systems",
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.DC1C,
            display_label="DC1C",
            category_path=("Excitation systems",),
            module_folder="excitation_systems",
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.ESDC2A,
            display_label="ESDC2A",
            category_path=("Excitation systems",),
            module_folder="excitation_systems",
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.EXAC1,
            display_label="EXAC1",
            category_path=("Excitation systems",),
            module_folder="excitation_systems",
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.IEEET1,
            display_label="IEEET1",
            category_path=("Excitation systems",),
            module_folder="excitation_systems",
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.IEEEX2,
            display_label="IEEEX2",
            category_path=("Excitation systems",),
            module_folder="excitation_systems",
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.IEEX2A,
            display_label="IEEX2A",
            category_path=("Excitation systems",),
            module_folder="excitation_systems",
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.SCRX,
            display_label="SCRX",
            category_path=("Excitation systems",),
            module_folder="excitation_systems",
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.SEXS,
            display_label="SEXS",
            category_path=("Excitation systems",),
            module_folder="excitation_systems",
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.ST1A,
            display_label="ST1A",
            category_path=("Excitation systems",),
            module_folder="excitation_systems",
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.ST1C,
            display_label="ST1C",
            category_path=("Excitation systems",),
            module_folder="excitation_systems",
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.ST4B,
            display_label="ST4B",
            category_path=("Excitation systems",),
            module_folder="excitation_systems",
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.ST4C,
            display_label="ST4C",
            category_path=("Excitation systems",),
            module_folder="excitation_systems",
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.ST5B,
            display_label="ST5B",
            category_path=("Excitation systems",),
            module_folder="excitation_systems",
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.ST5C,
            display_label="ST5C",
            category_path=("Excitation systems",),
            module_folder="excitation_systems",
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.ST6B,
            display_label="ST6B",
            category_path=("Excitation systems",),
            module_folder="excitation_systems",
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.ST6C,
            display_label="ST6C",
            category_path=("Excitation systems",),
            module_folder="excitation_systems",
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.ST7B,
            display_label="ST7B",
            category_path=("Excitation systems",),
            module_folder="excitation_systems",
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.ST7C,
            display_label="ST7C",
            category_path=("Excitation systems",),
            module_folder="excitation_systems",
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.ST9C,
            display_label="ST9C",
            category_path=("Excitation systems",),
            module_folder="excitation_systems",
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.VRKUNDUR,
            display_label="VRKUNDUR",
            category_path=("Excitation systems",),
            module_folder="excitation_systems",
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.IEEEVC_1981,
            display_label="IEEEVC 1981",
            category_path=("Excitation systems",),
            module_folder="excitation_systems",
        ),
    )))

    # Excitation limiters are kept together in both the filesystem and the editor tree.
    descriptors.extend(list((
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.IEEL,
            display_label="IEEL",
            category_path=("Excitation limiters",),
            module_folder="excitation_limiters",
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.MAXEX2,
            display_label="MAXEX2",
            category_path=("Excitation limiters",),
            module_folder="excitation_limiters",
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.OEL2C,
            display_label="OEL2C",
            category_path=("Excitation limiters",),
            module_folder="excitation_limiters",
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.OEL3C,
            display_label="OEL3C",
            category_path=("Excitation limiters",),
            module_folder="excitation_limiters",
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.OEL4C,
            display_label="OEL4C",
            category_path=("Excitation limiters",),
            module_folder="excitation_limiters",
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.OEL5C,
            display_label="OEL5C",
            category_path=("Excitation limiters",),
            module_folder="excitation_limiters",
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.SCL1C,
            display_label="SCL1C",
            category_path=("Excitation limiters",),
            module_folder="excitation_limiters",
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.SCL2C,
            display_label="SCL2C",
            category_path=("Excitation limiters",),
            module_folder="excitation_limiters",
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.UEL1,
            display_label="UEL1",
            category_path=("Excitation limiters",),
            module_folder="excitation_limiters",
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.UEL2C,
            display_label="UEL2C",
            category_path=("Excitation limiters",),
            module_folder="excitation_limiters",
        ),
    )))

    # Power system stabilizers are kept together in both the filesystem and the editor tree.
    descriptors.extend(list((
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.PSS1AOMEGA,
            display_label="PSS1A (omega input)",
            category_path=("Power system stabilizers",),
            module_folder="power_system_stabilizers",
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.PSS1APGEN,
            display_label="PSS1A (Pgen input)",
            category_path=("Power system stabilizers",),
            module_folder="power_system_stabilizers",
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.PSS2A,
            display_label="PSS2A",
            category_path=("Power system stabilizers",),
            module_folder="power_system_stabilizers",
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.PSS2B,
            display_label="PSS2B",
            category_path=("Power system stabilizers",),
            module_folder="power_system_stabilizers",
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.PSS2C,
            display_label="PSS2C",
            category_path=("Power system stabilizers",),
            module_folder="power_system_stabilizers",
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.PSS3B,
            display_label="PSS3B",
            category_path=("Power system stabilizers",),
            module_folder="power_system_stabilizers",
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.PSS3C,
            display_label="PSS3C",
            category_path=("Power system stabilizers",),
            module_folder="power_system_stabilizers",
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.PSS6C,
            display_label="PSS6C",
            category_path=("Power system stabilizers",),
            module_folder="power_system_stabilizers",
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.PSSKUNDUR,
            display_label="PSS Kundur",
            category_path=("Power system stabilizers",),
            module_folder="power_system_stabilizers",
        ),
    )))

    # Renewable controls are kept together in both the filesystem and the editor tree.
    descriptors.extend(list((
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.REECB,
            display_label="REECB",
            category_path=("Renewable controls",),
            module_folder="renewable_controls",
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.REECC,
            display_label="REECC",
            category_path=("Renewable controls",),
            module_folder="renewable_controls",
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.REGCBCS,
            display_label="REGCbCS",
            category_path=("Renewable controls",),
            module_folder="renewable_controls",
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.REPCA,
            display_label="REPCA",
            category_path=("Renewable controls",),
            module_folder="renewable_controls",
        ),
    )))

    # Wind generation are kept together in both the filesystem and the editor tree.
    descriptors.extend(list((
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.WT4ACURRENTSOURCE,
            display_label="WT4A current source",
            category_path=("Wind generation",),
            module_folder="wind_generation",
            device_type=DeviceType.GeneratorDevice,
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.WT4ACURRENTSOURCE2020,
            display_label="WT4A current source 2020",
            category_path=("Wind generation",),
            module_folder="wind_generation",
            device_type=DeviceType.GeneratorDevice,
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.WT4BCURRENTSOURCE,
            display_label="WT4B current source",
            category_path=("Wind generation",),
            module_folder="wind_generation",
            device_type=DeviceType.GeneratorDevice,
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.WT4BCURRENTSOURCE2020,
            display_label="WT4B current source 2020",
            category_path=("Wind generation",),
            module_folder="wind_generation",
            device_type=DeviceType.GeneratorDevice,
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.WT4INJECTOR,
            display_label="WT4 injector",
            category_path=("Wind generation",),
            module_folder="wind_generation",
            device_type=DeviceType.GeneratorDevice,
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.WTG4ACURRENTSOURCE,
            display_label="WTG4A current source",
            category_path=("Wind generation",),
            module_folder="wind_generation",
            device_type=DeviceType.GeneratorDevice,
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.WTG4BCURRENTSOURCE,
            display_label="WTG4B current source",
            category_path=("Wind generation",),
            module_folder="wind_generation",
            device_type=DeviceType.GeneratorDevice,
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.WPP4BCURRENTSOURCE2020,
            display_label="WPP4B current source 2020",
            category_path=("Wind generation",),
            module_folder="wind_generation",
            device_type=DeviceType.GeneratorDevice,
        ),
    )))

    # Solar PV generation are kept together in both the filesystem and the editor tree.
    descriptors.extend(list((
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.PVCURRENTSOURCEBNOPLANTCONTROL,
            display_label="PV current source B (no plant control)",
            category_path=("Solar PV generation",),
            module_folder="solar_pv_generation",
            device_type=DeviceType.GeneratorDevice,
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.PVVOLTAGESOURCEANOPLANTCONTROL,
            display_label="PV voltage source A (no plant control)",
            category_path=("Solar PV generation",),
            module_folder="solar_pv_generation",
            device_type=DeviceType.GeneratorDevice,
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.PVVOLTAGESOURCEBNOPLANTCONTROL,
            display_label="PV voltage source B (no plant control)",
            category_path=("Solar PV generation",),
            module_folder="solar_pv_generation",
            device_type=DeviceType.GeneratorDevice,
        ),
    )))

    # Battery energy storage are kept together in both the filesystem and the editor tree.
    descriptors.extend(list((
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.BESSCBCURRENTSOURCENOPLANTCONTROL,
            display_label="BESSCB current source (no plant control)",
            category_path=("Battery energy storage",),
            module_folder="battery_energy_storage",
            device_type=DeviceType.BatteryDevice,
        ),
    )))

    # Protection relays are kept together in both the filesystem and the editor tree.
    descriptors.extend(list((
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.FRQTPA,
            display_label="FRQTPA",
            category_path=("Protection relays",),
            module_folder="protection_relays",
        ),
        InternationalStandardTemplateDescriptor(
            model=InternationalStandardModel.VTGTPA,
            display_label="VTGTPA",
            category_path=("Protection relays",),
            module_folder="protection_relays",
        ),
    )))

    return tuple(descriptors)


def get_international_standard_device_template_descriptors() -> Sequence[InternationalStandardTemplateDescriptor]:
    """Return standards that model a complete MultiCircuit device.

    Controls, limiters, stabilizers, and protection components remain in the
    Dynamic Editor catalog but are excluded from the reusable device catalog.

    :return: Immutable ordered sequence of device-compatible descriptors.
    """
    device_descriptors: list[InternationalStandardTemplateDescriptor] = list()
    descriptor: InternationalStandardTemplateDescriptor
    for descriptor in get_international_standard_template_descriptors():
        if descriptor.device_type is None:
            pass
        else:
            device_descriptors.append(descriptor)
    return tuple(device_descriptors)


def load_international_standard_template(
        descriptor: InternationalStandardTemplateDescriptor,
        var_factory: VarFactory,
        name: str | None = None,
) -> RmsModelTemplate:
    """Materialize a fresh RMS model represented by one catalog descriptor.

    :param descriptor: Typed model and catalog metadata.
    :param var_factory: Factory allocating fresh symbolic identities.
    :param name: Optional explicit runtime instance name.
    :return: Materialized international-standard RMS template.
    """
    return build_international_standard_template(
        model=descriptor.model,
        vf=var_factory,
        name=name,
    )
