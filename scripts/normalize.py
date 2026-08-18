#!/usr/bin/env python3
"""Normalize scanner output into the pipeline's findings format (one category per file)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SEVERITIES = ("critical", "high", "medium", "low", "info")
TOOL_NAME = {
    "gitleaks": "gitleaks",
    "semgrep": "semgrep",
    "trivy-vuln": "trivy",
    "trivy-license": "trivy",
    "trivy-misconfig": "trivy",
    "hadolint": "hadolint",
    "zap": "zap",
}


def _sev(value, default: str = "info") -> str:
    v = str(value or "").lower()
    return v if v in SEVERITIES else default


def finding(**kw) -> dict:
    base = {
        "id": "",
        "title": "",
        "severity": "info",
        "location": "",
        "package": "",
        "installed": "",
        "fixed": "",
        "url": "",
        "tool": "",
    }
    base.update(kw)
    base["severity"] = _sev(base["severity"])
    base["title"] = str(base["title"])[:300]
    return base


def gitleaks(data) -> list[dict]:
    return [
        finding(
            id=item.get("RuleID", "secret"),
            title=item.get("Description", "Secret detected"),
            severity="critical",
            location=f"{item.get('File', '')}:{item.get('StartLine', '')}",
            url="https://github.com/gitleaks/gitleaks#rules",
            tool="gitleaks",
        )
        for item in (data or [])
    ]


SEMGREP_SEV = {"ERROR": "high", "WARNING": "medium", "INFO": "low"}


def semgrep(data) -> list[dict]:
    out = []
    for r in (data or {}).get("results", []) or []:
        extra = r.get("extra", {}) or {}
        meta = extra.get("metadata", {}) or {}
        out.append(
            finding(
                id=r.get("check_id", ""),
                title=extra.get("message", ""),
                severity=SEMGREP_SEV.get(str(extra.get("severity", "")).upper(), "low"),
                location=f"{r.get('path', '')}:{(r.get('start') or {}).get('line', '')}",
                url=meta.get("source", "") or meta.get("shortlink", ""),
                tool="semgrep",
            )
        )
    return out


def _trivy_results(data):
    return (data or {}).get("Results") or []


def trivy_vuln(data) -> list[dict]:
    out = []
    for res in _trivy_results(data):
        for v in res.get("Vulnerabilities") or []:
            out.append(
                finding(
                    id=v.get("VulnerabilityID", ""),
                    title=v.get("Title") or v.get("VulnerabilityID", ""),
                    severity=_sev(v.get("Severity")),
                    location=res.get("Target", ""),
                    package=v.get("PkgName", ""),
                    installed=v.get("InstalledVersion", ""),
                    fixed=v.get("FixedVersion", ""),
                    url=v.get("PrimaryURL", ""),
                    tool="trivy",
                )
            )
    return out


def trivy_license(data) -> list[dict]:
    out = []
    for res in _trivy_results(data):
        for lic in res.get("Licenses") or []:
            out.append(
                finding(
                    id=lic.get("Name", ""),
                    title=f"{lic.get('Category', '')} licence {lic.get('Name', '')}".strip(),
                    severity=_sev(lic.get("Severity")),
                    location=lic.get("FilePath") or res.get("Target", ""),
                    package=lic.get("PkgName", ""),
                    url=lic.get("Link", ""),
                    tool="trivy",
                )
            )
    return out


def trivy_misconfig(data) -> list[dict]:
    out = []
    for res in _trivy_results(data):
        for m in res.get("Misconfigurations") or []:
            line = (m.get("CauseMetadata") or {}).get("StartLine", "")
            out.append(
                finding(
                    id=m.get("ID", ""),
                    title=m.get("Title", ""),
                    severity=_sev(m.get("Severity")),
                    location=f"{res.get('Target', '')}:{line}",
                    url=m.get("PrimaryURL", ""),
                    tool="trivy",
                )
            )
    return out


HADOLINT_SEV = {"error": "high", "warning": "medium", "info": "low", "style": "info"}


def hadolint(data) -> list[dict]:
    out = []
    for item in data or []:
        code = str(item.get("code", ""))
        url = (
            f"https://github.com/hadolint/hadolint/wiki/{code}"
            if code.startswith("DL")
            else f"https://www.shellcheck.net/wiki/{code}"
        )
        out.append(
            finding(
                id=code,
                title=item.get("message", ""),
                severity=HADOLINT_SEV.get(str(item.get("level", "")).lower(), "info"),
                location=f"{item.get('file', 'Dockerfile')}:{item.get('line', '')}",
                url=url,
                tool="hadolint",
            )
        )
    return out


ZAP_SEV = {3: "high", 2: "medium", 1: "low", 0: "info"}


def zap(data) -> list[dict]:
    out = []
    for site in (data or {}).get("site", []) or []:
        for a in site.get("alerts", []) or []:
            try:
                risk = int(a.get("riskcode", 0))
            except (TypeError, ValueError):
                risk = 0
            instances = a.get("instances") or [{}]
            out.append(
                finding(
                    id=str(a.get("pluginid", "")),
                    title=a.get("name") or a.get("alert", ""),
                    severity=ZAP_SEV.get(risk, "info"),
                    location=instances[0].get("uri", ""),
                    url=str(a.get("reference", "")).split("\n")[0],
                    tool="zap",
                )
            )
    return out


PARSERS = {
    "gitleaks": gitleaks,
    "semgrep": semgrep,
    "trivy-vuln": trivy_vuln,
    "trivy-license": trivy_license,
    "trivy-misconfig": trivy_misconfig,
    "hadolint": hadolint,
    "zap": zap,
}


def counts(findings: list[dict]) -> dict:
    c = {s: 0 for s in SEVERITIES}
    for f in findings:
        c[f["severity"]] += 1
    return c


def build(
    category: str,
    tool: str,
    version: str,
    status: str,
    reason: str,
    findings: list[dict],
    existing: dict | None = None,
) -> dict:
    doc = existing or {
        "category": category,
        "tools": [],
        "status": "ok",
        "reason": "",
        "counts": {},
        "findings": [],
    }
    name = TOOL_NAME[tool]
    if not any(t["name"] == name for t in doc["tools"]):
        doc["tools"].append({"name": name, "version": version})
    doc["findings"].extend(findings)
    if status == "error" or doc["status"] == "error":
        doc["status"] = "error"
        doc["reason"] = " ".join(
            x for x in (doc.get("reason", ""), reason) if x
        ).strip()
    elif status == "skipped" and not doc["findings"]:
        doc["status"] = "skipped"
        doc["reason"] = reason
    doc["counts"] = counts(doc["findings"])
    return doc


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--tool", required=True, choices=sorted(PARSERS))
    p.add_argument(
        "--input",
        required=True,
        help="tool JSON output; unreadable file => status error",
    )
    p.add_argument("--category", required=True)
    p.add_argument("--tool-version", default="")
    p.add_argument("--status", default="ok", choices=("ok", "error", "skipped"))
    p.add_argument("--reason", default="")
    p.add_argument("--out", required=True)
    p.add_argument(
        "--append", action="store_true", help="merge into an existing --out file"
    )
    a = p.parse_args(argv)

    findings, status, reason = [], a.status, a.reason
    if status == "ok":
        try:
            with open(a.input, encoding="utf-8") as fh:
                findings = PARSERS[a.tool](json.load(fh))
        except (OSError, json.JSONDecodeError) as exc:
            status, reason = "error", f"{a.tool}: cannot read {a.input}: {exc}"

    out = Path(a.out)
    existing = (
        json.loads(out.read_text(encoding="utf-8"))
        if a.append and out.is_file()
        else None
    )
    doc = build(a.category, a.tool, a.tool_version, status, reason, findings, existing)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    c = doc["counts"]
    print(
        f"{a.category}: {len(doc['findings'])} finding(s) critical={c['critical']} high={c['high']} medium={c['medium']} low={c['low']} info={c['info']} status={doc['status']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
