# ADR 0001 — One reusable workflow, logic in composite actions

Date: 2026-08-16 · Status: accepted

## Context
Reusable workflows must live flat in `.github/workflows/`. Callers should stay ~10 lines. Stages must
be organised by folder and usable à la carte.

## Decision
`pipeline.yml` only wires jobs; every stage is a composite action under `actions/`, checked out at
`job.workflow_sha` into `.pipeline/`. Composite actions never reference other local actions.

## Consequences
Two-tier API (workflow + actions); adding a stage is a folder plus a job block; per-stage reusable
workflows composed by the caller were rejected (60-line callers, cross-workflow artifact plumbing).
