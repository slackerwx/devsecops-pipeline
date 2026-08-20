# Findings schema and gate rules

`findings.json` (in the evidence bundle) follows `scripts/schema/findings.v1.json`
(`schema: devsecops-pipeline/findings/v1`). One entry per category: `secrets`, `sast`, `sca`,
`license`, `iac`, `container`, `dast`; each with `tools`, `status` (`ok|error|skipped`), `counts`,
`findings[]`, `gate` (`pass|fail|skipped`), `threshold`, `at_or_above`.

## Severity mapping

| Tool | Mapping |
|---|---|
| Gitleaks | every leak → `critical` |
| Semgrep | ERROR → high, WARNING → medium, INFO → low |
| Trivy (vuln, misconfig) | CRITICAL/HIGH/MEDIUM/LOW → same; UNKNOWN → info |
| Trivy (licence) | Trivy's category severity (forbidden → critical … unencumbered → info) |
| Hadolint | error → high, warning → medium, info → low, style → info |
| ZAP | riskcode 3 → high, 2 → medium, 1 → low, 0 → info |

## Gate

`fail-on` = `category=threshold,…` over the defaults
`secrets=any,sast=high,sca=high,container=critical,iac=high,dast=high,license=none`. A category
fails when any finding is at or above the threshold (`any` = any finding, `none` = never). A tool
error is a failure; a skipped stage never fails. `enforce` fails the stage's job; `audit` reports
and sets `verdict=fail`. Risk acceptance only through the tools' ignore files (see `docs/usage.md`).
