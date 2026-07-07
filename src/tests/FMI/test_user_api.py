from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from VeraGridEngine.IO.fmu.exporter.api import export_fmu
from VeraGridEngine.IO.fmu.exporter.build import host_build_capable
from VeraGridEngine.IO.fmu.exporter.config import ExportConfig as CsExportConfig, detect_target_platform as detect_cs_target_platform
from VeraGridEngine.IO.fmu.exporter.compat import Block, Const, Var
from VeraGridEngine.IO.fmu.importer import (
    FmuDeviceAttachmentRequest,
    FmuDeviceDomain,
    FmuImportConfig,
    FmuInterfaceMode,
    FmuMeIntegrationMethod,
    FmuReferenceValue,
    FmuRefBinding,
)
from VeraGridEngine.IO.fmu.importer.user_api import attach_fmu_to_device
from VeraGridEngine.IO.fmu.exporter_me.api import export_fmu_me
from VeraGridEngine.IO.fmu.exporter_me.config import ExportConfig as MeExportConfig, detect_target_platform as detect_me_target_platform
from VeraGridEngine.enumerations import DeviceType, VarPowerFlowRefferenceType
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory


class FakeGrid:
    __slots__ = ("var_factory")

    def __init__(self) -> None:


        self.var_factory = VarFactory(name="UserApiVarFactory")


def _tmp_root() -> Path:
    root = Path(__file__).resolve().parent / ".tmp"
    root.mkdir(parents=True, exist_ok=True)
    return root.resolve()


def build_cs_output_block() -> Block:
    x = Var("x")
    dx = Var("dx", base_var=x)
    y = Var("y")
    return Block(
        state_vars=[x],
        state_eqs=[Const(1.0)],
        algebraic_vars=[y],
        algebraic_eqs=[y - x],
        diff_vars=[dx],
        init_values={x: Const(0.0), y: Const(0.0)},
        init_eqs={y: Const(0.0)},
        out_vars=[y],
    )


def build_me_output_block() -> Block:
    x = Var("x")
    dx = Var("dx", base_var=x)
    y = Var("y")
    u = Var("u")
    return Block(
        state_vars=[x],
        state_eqs=[Const(1.0) + u],
        algebraic_vars=[y],
        algebraic_eqs=[y - x],
        diff_vars=[dx],
        init_values={x: Const(0.0), y: Const(0.0)},
        init_eqs={y: Const(0.0)},
        in_vars=[u],
        out_vars=[y],
    )


@pytest.mark.skipif(not host_build_capable(), reason="No usable host build toolchain available")
def test_user_api_attaches_rms_cs_device() -> None:
    pytest.importorskip("fmpy")

    output_root = _tmp_root()
    fmu_path = output_root / "user_api_rms_cs.fmu"
    try:
        exported_fmu = export_fmu(
            build_cs_output_block(),
            CsExportConfig(
                model_name="UserApiRmsCs",
                output_path=fmu_path,
                target_platform=detect_cs_target_platform(),
                compile_binary=True,
                keep_build_dir=False,
            ),
        )

        device = SimpleNamespace(name="LoadA", device_type=DeviceType.LoadDevice, rms_model=Block(), rms_fmu_import_config="")
        grid = FakeGrid()
        request = FmuDeviceAttachmentRequest(
            fmu_path=exported_fmu,
            domain=FmuDeviceDomain.RMS,
            mode=FmuInterfaceMode.CO_SIMULATION,
            input_bindings=tuple(),
            output_bindings=(FmuRefBinding(reference=VarPowerFlowRefferenceType.P, fmu_variable_name="y"),),
            output_defaults=(FmuReferenceValue(reference=VarPowerFlowRefferenceType.P, value=0.0),),
        )
        attach_fmu_to_device(device, grid, request)

        assert device.rms_fmu_import_config != ""
    finally:
        fmu_path.unlink(missing_ok=True)


@pytest.mark.skipif(not host_build_capable(), reason="No usable host build toolchain available")
def test_user_api_attaches_emt_me_device() -> None:
    pytest.importorskip("fmpy")

    output_root = _tmp_root()
    fmu_path = output_root / "user_api_emt_me.fmu"
    try:
        exported_fmu = export_fmu_me(
            build_me_output_block(),
            MeExportConfig(
                model_name="UserApiEmtMe",
                output_path=fmu_path,
                target_platform=detect_me_target_platform(),
                compile_binary=True,
                keep_build_dir=False,
            ),
        )

        device = SimpleNamespace(name="LoadB", device_type=DeviceType.LoadDevice, emt_model=Block(), emt_fmu_me_import_config="")
        grid = FakeGrid()
        request = FmuDeviceAttachmentRequest(
            fmu_path=exported_fmu,
            domain=FmuDeviceDomain.EMT,
            mode=FmuInterfaceMode.MODEL_EXCHANGE,
            input_bindings=tuple(),
            output_bindings=(FmuRefBinding(reference=VarPowerFlowRefferenceType.i_A, fmu_variable_name="y"),),
            output_defaults=(FmuReferenceValue(reference=VarPowerFlowRefferenceType.i_A, value=0.0),),
            integration_method=FmuMeIntegrationMethod.EXPLICIT_EULER,
        )
        attach_fmu_to_device(device, grid, request)

        assert device.emt_fmu_me_import_config != ""
    finally:
        fmu_path.unlink(missing_ok=True)
