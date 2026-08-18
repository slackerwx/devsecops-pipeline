#!/usr/bin/env python3
"""Evaluate findings against thresholds.

category: one partial findings file (fail-fast, exit 1 on fail).
all:      merge every findings-*.json under a directory into findings.json with the verdict (exit 0).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

SEVERITIES = ("critical", "high", "medium", "low", "info")
RANK = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
CATEGORIES = ("secrets", "sast", "sca", "license", "iac", "container", "dast")
DEFAULT_FAIL_ON = (
    "secrets=any,sast=high,sca=high,container=critical,iac=high,dast=high,license=none"
)
STAGE_OF = {
    "secrets": "secrets",
    "sast": "sast",
    "sca": "sca",
    "license": "sca",
    "iac": "iac",
    "container": "image",
    "dast": "dast",
}
SCHEMA = "devsecops-pipeline/findings/v1"


def die(msg: str) -> None:
    print(f"gate: {msg}", file=sys.stderr)
    raise SystemExit(2)


def parse_fail_on(spec: str) -> dict[str, str]:
    thresholds = dict(part.split("=") for part in DEFAULT_FAIL_ON.split(","))
    for part in (spec or "").split(","):
        part = part.strip()
        if not part:
            continue
        if "=" not in part:
            die(f"bad fail-on entry `{part}` (expected category=threshold)")
        k, v = (x.strip().lower() for x in part.split("=", 1))
        if k not in CATEGORIES:
            die(f"unknown category `{k}` in fail-on")
        if v not in SEVERITIES + ("any", "none"):
            die(f"unknown threshold `{v}` for {k}")
        thresholds[k] = v
    return thresholds


def evaluate(partial: dict, threshold: str) -> tuple[str, int]:
    """Return (gate, count at or above threshold); gate is pass | fail | skipped."""
    status = partial.get("status", "ok")
    if status == "skipped":
        return "skipped", 0
    if status == "error":
        return "fail", 0
    if threshold == "none":
        return "pass", 0
    findings = partial.get("findings", [])
    if threshold == "any":
        return ("fail" if findings else "pass"), len(findings)
    n = sum(
        1 for f in findings if RANK.get(f.get("severity", "info"), 0) >= RANK[threshold]
    )
    return ("fail" if n else "pass"), n


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def cmd_category(a: argparse.Namespace) -> int:
    thresholds = parse_fail_on(a.fail_on)
    path = Path(a.findings)
    partial = load(path)
    cat = partial["category"]
    gate, n = evaluate(partial, thresholds[cat])
    partial["gate"], partial["threshold"], partial["at_or_above"] = (
        gate,
        thresholds[cat],
        n,
    )
    path.write_text(json.dumps(partial, indent=2), encoding="utf-8")
    c = partial.get("counts", {})
    tools = ", ".join(t["name"] for t in partial.get("tools", [])) or "-"
    line = (
        f"- **{cat}** ({tools}): {gate.upper()} — {n} finding(s) at or above `{thresholds[cat]}`; "
        f"total {len(partial.get('findings', []))} (crit {c.get('critical', 0)}, high {c.get('high', 0)}, med {c.get('medium', 0)}, low {c.get('low', 0)})"
    )
    if partial.get("status") == "error":
        line += f" — tool error: {partial.get('reason', '')}"
    print(line)
    return 1 if gate == "fail" else 0


def cmd_all(a: argparse.Namespace) -> int:
    thresholds = parse_fail_on(a.fail_on)
    stages = json.loads(a.stages) if a.stages else {}
    partials = {}
    for path in sorted(Path(a.dir).rglob("findings-*.json")):
        doc = load(path)
        partials[doc["category"]] = doc
    categories, failed = {}, []
    for cat in CATEGORIES:
        doc = partials.get(cat)
        if doc is None:
            disabled = bool(stages) and not stages.get(STAGE_OF[cat], True)
            doc = {
                "category": cat,
                "tools": [],
                "status": "skipped",
                "reason": "stage disabled"
                if disabled
                else "no results produced (stage did not run)",
                "counts": {s: 0 for s in SEVERITIES},
                "findings": [],
            }
        gate, n = evaluate(doc, thresholds[cat])
        doc["gate"], doc["threshold"], doc["at_or_above"] = gate, thresholds[cat], n
        categories[cat] = doc
        if gate == "fail":
            failed.append(cat)
    out = {
        "schema": SCHEMA,
        "run": {
            "repository": os.environ.get("GITHUB_REPOSITORY", ""),
            "sha": os.environ.get("GITHUB_SHA", ""),
            "ref": os.environ.get("GITHUB_REF", ""),
            "run_id": int(os.environ.get("GITHUB_RUN_ID") or 0),
            "run_attempt": int(os.environ.get("GITHUB_RUN_ATTEMPT") or 1),
            "working_directory": a.working_directory,
            "stack": a.stack,
            "mode": a.mode,
        },
        "thresholds": thresholds,
        "categories": categories,
        "verdict": "fail" if failed else "pass",
        "failed_categories": failed,
    }
    path = Path(a.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"verdict={out['verdict']}")
    print(f"failed-categories={','.join(failed)}")
    return 0


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("category")
    c.add_argument("--findings", required=True)
    c.add_argument("--fail-on", default="")
    c.set_defaults(fn=cmd_category)
    g = sub.add_parser("all")
    g.add_argument("--dir", required=True)
    g.add_argument("--out", required=True)
    g.add_argument("--fail-on", default="")
    g.add_argument("--mode", default="enforce")
    g.add_argument("--stack", default="")
    g.add_argument("--working-directory", default=".")
    g.add_argument("--stages", default="")
    g.set_defaults(fn=cmd_all)
    a = p.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
