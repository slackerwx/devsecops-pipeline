#!/usr/bin/env python3
"""Generate docs/inputs.md from the workflow_call contract of pipeline.yml (dev tool; needs PyYAML)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

WORKFLOW = Path(".github/workflows/pipeline.yml")
DOC = Path("docs/inputs.md")


def render() -> str:
    doc = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    call = (doc.get("on") or doc.get(True))[
        "workflow_call"
    ]  # PyYAML reads the bare `on:` key as boolean True
    lines = [
        "# Inputs, secrets and outputs",
        "",
        "_Generated from `.github/workflows/pipeline.yml` by `scripts/gen_inputs_doc.py` (`make inputs-doc`); do not edit by hand._",
        "",
        "## Inputs",
        "",
        "| Input | Type | Default | Description |",
        "|---|---|---|---|",
    ]
    for name, spec in call.get("inputs", {}).items():
        default = spec.get("default")
        shown = "—" if default in (None, "") else f"`{default}`"
        lines.append(
            f"| `{name}` | {spec.get('type', 'string')} | {shown} | {spec.get('description', '')} |"
        )
    lines += [
        "",
        "## Secrets (all optional)",
        "",
        "| Secret | Description |",
        "|---|---|",
    ]
    for name, spec in call.get("secrets", {}).items():
        lines.append(f"| `{name}` | {spec.get('description', '')} |")
    lines += ["", "## Outputs", "", "| Output | Description |", "|---|---|"]
    for name, spec in call.get("outputs", {}).items():
        lines.append(f"| `{name}` | {spec.get('description', '')} |")
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--write", action="store_true")
    p.add_argument("--check", action="store_true")
    a = p.parse_args(argv)
    text = render()
    if a.write:
        DOC.parent.mkdir(parents=True, exist_ok=True)
        DOC.write_text(text, encoding="utf-8")
        print(f"wrote {DOC}")
        return 0
    if a.check:
        if not DOC.is_file() or DOC.read_text(encoding="utf-8") != text:
            print(
                "docs/inputs.md is out of date — run `make inputs-doc`", file=sys.stderr
            )
            return 1
        print("docs/inputs.md is up to date")
        return 0
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
