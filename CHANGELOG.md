# Changelog

All notable changes to this project are documented here. The format follows Keep a Changelog; the
project follows Semantic Versioning (breaking changes to inputs/outputs bump the major).

## [Unreleased]

## [1.0.3] — 2026-08-21

### Fixed
- The `java` stack no longer fails the `build` and `test` jobs when `working-directory` is left at
  its `.` default. `actions/setup-java` resolves `cache-dependency-path` through `@actions/glob`,
  which rejects a `.` path segment anywhere but the first, and the pipeline hands the stack action
  `source/<working-directory>` — so the default produced `source/./**/pom.xml` (or
  `source/./**/*.gradle*` on gradle) and the step errored out before anything was built. The
  trailing `/.` is now stripped before the globs are built, covering both package managers. Only the
  `.` case changes; the globs are byte-identical for every other `working-directory`. Same bug class
  as 1.0.1's test-report upload fix, which missed this instance.

## [1.0.2] — 2026-08-20

### Fixed
- `cosign-signature-format: legacy` again produces a `sha256-<digest>.sig` tag instead of a Sigstore
  bundle. The sign action chose its legacy flags by grepping `cosign <cmd> --help`, but cosign v3.1.1
  marked `--new-bundle-format` deprecated and cobra hides deprecated flags from `--help` while still
  honouring them. The probe silently stopped passing the flag, so cosign fell back to its
  new-bundle-format default and consumers doing tag-based signature discovery found nothing. The
  probe now asks cosign to parse each flag rather than reading help text. `COSIGN_VERSION` is
  unchanged at `v3.1.3`; only the detection was wrong.

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
