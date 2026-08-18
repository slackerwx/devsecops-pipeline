#!/usr/bin/env python3
"""Emit SARIF 2.1.0 from a partial findings file (for tools without native SARIF: gitleaks, zap)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

LEVEL = {
    "critical": "error",
    "high": "error",
    "medium": "warning",
    "low": "note",
    "info": "note",
}
SCORE = {"critical": "9.5", "high": "8.0", "medium": "5.0", "low": "2.0", "info": "0.0"}
DRIVER = {
    "gitleaks": ("Gitleaks", "https://github.com/gitleaks/gitleaks"),
    "zap": ("ZAP", "https://www.zaproxy.org/"),
    "trivy": ("Trivy", "https://trivy.dev"),
    "semgrep": ("Semgrep", "https://semgrep.dev"),
    "hadolint": ("Hadolint", "https://github.com/hadolint/hadolint"),
}


def _physical(location: str) -> dict:
    if location.startswith(("http://", "https://")):
        return {"artifactLocation": {"uri": location}}
    path, sep, line = location.rpartition(":")
    if not sep:
        path, line = location, ""
    physical = {"artifactLocation": {"uri": path or location}}
    if line.isdigit() and int(line) > 0:
        physical["region"] = {"startLine": int(line)}
    return physical


def to_sarif(partial: dict) -> dict:
    tool = (partial.get("tools") or [{"name": "unknown", "version": ""}])[0]
    name, uri = DRIVER.get(tool["name"], (tool["name"], ""))
    rules, index, results = [], {}, []
    for f in partial.get("findings", []):
        rid = f.get("id") or "finding"
        if rid not in index:
            index[rid] = len(rules)
            rules.append(
                {
                    "id": rid,
                    "name": rid,
                    "shortDescription": {"text": (f.get("title") or rid)[:200]},
                    "helpUri": f.get("url") or uri,
                    "properties": {
                        "security-severity": SCORE[f["severity"]],
                        "tags": ["security", f["severity"]],
                    },
                }
            )
        results.append(
            {
                "ruleId": rid,
                "ruleIndex": index[rid],
                "level": LEVEL[f["severity"]],
                "message": {"text": f.get("title") or rid},
                "locations": [{"physicalLocation": _physical(f.get("location") or "")}],
            }
        )
    return {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": name,
                        "version": tool.get("version", ""),
                        "informationUri": uri,
                        "rules": rules,
                    }
                },
                "results": results,
            }
        ],
    }


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--findings", required=True)
    p.add_argument("--out", required=True)
    a = p.parse_args(argv)
    doc = to_sarif(json.loads(Path(a.findings).read_text(encoding="utf-8")))
    Path(a.out).write_text(json.dumps(doc, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
