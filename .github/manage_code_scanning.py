#!/usr/bin/env python3
"""Repo-specific GitHub code scanning cleanup tool.

Running with no arguments performs the full cleanup for SanPen/VeraGrid:
1. Delete deletable code scanning analyses.
2. Dismiss any remaining open code scanning alerts.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

API_VERSION = "2026-03-10"
API_ROOT = "https://api.github.com"
DEFAULT_REPO = "SanPen/VeraGrid"


def get_token() -> str:
    candidates = [
        ("GH_TOKEN", None),
        ("GITHUB_TOKEN", None),
    ]

    for env_name, _ in candidates:
        value = os.environ.get(env_name)
        if value:
            return value

    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            check=True,
            capture_output=True,
            text=True,
        )
        token = result.stdout.strip()
        if token:
            return token
    except Exception:
        pass

    raise RuntimeError("No GitHub token found. Set GH_TOKEN or run `gh auth login`.")


def build_headers(token: str) -> dict[str, str]:
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": API_VERSION,
        "User-Agent": "VeraGrid-code-scanning-admin",
    }


def request_json(
    method: str,
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any] | None = None,
) -> tuple[Any, dict[str, str]]:
    data = None
    request_headers = dict(headers)
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        request_headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url, data=data, headers=request_headers, method=method)
    with urllib.request.urlopen(request) as response:
        body = response.read().decode("utf-8")
        return (json.loads(body) if body else None), dict(response.headers.items())


def http_error_message(exc: urllib.error.HTTPError) -> str:
    try:
        return exc.read().decode("utf-8", errors="replace")
    except Exception:
        return str(exc)


def next_link(headers: dict[str, str]) -> str | None:
    link_header = headers.get("Link")
    if not link_header:
        return None

    for chunk in link_header.split(","):
        section = chunk.strip()
        if 'rel="next"' not in section:
            continue
        start = section.find("<")
        end = section.find(">")
        if start != -1 and end != -1 and end > start:
            return section[start + 1 : end]
    return None


def paginate(url: str, headers: dict[str, str]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    next_url = url
    while next_url:
        page, response_headers = request_json("GET", next_url, headers)
        if not isinstance(page, list):
            raise RuntimeError(f"Expected list response from {next_url}")
        items.extend(page)
        next_url = next_link(response_headers)
    return items


def matches_filters(item: dict[str, Any], tool: str | None, category: str | None, ref: str | None) -> bool:
    if tool:
        tool_name = (
            item.get("tool", {}).get("name")
            or item.get("tool", {}).get("driver", {}).get("name")
            or item.get("most_recent_instance", {}).get("analysis_key", "")
        )
        if tool.lower() not in str(tool_name).lower():
            return False

    if category:
        category_name = item.get("category") or item.get("most_recent_instance", {}).get("category", "")
        if category.lower() not in str(category_name).lower():
            return False

    if ref:
        item_ref = item.get("ref") or item.get("most_recent_instance", {}).get("ref", "")
        if ref != item_ref:
            return False

    return True


def dismiss_alerts(
    repo: str,
    headers: dict[str, str],
    tool: str | None,
    category: str | None,
    ref: str | None,
    dry_run: bool,
    pause: float,
) -> int:
    url = f"{API_ROOT}/repos/{repo}/code-scanning/alerts?state=open&per_page=100"
    alerts = [item for item in paginate(url, headers) if matches_filters(item, tool, category, ref)]

    print(f"Open alerts matched: {len(alerts)}")
    if dry_run:
        for alert in alerts[:25]:
            print(
                f"would dismiss alert #{alert['number']} "
                f"tool={alert.get('tool', {}).get('name', '')} "
                f"severity={alert.get('rule', {}).get('severity', '')}"
            )
        return len(alerts)

    for index, alert in enumerate(alerts, start=1):
        url = f"{API_ROOT}/repos/{repo}/code-scanning/alerts/{alert['number']}"
        payload = {
            "state": "dismissed",
            "dismissed_reason": "won't fix",
            "dismissed_comment": "Bulk cleanup of noisy automated code scanning alerts.",
        }
        request_json("PATCH", url, headers, payload)
        print(f"[dismiss {index}/{len(alerts)}] alert #{alert['number']}")
        time.sleep(pause)

    return len(alerts)


def ensure_confirm_delete(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    params = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    if not any(key == "confirm_delete" for key, _ in params):
        params.append(("confirm_delete", "true"))
    query = urllib.parse.urlencode(params)
    return urllib.parse.urlunparse(parsed._replace(query=query))


def delete_analyses(
    repo: str,
    headers: dict[str, str],
    tool: str | None,
    category: str | None,
    ref: str | None,
    dry_run: bool,
    pause: float,
) -> int:
    list_url = f"{API_ROOT}/repos/{repo}/code-scanning/analyses?per_page=100"
    if dry_run:
        analyses = paginate(list_url, headers)
        analyses = [item for item in analyses if item.get("deletable") and matches_filters(item, tool, category, ref)]
        print(f"Deletable analyses matched: {len(analyses)}")
        for analysis in analyses[:25]:
            print(
                f"would delete analysis {analysis['id']} "
                f"tool={analysis.get('tool', {}).get('name', '')} "
                f"category={analysis.get('category', '')} "
                f"ref={analysis.get('ref', '')}"
            )
        return len(analyses)

    deleted = 0
    while True:
        analyses = paginate(list_url, headers)
        analyses = [item for item in analyses if item.get("deletable") and matches_filters(item, tool, category, ref)]
        if not analyses:
            print(f"Deletable analyses matched: 0")
            return deleted

        print(f"Deletable analyses matched: {len(analyses)}")
        analysis = analyses[0]
        delete_url: str | None = ensure_confirm_delete(
            f"{API_ROOT}/repos/{repo}/code-scanning/analyses/{analysis['id']}"
        )

        while delete_url:
            try:
                body, _ = request_json("DELETE", delete_url, headers)
            except urllib.error.HTTPError as exc:
                message = http_error_message(exc)
                if exc.code == 400 and "Analysis specified is not deletable" in message:
                    print(
                        f"skip stale analysis {analysis['id']} "
                        f"tool={analysis.get('tool', {}).get('name', '')}",
                        file=sys.stderr,
                    )
                    break
                raise
            deleted += 1
            print(
                f"[delete {deleted}] "
                f"tool={analysis.get('tool', {}).get('name', '')} "
                f"category={analysis.get('category', '')}"
            )
            next_url = body.get("confirm_delete_url") if isinstance(body, dict) else None
            delete_url = ensure_confirm_delete(next_url) if next_url else None

        time.sleep(pause)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Delete code scanning analyses and dismiss leftover alerts for VeraGrid."
    )
    parser.add_argument(
        "mode",
        nargs="?",
        default="cleanup",
        choices=["cleanup", "delete-analyses", "dismiss-alerts"],
        help="Default is cleanup: delete analyses, then dismiss remaining alerts.",
    )
    parser.add_argument("--repo", default=DEFAULT_REPO, help=f"Default: {DEFAULT_REPO}")
    parser.add_argument("--tool", help="Only touch tools whose name contains this text")
    parser.add_argument("--category", help="Only touch categories containing this text")
    parser.add_argument("--ref", help="Only touch a specific ref, e.g. refs/heads/master")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be changed")
    parser.add_argument("--pause", type=float, default=0.05, help="Delay between API calls")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        token = get_token()
        headers = build_headers(token)

        if args.mode == "delete-analyses":
            delete_analyses(args.repo, headers, args.tool, args.category, args.ref, args.dry_run, args.pause)
            return 0

        if args.mode == "dismiss-alerts":
            dismiss_alerts(args.repo, headers, args.tool, args.category, args.ref, args.dry_run, args.pause)
            return 0

        delete_analyses(args.repo, headers, args.tool, args.category, args.ref, args.dry_run, args.pause)
        dismiss_alerts(args.repo, headers, args.tool, args.category, args.ref, args.dry_run, args.pause)
        return 0

    except urllib.error.HTTPError as exc:
        message = exc.read().decode("utf-8", errors="replace")
        print(f"GitHub API error: {exc.code} {message}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
