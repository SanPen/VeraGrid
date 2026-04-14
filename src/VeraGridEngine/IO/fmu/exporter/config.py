# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from enum import Enum
from pathlib import Path
import platform
import re
import uuid


class InterfaceType(str, Enum):
    """
    FMI interface types supported by the co-simulation exporter.
    """

    CO_SIMULATION = "co-simulation"


class IntegrationMethod(str, Enum):
    """
    Numerical integration schemes supported by the generated FMU runtime.
    """

    BACKWARD_EULER = "backward_euler"
    TRAPEZOIDAL = "trapezoidal"
    BDF2 = "bdf2"


class TargetPlatform(str, Enum):
    """
    FMI binary folders supported by the exporter.
    """

    WIN64 = "win64"
    LINUX64 = "linux64"
    DARWIN64 = "darwin64"


def detect_target_platform() -> TargetPlatform:
    """
    Detect the current host platform using the FMI binary-folder naming convention.

    :return: Host target platform.
    """

    system_name: str = platform.system().lower()
    if system_name == "windows":
        return TargetPlatform.WIN64
    else:
        if system_name == "darwin":
            return TargetPlatform.DARWIN64
        else:
            return TargetPlatform.LINUX64


def library_suffix(target_platform: TargetPlatform) -> str:
    """
    Return the shared-library suffix used by one FMI binary folder.

    :param target_platform: Target FMI binary platform.
    :return: Shared-library suffix.
    """

    if target_platform == TargetPlatform.WIN64:
        return ".dll"
    else:
        if target_platform == TargetPlatform.DARWIN64:
            return ".dylib"
        else:
            return ".so"


def sanitize_identifier(name: str) -> str:
    """
    Convert one user-facing model name into a valid C/FMI identifier.

    :param name: Requested model identifier or model name.
    :return: Sanitized identifier.
    """

    text: str = re.sub(r"[^0-9A-Za-z_]", "_", name)
    if len(text) == 0:
        text = "GeneratedModel"
    else:
        pass
    if text[0].isdigit():
        text = f"M_{text}"
    else:
        pass
    return text


def build_export_guid() -> str:
    """
    Create a fresh GUID for one exported FMU.

    :return: GUID string.
    """

    return str(uuid.uuid4())


class ExportConfig:
    """
    Lightweight export configuration for FMI 2.0 Co-Simulation packaging.

    The configuration is explicit on purpose because the FMU exporter needs stable
    values for naming, staging, numerical settings, and host-platform packaging.
    """

    __slots__ = (
        "model_name",
        "output_path",
        "guid",
        "interface_type",
        "target_platform",
        "integration_method",
        "fixed_step",
        "build_dir",
        "staging_dir",
        "model_identifier",
        "debug",
        "keep_build_dir",
        "include_snapshot_resource",
        "include_export_model_resource",
        "compile_binary",
        "max_newton_iterations",
        "newton_tolerance",
    )

    def __init__(self,
                 model_name: str,
                 output_path: Path | str,
                 guid: str | None = None,
                 interface_type: InterfaceType = InterfaceType.CO_SIMULATION,
                 target_platform: TargetPlatform | None = None,
                 integration_method: IntegrationMethod = IntegrationMethod.BACKWARD_EULER,
                 fixed_step: float = 1e-4,
                 build_dir: Path | str | None = None,
                 staging_dir: Path | str | None = None,
                 model_identifier: str | None = None,
                 debug: bool = False,
                 keep_build_dir: bool = False,
                 include_snapshot_resource: bool = True,
                 include_export_model_resource: bool = True,
                 compile_binary: bool = True,
                 max_newton_iterations: int = 10,
                 newton_tolerance: float = 1e-9) -> None:
        """
        Build one explicit FMU export configuration.

        :param model_name: User-visible FMU model name.
        :param output_path: Final `.fmu` output path.
        :param guid: Optional explicit FMU GUID.
        :param interface_type: FMI interface type.
        :param target_platform: Target FMI binary folder.
        :param integration_method: Generated runtime integration method.
        :param fixed_step: Default fixed communication step.
        :param build_dir: Optional persistent build directory.
        :param staging_dir: Optional staging directory used before packaging.
        :param model_identifier: Optional explicit FMI model identifier.
        :param debug: Whether to keep debug-friendly generation settings.
        :param keep_build_dir: Preserve the generated build directory.
        :param include_snapshot_resource: Include the serialized source snapshot.
        :param include_export_model_resource: Include the export IR resource.
        :param compile_binary: Compile the FMU binary.
        :param max_newton_iterations: Maximum nonlinear iterations in the runtime solver.
        :param newton_tolerance: Nonlinear solver tolerance.
        :return: None.
        """

        self.model_name: str = model_name
        self.output_path: Path = Path(output_path)
        if guid is None:
            self.guid: str = build_export_guid()
        else:
            self.guid = guid
        self.interface_type: InterfaceType = interface_type
        if target_platform is None:
            self.target_platform: TargetPlatform = detect_target_platform()
        else:
            self.target_platform = target_platform
        self.integration_method: IntegrationMethod = integration_method
        self.fixed_step: float = fixed_step
        if build_dir is None:
            self.build_dir: Path | None = None
        else:
            self.build_dir = Path(build_dir)
        if staging_dir is None:
            self.staging_dir: Path | None = None
        else:
            self.staging_dir = Path(staging_dir)
        self.model_identifier: str = sanitize_identifier(model_identifier or model_name)
        self.debug: bool = debug
        self.keep_build_dir: bool = keep_build_dir
        self.include_snapshot_resource: bool = include_snapshot_resource
        self.include_export_model_resource: bool = include_export_model_resource
        self.compile_binary: bool = compile_binary
        self.max_newton_iterations: int = max_newton_iterations
        self.newton_tolerance: float = newton_tolerance
        self._validate()

    def _validate(self) -> None:
        """
        Validate the numerical and filesystem settings for one export configuration.

        :return: None.
        """

        if self.fixed_step <= 0.0:
            raise ValueError("fixed_step must be positive")
        else:
            pass
        if self.max_newton_iterations <= 0:
            raise ValueError("max_newton_iterations must be positive")
        else:
            pass
        if self.newton_tolerance <= 0.0:
            raise ValueError("newton_tolerance must be positive")
        else:
            pass

    @property
    def output_dir(self) -> Path:
        """
        Return the directory that will contain the final `.fmu` file.

        :return: Output directory.
        """

        return self.output_path.parent

    @property
    def library_name(self) -> str:
        """
        Return the platform-specific shared-library file name.

        :return: Shared-library file name.
        """

        return f"{self.model_identifier}{library_suffix(self.target_platform)}"
