# Changelog

All notable changes to this project are documented here. The format follows Keep a Changelog; the
project follows Semantic Versioning (breaking changes to inputs/outputs bump the major).

## [Unreleased]

## [1.0.1] — 2026-08-20

### Fixed
- Test-report upload no longer fails the `test` job when `working-directory` is left at its `.`
  default. The artifact globs interpolated the input directly, producing `source/./**`, which
  `actions/upload-artifact` rejects during pattern validation — before `if-no-files-found: ignore`
  can apply. The path prefix is now computed in a shell step. Only the `.` case changes; the glob is
  byte-identical for every other `working-directory`.

## [1.0.0] — 2026-08-20

### Added
- Reusable workflow `pipeline.yml`: plan, build, test, secrets (Gitleaks), sast (Semgrep CE), sca +
  licences (Trivy fs), iac (Trivy config + Hadolint), image (buildx, Trivy image scan before push,
  metadata tags, multi-arch), dast (ZAP baseline, ephemeral or external), sign (Cosign keyless/key,
  SBOM attestation), evidence (verdict, summary, PR comment, bundle, optional SARIF upload, webhook).
- Stacks: node (npm/pnpm/yarn), python (pip/uv/poetry), go, java (maven/gradle), dotnet.
- `enforce`/`audit` modes, per-category `fail-on` thresholds, tool-native config files honoured.
- Composite actions usable à la carte under `actions/`.
- Dogfood CI over five fixtures plus a vulnerable fixture asserting the audit verdict.
- Renovate config, consumer preset, OpenSSF Scorecard, immutable releases, rulesets.
