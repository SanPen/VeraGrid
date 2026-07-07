# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path
import importlib
import sys


if __package__ in {None, ""}:
    _REPO_ROOT = Path(__file__).resolve().parents[2]
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))
    from VeraGridEngine.IO.fmu.exporter.api import export_fmu
    from VeraGridEngine.IO.fmu.exporter.config import ExportConfig, detect_target_platform
    from VeraGridEngine.IO.fmu.exporter.real_pilots import get_powerfactory_pilot_model, pilot_output_path
else:
    from .api import export_fmu
    from .config import ExportConfig, detect_target_platform
    from .real_pilots import get_powerfactory_pilot_model, pilot_output_path


IDE_PLAY_DEFAULTS = {
    "pilot": "rms",
    "project": "Project_prueba",
    "study_case": "Caso Base",
    "agent_name": "Test",
    "output_dir": str(Path(__file__).parent / "tests" / "artifacts"),
    "configure": True,
    "execute": True,
    "allow_engine": False,
}


def _default_ide_argv() -> list[str]:
    argv = [str(IDE_PLAY_DEFAULTS["pilot"])]
    argv.extend(["--project", str(IDE_PLAY_DEFAULTS["project"])])
    argv.extend(["--study-case", str(IDE_PLAY_DEFAULTS["study_case"])])
    argv.extend(["--agent-name", str(IDE_PLAY_DEFAULTS["agent_name"])])
    argv.extend(["--output-dir", str(IDE_PLAY_DEFAULTS["output_dir"])])
    if bool(IDE_PLAY_DEFAULTS["configure"]):
        argv.append("--configure")
    if bool(IDE_PLAY_DEFAULTS["execute"]):
        argv.append("--execute")
    if bool(IDE_PLAY_DEFAULTS["allow_engine"]):
        argv.append("--allow-engine")
    return argv


def candidate_powerfactory_python_dirs() -> list[Path]:
    root = Path(r"C:\Program Files\DIgSILENT")
    candidates: list[Path] = []
    if not root.exists():
        return candidates
    for version_dir in sorted(root.glob("PowerFactory*")):
        python_dir = version_dir / "Python" / f"{sys.version_info.major}.{sys.version_info.minor}"
        if (python_dir / "powerfactory.pyd").exists():
            candidates.append(python_dir)
    return candidates


def load_powerfactory_module():
    for directory in candidate_powerfactory_python_dirs():
        if str(directory) not in sys.path:
            sys.path.insert(0, str(directory))
        try:
            return importlib.import_module("powerfactory"), directory
        except Exception:
            continue
    raise ModuleNotFoundError("Could not locate a compatible PowerFactory Python module for this Python version")


def _get_application(powerfactory_module, *, allow_engine: bool):
    method_names = ["GetApplication"]
    if allow_engine:
        method_names.append("GetApplicationExt")
    for method_name in method_names:
        method = getattr(powerfactory_module, method_name, None)
        if method is None:
            continue
        try:
            app = method()
        except Exception:
            continue
        if app is not None:
            return app, method_name
    return None, None


def list_powerfactory_projects(app) -> list[str]:
    user = app.GetCurrentUser()
    projects = user.GetContents("*.IntPrj", 1) if user is not None else []
    return sorted({getattr(project, "loc_name", "") for project in projects if getattr(project, "loc_name", None)})


def activate_project(app, project_name: str | None) -> tuple[object | None, list[str]]:
    available_projects = list_powerfactory_projects(app)
    if project_name:
        rc = app.ActivateProject(project_name)
        if rc != 0:
            raise RuntimeError(f"Could not activate PowerFactory project {project_name!r}; return code {rc}")
    project = app.GetActiveProject()
    return project, available_projects


def activate_study_case(project, study_case_name: str | None) -> tuple[object | None, list[str]]:
    if project is None:
        return None, []
    study_cases = project.GetContents("*.IntCase", 1)
    available_cases = [getattr(case, "loc_name", "") for case in study_cases if getattr(case, "loc_name", None)]
    if study_case_name:
        for case in study_cases:
            if getattr(case, "loc_name", None) == study_case_name:
                case.Activate()
                return case, available_cases
        raise RuntimeError(f"Could not find study case {study_case_name!r} in project {getattr(project, 'loc_name', None)!r}")
    active_case = None
    try:
        active_case = project.GetContents("*.IntCase", 1)[0] if study_cases else None
        if active_case is not None:
            active_case.Activate()
    except Exception:
        active_case = None
    return active_case, available_cases


def inspect_cosimulation_objects(app) -> dict[str, object]:
    report: dict[str, object] = {}
    try:
        cosim = app.GetFromStudyCase("ComCosim")
    except Exception as exc:
        report["warning"] = str(exc)
        return report
    if cosim is None:
        report["present"] = False
        return report
    report["present"] = True
    report["path"] = str(cosim)
    report["attributes"] = {
        "cfmu": cosim.GetAttribute("cfmu"),
        "cfmuOutserv": cosim.GetAttribute("cfmuOutserv"),
        "cfmuSimMod": cosim.GetAttribute("cfmuSimMod"),
        "iopt_type": getattr(cosim, "iopt_type", None),
        "task": getattr(cosim, "task", None),
    }
    return report


def _set_pf_attribute(obj, name: str, value) -> None:
    setter = getattr(obj, "SetAttribute", None)
    if callable(setter):
        setter(name, value)
        return
    setattr(obj, name, value)


def _get_active_grid(project) -> object:
    networks = project.GetContents("*.ElmNet", 1) if project is not None else []
    if not networks:
        raise RuntimeError("No ElmNet grid object was found in the active PowerFactory project")
    return networks[0]


def _find_or_create_agent(grid, agent_name: str):
    existing = grid.GetContents(f"{agent_name}.ElmAgent", 1)
    if existing:
        return existing[0], False
    agent = grid.CreateObject("ElmAgent", agent_name)
    if agent is None:
        raise RuntimeError(f"Could not create ElmAgent {agent_name!r} under grid {getattr(grid, 'loc_name', None)!r}")
    return agent, True


def _set_other_agents_out_of_service(cosim, selected_agent) -> list[str]:
    disabled: list[str] = []
    for agent in (cosim.GetAttribute("cfmu") or []):
        name = getattr(agent, "loc_name", None)
        if name == getattr(selected_agent, "loc_name", None):
            _set_pf_attribute(agent, "outserv", 0)
            continue
        _set_pf_attribute(agent, "outserv", 1)
        if name:
            disabled.append(str(name))
    return disabled


def configure_powerfactory_cosimulation(
    app,
    *,
    fmu_path: str | Path,
    project_name: str | None,
    study_case_name: str | None,
    agent_name: str,
    execute: bool,
) -> dict[str, object]:
    project, available_projects = activate_project(app, project_name)
    study_case, available_cases = activate_study_case(project, study_case_name)
    if project is None or study_case is None:
        raise RuntimeError("An active PowerFactory project and study case are required")

    cosim = app.GetFromStudyCase("ComCosim")
    if cosim is None:
        raise RuntimeError("ComCosim was not found in the active study case")

    grid = _get_active_grid(project)
    agent, created = _find_or_create_agent(grid, agent_name)

    _set_pf_attribute(agent, "path", str(Path(fmu_path).resolve()))
    _set_pf_attribute(agent, "outserv", 0)
    _set_pf_attribute(cosim, "iopt_type", 2)
    _set_pf_attribute(cosim, "task", 0)
    disabled_agents = _set_other_agents_out_of_service(cosim, agent)

    execution_result = None
    execution_error = None
    if execute:
        try:
            execution_result = cosim.Execute()
        except Exception as exc:
            execution_error = str(exc)

    return {
        "active_project": getattr(project, "loc_name", None),
        "active_study_case": getattr(study_case, "loc_name", None),
        "available_projects": available_projects,
        "available_study_cases": available_cases,
        "grid": getattr(grid, "loc_name", None),
        "agent": getattr(agent, "loc_name", None),
        "agent_created": created,
        "disabled_agents": disabled_agents,
        "agent_path": getattr(agent, "path", None),
        "cosim_path": str(cosim),
        "iopt_type": getattr(cosim, "iopt_type", None),
        "task": getattr(cosim, "task", None),
        "cfmu": [getattr(item, "loc_name", None) for item in (cosim.GetAttribute("cfmu") or [])],
        "execute_requested": execute,
        "execute_result": execution_result,
        "execute_error": execution_error,
    }


def probe_powerfactory(project_name: str | None = None, study_case_name: str | None = None, *, allow_engine: bool = False) -> dict[str, object]:
    report: dict[str, object] = {
        "python_dirs": [str(path) for path in candidate_powerfactory_python_dirs()],
        "module_loaded": False,
        "license_available": False,
    }
    try:
        powerfactory, module_dir = load_powerfactory_module()
    except Exception as exc:
        report["error"] = str(exc)
        return report

    report["module_loaded"] = True
    report["module_dir"] = str(module_dir)
    report["module"] = getattr(powerfactory, "__file__", "powerfactory")

    app, acquisition_method = _get_application(powerfactory, allow_engine=allow_engine)
    report["application_method"] = acquisition_method
    report["license_available"] = app is not None
    if app is None:
        report["error"] = "Could not obtain a PowerFactory application handle; open PowerFactory first or pass --allow-engine"
        return report

    try:
        project, available_projects = activate_project(app, project_name)
        report["available_projects"] = available_projects
        report["active_project"] = None if project is None else getattr(project, "loc_name", None)

        study_case, available_cases = activate_study_case(project, study_case_name)
        report["available_study_cases"] = available_cases
        report["active_study_case"] = None if study_case is None else getattr(study_case, "loc_name", None)
        report["cosimulation"] = inspect_cosimulation_objects(app)
    except Exception as exc:
        report["error"] = str(exc)
    return report


def export_pilot_for_powerfactory(pilot_name: str, output_dir: str | Path) -> Path:
    pilot = get_powerfactory_pilot_model(pilot_name)
    output_path = pilot_output_path(output_dir, pilot)
    return export_fmu(
        pilot.model,
        ExportConfig(
            model_name=pilot.name,
            output_path=output_path,
            target_platform=detect_target_platform(),
            compile_binary=True,
        ),
    )


def powerfactory_manual_checklist(fmu_path: str | Path, project_name: str | None = None, study_case_name: str | None = None) -> list[str]:
    lines = [
        "Abre PowerFactory con licencia activa.",
    ]
    if project_name:
        lines.append(f"Activa el proyecto `{project_name}`.")
    else:
        lines.append("Activa el proyecto de pruebas que quieras usar.")
    if study_case_name:
        lines.append(f"Activa el estudio `{study_case_name}`.")
    else:
        lines.append("Activa el study case donde vayas a probar el FMU.")
    lines.extend(
        [
            f"Importa el FMU `{fmu_path}` como bloque de Co-Simulation FMI 2.0.",
            "Conecta las entradas/salidas del piloto a fuentes/medidas simples del caso de estudio.",
            "Ejecuta una simulacion RMS o EMT segun el piloto exportado y verifica que las magnitudes cambian de forma coherente.",
            "Si PowerFactory rechaza el FMU, guarda el mensaje exacto para ajustar el wrapper/import path.",
        ]
    )
    return lines


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(description="Prepare and probe PowerFactory validation for VeraGrid FMU pilots")
    parser.add_argument("pilot", choices=["rms", "emt"], help="Pilot FMU to export for PowerFactory")
    parser.add_argument("--output-dir", default=str(Path(__file__).parent / "dist"))
    parser.add_argument("--project", default=None, help="PowerFactory project to activate")
    parser.add_argument("--study-case", default=None, help="PowerFactory study case to activate")
    parser.add_argument("--agent-name", default="Test", help="ElmAgent name to create or update inside PowerFactory")
    parser.add_argument("--allow-engine", action="store_true", help="Allow launching PowerFactory in engine mode if no GUI instance is attached")
    parser.add_argument("--configure", action="store_true", help="Configure ComCosim and the ElmAgent automatically")
    parser.add_argument("--execute", action="store_true", help="Execute ComCosim after configuring it")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    if argv is None and len(sys.argv) == 1:
        argv = _default_ide_argv()
    args = parser.parse_args(argv)
    fmu_path = export_pilot_for_powerfactory(args.pilot, args.output_dir)
    report = probe_powerfactory(project_name=args.project, study_case_name=args.study_case, allow_engine=args.allow_engine)
    configuration = None
    if args.configure and report.get("license_available"):
        powerfactory, _ = load_powerfactory_module()
        app, _ = _get_application(powerfactory, allow_engine=args.allow_engine)
        if app is not None:
            configuration = configure_powerfactory_cosimulation(
                app,
                fmu_path=fmu_path,
                project_name=args.project,
                study_case_name=args.study_case,
                agent_name=args.agent_name,
                execute=args.execute,
            )
    print(
        {
            "fmu_path": str(fmu_path),
            "powerfactory": report,
            "configuration": configuration,
            "manual_checklist": powerfactory_manual_checklist(fmu_path, project_name=args.project, study_case_name=args.study_case),
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
