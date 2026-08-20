# ADR 0004 — A small evidence webhook instead of a vendor integration

Date: 2026-08-16 · Status: accepted

## Context
Private repos on free plans cannot upload to Code Scanning; VirtuaLab already ingests SARIF and
custody events.

## Decision
Optional `EVIDENCE_WEBHOOK_URL/TOKEN`: SARIF per scanner to `<base>/sarif`, four event types to
`<base>/event`, best-effort, never failing a job. VirtuaLab is the reference consumer.

## Consequences
DefectDojo/SonarQube stay separate future integrations; the contract is documented in
`docs/evidence-webhook.md` and versioned with the pipeline.
