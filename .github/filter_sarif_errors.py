#!/usr/bin/env python3
"""Keep only error-level SARIF results."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def rule_levels(run: dict[str, Any]) -> dict[tuple[str, str], str]:
    levels: dict[tuple[str, str], str] = {}

    def collect(driver_name: str, rules: list[dict[str, Any]] | None) -> None:
        if not rules:
            return
        for rule in rules:
            rule_id = rule.get("id")
            level = rule.get("defaultConfiguration", {}).get("level")
            if rule_id and level:
                levels[(driver_name, rule_id)] = level

    driver = run.get("tool", {}).get("driver", {})
    driver_name = driver.get("name", "")
    collect(driver_name, driver.get("rules"))

    for extension in run.get("tool", {}).get("extensions", []):
        collect(extension.get("name", driver_name), extension.get("rules"))

    return levels


def result_level(result: dict[str, Any], levels: dict[tuple[str, str], str], driver_name: str) -> str:
    explicit_level = result.get("level")
    if explicit_level:
        return explicit_level

    rule_id = result.get("ruleId")
    if not rule_id:
        return "warning"

    return levels.get((driver_name, rule_id), "warning")


def filter_run(run: dict[str, Any]) -> None:
    driver = run.get("tool", {}).get("driver", {})
    driver_name = driver.get("name", "")
    levels = rule_levels(run)

    kept_results: list[dict[str, Any]] = []
    used_rule_ids: set[str] = set()

    for result in run.get("results", []):
        if result_level(result, levels, driver_name) != "error":
            continue
        kept_results.append(result)
        rule_id = result.get("ruleId")
        if rule_id:
            used_rule_ids.add(rule_id)

    run["results"] = kept_results

    for tool_section in [driver, *run.get("tool", {}).get("extensions", [])]:
        rules = tool_section.get("rules")
        if not rules:
            continue
        tool_section["rules"] = [rule for rule in rules if rule.get("id") in used_rule_ids]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sarif_file", type=Path)
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Write filtered SARIF to a different path. Defaults to in-place.",
    )
    args = parser.parse_args()

    target = args.output or args.sarif_file
    data = json.loads(args.sarif_file.read_text(encoding="utf-8"))

    for run in data.get("runs", []):
        filter_run(run)

    target.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
