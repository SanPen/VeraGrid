from __future__ import annotations

import ast
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]


def get_local_results_declarations(relative_path: str, class_name: str) -> dict[str, str]:
    module_path = REPO_ROOT / relative_path
    module = ast.parse(module_path.read_text())

    for node in module.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for item in node.body:
                if not isinstance(item, ast.Assign):
                    continue

                for target in item.targets:
                    if isinstance(target, ast.Name) and target.id == "LOCAL_RESULTS_DECLARATIONS":
                        declarations: dict[str, str] = dict()

                        if isinstance(item.value, (ast.Tuple, ast.List)):
                            for declaration in item.value.elts:
                                if not isinstance(declaration, ast.Call):
                                    continue

                                name = None
                                tpe = None
                                for keyword in declaration.keywords:
                                    if keyword.arg == "name":
                                        name = ast.literal_eval(keyword.value)
                                    elif keyword.arg == "tpe":
                                        tpe = ast.unparse(keyword.value)

                                if name is not None and tpe is not None:
                                    declarations[name] = tpe

                        return declarations

    raise AssertionError(f"Could not find LOCAL_RESULTS_DECLARATIONS for {class_name} in {relative_path}")


@pytest.mark.parametrize(
    ("relative_path", "class_name", "expected_properties"),
    [
        (
            "src/VeraGridEngine/Simulations/PowerFlow/power_flow_results.py",
            "PowerFlowResults",
            {
                "vsc_names": "StrVec",
                "gen_p": "Vec",
                "battery_p": "Vec",
            },
        ),
        (
            "src/VeraGridEngine/Simulations/PowerFlow/power_flow_results_3ph.py",
            "PowerFlowResults3Ph",
            {
                "vsc_names": "StrVec",
                "shunt_Vn": "CxVec",
                "load_Vn": "CxVec",
            },
        ),
        (
            "src/VeraGridEngine/Simulations/StateEstimation/state_estimation_results.py",
            "StateEstimationResults",
            {
                "vsc_names": "StrVec",
            },
        ),
        (
            "src/VeraGridEngine/Simulations/LinearFactors/linear_analysis_results.py",
            "LinearAnalysisResults",
            {
                "hvdc_names": "StrVec",
                "vsc_names": "StrVec",
            },
        ),
        (
            "src/VeraGridEngine/Simulations/NTC/ntc_results.py",
            "OptimalNetTransferCapacityResults",
            {
                "nodal_balance": "Vec",
            },
        ),
        (
            "src/VeraGridEngine/Simulations/NTC/ntc_ts_results.py",
            "OptimalNetTransferCapacityTimeSeriesResults",
            {
                "vsc_names": "StrVec",
                "nodal_balance": "Mat",
            },
        ),
        (
            "src/VeraGridEngine/Simulations/OPF/opf_results.py",
            "OptimalPowerFlowResults",
            {
                "vsc_names": "StrVec",
            },
        ),
        (
            "src/VeraGridEngine/Simulations/OPF/opf_ts_results.py",
            "OptimalPowerFlowTimeSeriesResults",
            {
                "vsc_names": "StrVec",
                "fuel_names": "StrVec",
                "emission_names": "StrVec",
                "technology_names": "StrVec",
                "fluid_node_names": "StrVec",
                "fluid_path_names": "StrVec",
                "fluid_injection_names": "StrVec",
                "vsc_Pf": "Mat",
                "vsc_loading": "Mat",
                "battery_invested": "Mat",
            },
        ),
        (
            "src/VeraGridEngine/Simulations/SmallSignalStabilityEmt/small_signal_stability_emt_results.py",
            "SmallSignalStabilityEmtResults",
            {
                "right_vecs": "CxMat",
                "left_vecs": "CxMat",
                "period": "float",
                "damping_ratios": "Vec",
                "conjugate_frequencies": "Vec",
                "stat_vars_array": "StrVec",
            },
        ),
        (
            "src/VeraGridEngine/Simulations/SmallSignalStabilityRms/small_signal_results.py",
            "SmallSignalStabilityRmsResults",
            {
                "stat_vars_array": "StrVec",
            },
        ),
        (
            "src/VeraGridEngine/Simulations/Stochastic/stochastic_power_flow_results.py",
            "StochasticPowerFlowResults",
            {
                "points_number": "int",
                "bus_names": "StrVec",
                "branch_names": "StrVec",
                "bus_types": "IntVec",
                "S_points": "CxMat",
                "V_points": "CxMat",
                "Sbr_points": "CxMat",
                "loading_points": "CxMat",
                "losses_points": "CxMat",
                "error_series": "list",
                "voltage": "Vec",
                "loading": "Vec",
                "sbranch": "Vec",
                "losses": "Vec",
                "v_std_conv": "Mat",
                "s_std_conv": "Mat",
                "l_std_conv": "Mat",
                "loss_std_conv": "Mat",
                "v_avg_conv": "Mat",
                "s_avg_conv": "Mat",
                "l_avg_conv": "Mat",
                "loss_avg_conv": "Mat",
            },
        ),
    ],
)
def test_result_data_fields_are_registered(relative_path, class_name, expected_properties) -> None:
    registered = get_local_results_declarations(relative_path=relative_path, class_name=class_name)

    assert registered.keys() >= expected_properties.keys()

    for property_name, expected_type_name in expected_properties.items():
        assert registered[property_name] == expected_type_name
