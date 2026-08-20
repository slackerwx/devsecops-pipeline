# Security model

This repository is public and executed by private repositories. It therefore holds no secrets and is
built so that neither this repo nor its dependencies can become a path into a caller.

## Threats and controls

| Threat | Control |
|---|---|
| Compromised upstream action or tool image | every `uses:` pinned to a full commit SHA (`pinact`, checked in CI); every scanner image `tag@sha256` in `config/versions.env` (`check_pins.sh`); tool versions explicit; updates only through Renovate PRs; the pipeline checks itself out at `job.workflow_sha`, so workflow and actions always come from the same commit |
| Malicious PR to this repo runs with secrets | no secrets exist here; CI uses `pull_request` (never `pull_request_target`); PR runs never push or sign; `permissions: {}` by default; `zizmor --persona pedantic` and `actionlint` gate every change |
| Moved tag / rewritten history | rulesets on `main` (PR + `ci-ok` + linear history + no force-push/delete) and on `v*` (no update/delete); immutable releases; consumers pin by SHA or immutable `vX.Y.Z`; `@main` unsupported |
| Secret leakage in logs | secrets only via `env:`; never interpolated into `run:`; Gitleaks runs with `--redact` and the generated SARIF carries no secret material; webhook payloads never include tokens |
| Pipeline code leaking into artifacts | caller code in `source/`, pipeline code in `.pipeline/`; scanners and the Docker build context only see `source/<working-directory>` |
| Registry credentials | GHCR via `GITHUB_TOKEN` by default; other registries via caller-provided secrets, used only by `docker/login-action` |
| Rekor identity disclosure (keyless) | documented; `sign: key` alternative |
| Semgrep registry packs fetched at run time | rules cannot execute code; a bad pack only degrades results; `semgrep-rulesets` can point at vendored rules |
| buildx cache poisoning | GitHub Actions caches are branch-scoped; the publishing build reads only its own ref's cache (`zizmor` finding acknowledged in `zizmor.yml`) |

## What a consumer should do

Pin by SHA and let Renovate move it (`renovate/consumer.json`); enable "require actions to be
pinned to a full-length commit SHA" in the caller's Actions policy; grant only the permissions in
`docs/permissions.md`; keep `mode: enforce` once onboarding is done.

## Reporting

See `SECURITY.md`.
