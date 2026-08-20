# ADR 0002 — Scanners as digest-pinned images; toolchains as SHA-pinned official actions

Date: 2026-08-16 · Status: accepted

## Context
Every tool is a supply-chain dependency executed inside private repositories.

## Decision
Scanners run from `config/versions.env` images (`tag@sha256`), Renovate-managed. Toolchains use
official `actions/setup-*`, Docker and Sigstore actions pinned by SHA. Exceptions: Semgrep from PyPI
(`pipx install semgrep==X`; no GHCR image, Docker Hub rate limits) and Cosign via
`sigstore/cosign-installer` (verifies its binary).

## Consequences
Uniform, verifiable tool identity; one file to bump. A golden "toolbox" image (single root of
trust, identical local/CI runs) stays a future option: the `docker run` lines are the seam.
