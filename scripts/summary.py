#!/usr/bin/env python3
"""Render findings.json as markdown for the job summary or the PR comment."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ORDER = ("secrets", "sast", "sca", "license", "iac", "container", "dast")
ICON = {"pass": "✅", "fail": "❌", "skipped": "⏭️"}
SEV_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
LIMIT = {"summary": 900_000, "comment": 60_000}


def esc(value) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def render(
    doc: dict, extra: dict, fmt: str, max_per_category: int, marker: str = ""
) -> str:
    run = doc.get("run", {})
    verdict = doc.get("verdict", "pass")
    lines = [marker] if marker else []
    title = f"DevSecOps pipeline — `{run.get('working_directory', '.')}` ({run.get('stack', '?')})"
    lines.append(("## " if fmt == "summary" else "### ") + title)
    advisory = " (audit mode — advisory)" if run.get("mode") == "audit" else ""
    lines.append(
        f"Verdict: {ICON.get(verdict, '')} **{verdict.upper()}**{advisory} · commit `{str(run.get('sha', ''))[:7]}`"
    )
    if doc.get("failed_categories"):
        lines.append(
            "Failed categories: "
            + ", ".join(f"`{c}`" for c in doc["failed_categories"])
        )
    lines += [
        "",
        "| Category | Tools | Status | Threshold | ≥ threshold | Crit | High | Med | Low | Gate |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for cat in ORDER:
        c = doc.get("categories", {}).get(cat)
        if not c:
            continue
        n = c.get("counts", {})
        tools = (
            ", ".join(
                f"{t['name']} {t.get('version', '')}".strip()
                for t in c.get("tools", [])
            )
            or "—"
        )
        status = c.get("status", "ok") + (
            f" ({esc(c['reason'])})" if c.get("reason") else ""
        )
        lines.append(
            f"| {cat} | {tools} | {status} | {c.get('threshold', '')} | {c.get('at_or_above', 0)} | {n.get('critical', 0)} | {n.get('high', 0)} | "
            f"{n.get('medium', 0)} | {n.get('low', 0)} | {ICON.get(c.get('gate', ''), '')} {c.get('gate', '')} |"
        )
    image = extra.get("image")
    if image:
        line = f"Image: `{image.get('image', '')}`"
        if image.get("digest"):
            line += f" @ `{image['digest']}`"
        line += f" · pushed: {str(image.get('pushed', False)).lower()}"
        if image.get("tags"):
            line += " · tags: " + ", ".join(f"`{t}`" for t in image["tags"])
        lines += ["", line]
    sign = extra.get("sign")
    if sign:
        lines.append(
            f"Signature: signed ({sign.get('mode', '')}, {sign.get('format', '')})"
            if sign.get("signed")
            else f"Signature: not signed — {sign.get('reason', '')}"
        )
    sbom = extra.get("sbom")
    if sbom:
        lines.append(
            f"SBOM: {sbom.get('packages', '?')} packages ({sbom.get('format', 'spdx-json')})"
        )
    for cat in ORDER:
        c = doc.get("categories", {}).get(cat)
        if not c or not c.get("findings"):
            continue
        fs = sorted(
            c["findings"],
            key=lambda f: (
                SEV_ORDER.get(f.get("severity", "info"), 9),
                f.get("id", ""),
            ),
        )
        shown = fs[:max_per_category]
        more = f" — showing {len(shown)}" if len(shown) < len(fs) else ""
        lines += [
            "",
            f"<details><summary>{cat}: {len(fs)} finding(s){more}</summary>",
            "",
            "| Severity | Id | Location | Package | Fixed | Title |",
            "|---|---|---|---|---|---|",
        ]
        for f in shown:
            ident = (
                f"[{esc(f.get('id', ''))}]({f['url']})"
                if f.get("url")
                else esc(f.get("id", ""))
            )
            pkg = esc(f.get("package", "")) + (
                f"@{esc(f['installed'])}" if f.get("installed") else ""
            )
            lines.append(
                f"| {f.get('severity', '')} | {ident} | `{esc(f.get('location', ''))}` | {pkg} | {esc(f.get('fixed', ''))} | {esc(f.get('title', ''))} |"
            )
        lines += ["", "</details>"]
    text = "\n".join(lines) + "\n"
    if len(text) > LIMIT[fmt]:
        text = text[: LIMIT[fmt]] + "\n\n_(truncated)_\n"
    return text


def load_extra(directory: str) -> dict:
    extra = {}
    if not directory:
        return extra
    for name in ("image", "sign", "sbom"):
        for path in Path(directory).rglob(f"{name}.json"):
            try:
                extra[name] = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            break
    return extra


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--findings", required=True)
    p.add_argument("--format", choices=("summary", "comment"), default="summary")
    p.add_argument("--extra-dir", default="")
    p.add_argument("--max-per-category", type=int, default=15)
    p.add_argument("--marker", default="")
    a = p.parse_args(argv)
    doc = json.loads(Path(a.findings).read_text(encoding="utf-8"))
    sys.stdout.write(
        render(doc, load_extra(a.extra_dir), a.format, a.max_per_category, a.marker)
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
