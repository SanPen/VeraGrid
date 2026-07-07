# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Public entry points for the experimental FMU import package.

This module uses lazy imports so the package can be imported from VeraGrid core
without triggering circular imports during solver/module bootstrap.
"""

from __future__ import annotations

import importlib
from typing import Any


_SYMBOL_TO_MODULE: dict[str, str] = {
    "FmuArchiveError": "VeraGridEngine.IO.fmu.importer.errors",
    "FmuBindingError": "VeraGridEngine.IO.fmu.importer.errors",
    "FmuDependencyError": "VeraGridEngine.IO.fmu.importer.errors",
    "FmuImportError": "VeraGridEngine.IO.fmu.importer.errors",
    "FmuModeError": "VeraGridEngine.IO.fmu.importer.errors",
    "FmuBindingDirection": "VeraGridEngine.IO.fmu.importer.bindings",
    "FmuImportConfig": "VeraGridEngine.IO.fmu.importer.bindings",
    "FmuVariableBinding": "VeraGridEngine.IO.fmu.importer.bindings",
    "validate_bindings": "VeraGridEngine.IO.fmu.importer.bindings",
    "FmuInterfaceMode": "VeraGridEngine.IO.fmu.importer.model_description",
    "FmuModelDescription": "VeraGridEngine.IO.fmu.importer.model_description",
    "FmuVariableDescription": "VeraGridEngine.IO.fmu.importer.model_description",
    "FmuVariableType": "VeraGridEngine.IO.fmu.importer.model_description",
    "choose_fmu_mode": "VeraGridEngine.IO.fmu.importer.model_description",
    "list_fmu_variable_names": "VeraGridEngine.IO.fmu.importer.model_description",
    "read_fmu_model_description": "VeraGridEngine.IO.fmu.importer.model_description",
    "FmuRuntimeHost": "VeraGridEngine.IO.fmu.importer.runtime_host",
    "open_fmu_runtime_host": "VeraGridEngine.IO.fmu.importer.runtime_host",
    "FmuCsDeviceConfigRecord": "VeraGridEngine.IO.fmu.importer.device_config",
    "FmuMeDeviceConfigRecord": "VeraGridEngine.IO.fmu.importer.device_config",
    "dump_fmu_cs_device_config": "VeraGridEngine.IO.fmu.importer.device_config",
    "dump_fmu_me_device_config": "VeraGridEngine.IO.fmu.importer.device_config",
    "load_fmu_cs_device_config": "VeraGridEngine.IO.fmu.importer.device_config",
    "load_fmu_me_device_config": "VeraGridEngine.IO.fmu.importer.device_config",
    "FmuCsDeviceAdapter": "VeraGridEngine.IO.fmu.importer.experimental_cs",
    "FmuCsDeviceSpec": "VeraGridEngine.IO.fmu.importer.experimental_cs",
    "FmuCsDomain": "VeraGridEngine.IO.fmu.importer.experimental_cs",
    "FmuRefBinding": "VeraGridEngine.IO.fmu.importer.experimental_cs",
    "build_emt_fmu_cs_injection_template": "VeraGridEngine.IO.fmu.importer.experimental_cs",
    "build_rms_fmu_cs_injection_template": "VeraGridEngine.IO.fmu.importer.experimental_cs",
    "advance_rms_fmu_cs_devices": "VeraGridEngine.IO.fmu.importer.experimental_cs",
    "close_rms_fmu_cs_devices": "VeraGridEngine.IO.fmu.importer.experimental_cs",
    "finalize_emt_fmu_cs_devices": "VeraGridEngine.IO.fmu.importer.experimental_cs",
    "initialize_rms_fmu_cs_devices": "VeraGridEngine.IO.fmu.importer.experimental_cs",
    "queue_emt_fmu_cs_device": "VeraGridEngine.IO.fmu.importer.experimental_cs",
    "register_emt_fmu_cs_device": "VeraGridEngine.IO.fmu.importer.experimental_cs",
    "register_rms_fmu_cs_device": "VeraGridEngine.IO.fmu.importer.experimental_cs",
    "FmuMeDeviceAdapter": "VeraGridEngine.IO.fmu.importer.experimental_me",
    "FmuMeDeviceSpec": "VeraGridEngine.IO.fmu.importer.experimental_me",
    "FmuMeDomain": "VeraGridEngine.IO.fmu.importer.experimental_me",
    "FmuMeIntegrationMethod": "VeraGridEngine.IO.fmu.importer.experimental_me",
    "build_fmu_me_device_spec": "VeraGridEngine.IO.fmu.importer.experimental_me",
    "build_emt_fmu_me_injection_template": "VeraGridEngine.IO.fmu.importer.experimental_me",
    "build_rms_fmu_me_injection_template": "VeraGridEngine.IO.fmu.importer.experimental_me",
    "advance_rms_fmu_me_devices": "VeraGridEngine.IO.fmu.importer.experimental_me",
    "close_rms_fmu_me_devices": "VeraGridEngine.IO.fmu.importer.experimental_me",
    "finalize_emt_fmu_me_devices": "VeraGridEngine.IO.fmu.importer.experimental_me",
    "initialize_rms_fmu_me_devices": "VeraGridEngine.IO.fmu.importer.experimental_me",
    "queue_emt_fmu_me_device": "VeraGridEngine.IO.fmu.importer.experimental_me",
    "register_emt_fmu_me_device": "VeraGridEngine.IO.fmu.importer.experimental_me",
    "register_rms_fmu_me_device": "VeraGridEngine.IO.fmu.importer.experimental_me",
    "CompositeEmtBoundaryUpdater": "VeraGridEngine.IO.fmu.importer.emt_boundary",
    "build_emt_boundary_updater": "VeraGridEngine.IO.fmu.importer.emt_boundary",
    "attach_emt_fmu_cs_device": "VeraGridEngine.IO.fmu.importer.device_api",
    "attach_emt_fmu_me_device": "VeraGridEngine.IO.fmu.importer.device_api",
    "attach_rms_fmu_cs_device": "VeraGridEngine.IO.fmu.importer.device_api",
    "attach_rms_fmu_me_device": "VeraGridEngine.IO.fmu.importer.device_api",
    "configure_fmu_template": "VeraGridEngine.IO.fmu.importer.template_api",
    "FmuDeviceAttachmentRequest": "VeraGridEngine.IO.fmu.importer.user_api",
    "FmuDeviceDomain": "VeraGridEngine.IO.fmu.importer.user_api",
    "FmuReferenceValue": "VeraGridEngine.IO.fmu.importer.user_api",
    "attach_fmu_to_device": "VeraGridEngine.IO.fmu.importer.user_api",
}

__all__ = list(_SYMBOL_TO_MODULE.keys())


def __getattr__(name: str) -> Any:
    """Resolve public symbols lazily to avoid circular imports.

    :param name: Public symbol requested from the package.
    :return: Resolved public object.
    """

    module_name: str | None = _SYMBOL_TO_MODULE.get(name, None)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    else:
        module = importlib.import_module(module_name)
        value: Any = getattr(module, name)
        globals()[name] = value
        return value


def __dir__() -> list[str]:
    """Return the public directory of the package.

    :return: Sorted public names.
    """

    return sorted(__all__)
