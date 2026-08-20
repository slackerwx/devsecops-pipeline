# ADR 0003 — Fail-fast gates per stage; the signature means "passed everything"

Date: 2026-08-16 · Status: accepted

## Context
Publishing then blocking leaves vulnerable images in the registry; a single final gate would sign
before knowing the verdict.

## Decision
Each scan job evaluates its category threshold (`enforce` fails the job, `audit` warns); the image
is scanned before push; `sign` runs after `dast`; `evidence` always consolidates and reports.

## Consequences
In `enforce`, nothing vulnerable reaches the registry and an unsigned image is a failed pipeline
(pairs with Kyverno `verifyImages`); developers see all parallel verdicts in one run.
