from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from VeraGridEngine.IO.fmu.exporter.api import export_fmu
from VeraGridEngine.IO.fmu.exporter.build import host_build_capable
from VeraGridEngine.IO.fmu.exporter.config import ExportConfig as CsExportConfig, detect_target_platform as detect_cs_target_platform
from VeraGridEngine.IO.fmu.exporter.compat import Block, Const, Var
from VeraGridEngine.IO.fmu.exporter_me.api import export_fmu_me
from VeraGridEngine.IO.fmu.exporter_me.config import ExportConfig as MeExportConfig, detect_target_platform as detect_me_target_platform
from VeraGridEngine.IO.fmu.importer import (
    FmuImportConfig,
    FmuMeIntegrationMethod,
    FmuRefBinding,
    attach_rms_fmu_cs_device,
    attach_emt_fmu_cs_device,
    attach_rms_fmu_me_device,
    attach_emt_fmu_me_device,
    register_rms_fmu_cs_device,
    register_emt_fmu_cs_device,
    register_rms_fmu_me_device,
    register_emt_fmu_me_device,
)

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.enumerations import DeviceType, VarPowerFlowRefferenceType


def _tmp_root() -> Path:
    root = Path(__file__).resolve().parent / ".tmp"
    root.mkdir(parents=True, exist_ok=True)
    return root.resolve()


def build_simple_output_fmu_block() -> Block:
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


def build_simple_me_output_fmu_block() -> Block:
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


class FakeProblem:
    def __init__(self, block: Block):
        self.uid2idx_event_params = {var.uid: index for index, var in enumerate(block.event_dict.keys())}
        self._fmu_cs_adapters = list()
        self._fmu_me_adapters = list()


@pytest.mark.skipif(not host_build_capable(), reason="No usable host build toolchain available")
def test_rms_device_config_can_restore_runtime_spec() -> None:
    pytest.importorskip("fmpy")

    output_root = _tmp_root()
    fmu_path = output_root / "restore_rms.fmu"
    try:
        exported_fmu = export_fmu(
            build_simple_output_fmu_block(),
            CsExportConfig(
                model_name="RestoreRmsDevice",
                output_path=fmu_path,
                target_platform=detect_cs_target_platform(),
                compile_binary=True,
                keep_build_dir=False,
            ),
        )

        device = SimpleNamespace(device_type=DeviceType.LoadDevice, rms_model=Block(), rms_fmu_import_config="")
        attach_rms_fmu_cs_device(
            device=device,
            vfactory=VarFactory(name="restore_rms_var_factory"),
            config=FmuImportConfig(fmu_path=exported_fmu, extraction_root=output_root),
            input_bindings=tuple(),
            output_bindings=(FmuRefBinding(VarPowerFlowRefferenceType.P, "y"),),
            output_defaults={VarPowerFlowRefferenceType.P: 0.0},
            name="restore_rms_template",
        )

        loaded_block = device.rms_model.copy()
        loaded_device = SimpleNamespace(
            device_type=device.device_type,
            rms_model=loaded_block,
            rms_fmu_import_config=device.rms_fmu_import_config,
            bus=SimpleNamespace(rms_model=Block()),
            idtag="loaded-rms-device",
        )
        problem = FakeProblem(loaded_block)
        register_rms_fmu_cs_device(problem, loaded_device, loaded_block)
        assert len(problem._fmu_cs_adapters) == 1
    finally:
        fmu_path.unlink(missing_ok=True)


@pytest.mark.skipif(not host_build_capable(), reason="No usable host build toolchain available")
def test_emt_device_config_can_restore_runtime_spec() -> None:
    pytest.importorskip("fmpy")

    output_root = _tmp_root()
    fmu_path = output_root / "restore_emt.fmu"
    try:
        exported_fmu = export_fmu(
            build_simple_output_fmu_block(),
            CsExportConfig(
                model_name="RestoreEmtDevice",
                output_path=fmu_path,
                target_platform=detect_cs_target_platform(),
                compile_binary=True,
                keep_build_dir=False,
            ),
        )

        device = SimpleNamespace(device_type=DeviceType.LoadDevice, emt_model=Block(), emt_fmu_import_config="")
        attach_emt_fmu_cs_device(
            device=device,
            vfactory=VarFactory(name="restore_emt_var_factory"),
            config=FmuImportConfig(fmu_path=exported_fmu, extraction_root=output_root),
            input_bindings=tuple(),
            output_bindings=(FmuRefBinding(VarPowerFlowRefferenceType.i_A, "y"),),
            output_defaults={VarPowerFlowRefferenceType.i_A: 0.0},
            name="restore_emt_template",
        )

        loaded_block = device.emt_model.copy()
        loaded_device = SimpleNamespace(
            device_type=device.device_type,
            emt_model=loaded_block,
            emt_fmu_import_config=device.emt_fmu_import_config,
            bus=SimpleNamespace(emt_model=Block()),
            idtag="loaded-emt-device",
        )
        problem = FakeProblem(loaded_block)
        register_emt_fmu_cs_device(problem, loaded_device, loaded_block)
        assert len(problem._fmu_cs_adapters) == 1
    finally:
        fmu_path.unlink(missing_ok=True)


@pytest.mark.skipif(not host_build_capable(), reason="No usable host build toolchain available")
def test_rms_me_device_config_can_restore_runtime_spec() -> None:
    pytest.importorskip("fmpy")

    output_root = _tmp_root()
    fmu_path = output_root / "restore_rms_me.fmu"
    try:
        exported_fmu = export_fmu_me(
            build_simple_me_output_fmu_block(),
            MeExportConfig(
                model_name="RestoreRmsMeDevice",
                output_path=fmu_path,
                target_platform=detect_me_target_platform(),
                compile_binary=True,
                keep_build_dir=False,
            ),
        )

        device = SimpleNamespace(device_type=DeviceType.LoadDevice, rms_model=Block(), rms_fmu_me_import_config="")
        attach_rms_fmu_me_device(
            device=device,
            vfactory=VarFactory(name="restore_rms_me_var_factory"),
            config=FmuImportConfig(fmu_path=exported_fmu, extraction_root=output_root),
            input_bindings=(FmuRefBinding(VarPowerFlowRefferenceType.Vm, "u"),),
            output_bindings=(FmuRefBinding(VarPowerFlowRefferenceType.P, "y"),),
            output_defaults={VarPowerFlowRefferenceType.P: 0.0},
            integration_method=FmuMeIntegrationMethod.EXPLICIT_EULER,
            name="restore_rms_me_template",
        )

        loaded_block = device.rms_model.copy()
        loaded_device = SimpleNamespace(
            device_type=device.device_type,
            rms_model=loaded_block,
            rms_fmu_me_import_config=device.rms_fmu_me_import_config,
            bus=SimpleNamespace(rms_model=Block()),
            idtag="loaded-rms-me-device",
        )
        problem = FakeProblem(loaded_block)
        register_rms_fmu_me_device(problem, loaded_device, loaded_block)
        assert len(problem._fmu_me_adapters) == 1
    finally:
        fmu_path.unlink(missing_ok=True)


@pytest.mark.skipif(not host_build_capable(), reason="No usable host build toolchain available")
def test_emt_me_device_config_can_restore_runtime_spec() -> None:
    pytest.importorskip("fmpy")

    output_root = _tmp_root()
    fmu_path = output_root / "restore_emt_me.fmu"
    try:
        exported_fmu = export_fmu_me(
            build_simple_me_output_fmu_block(),
            MeExportConfig(
                model_name="RestoreEmtMeDevice",
                output_path=fmu_path,
                target_platform=detect_me_target_platform(),
                compile_binary=True,
                keep_build_dir=False,
            ),
        )

        device = SimpleNamespace(device_type=DeviceType.LoadDevice, emt_model=Block(), emt_fmu_me_import_config="")
        attach_emt_fmu_me_device(
            device=device,
            vfactory=VarFactory(name="restore_emt_me_var_factory"),
            config=FmuImportConfig(fmu_path=exported_fmu, extraction_root=output_root),
            input_bindings=tuple(),
            output_bindings=(FmuRefBinding(reference=VarPowerFlowRefferenceType.i_A, fmu_variable_name="y"),),
            output_defaults={VarPowerFlowRefferenceType.i_A: 0.0},
            integration_method=FmuMeIntegrationMethod.EXPLICIT_EULER,
            name="restore_emt_me_template",
        )

        loaded_block = device.emt_model.copy()
        loaded_device = SimpleNamespace(
            device_type=device.device_type,
            emt_model=loaded_block,
            emt_fmu_me_import_config=device.emt_fmu_me_import_config,
            bus=SimpleNamespace(emt_model=Block()),
            idtag="loaded-emt-me-device",
        )
        problem = FakeProblem(loaded_block)
        register_emt_fmu_me_device(problem, loaded_device, loaded_block)
        assert len(problem._fmu_me_adapters) == 1
    finally:
        fmu_path.unlink(missing_ok=True)
