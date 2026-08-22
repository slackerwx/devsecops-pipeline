# Changelog

All notable changes to this project are documented here. The format follows Keep a Changelog; the
project follows Semantic Versioning (breaking changes to inputs/outputs bump the major).

## [Unreleased]

### Added
- A unit guard (`tests/unit/test_stack_globs.py`) over the bug class that produced 1.0.1, 1.0.3 and
  1.0.4: every input the setup actions resolve through `@actions/glob` must derive its path either
  from a working directory with the trailing `/.` stripped, or from an absolute `$(pwd)` built after
  the `cd`. Interpolating `working-directory` straight into such an input now fails `make unit`.
  Verified to catch all three historical regressions by running it against the pre-fix `action.yml`
  of each (`6ab018b^` java, `343818d^` go and python/uv), and to pass on all three fixes.

  This closes #24 differently from the fix that issue suggested. A dogfood job at the repository
  root is not reachable here — `pipeline.yml` checks the repo out itself, so `working-directory: .`
  means this repo's own root, which would have to carry a real app — and the issue's own suggestion
  of extending the node job would have caught none of the three: node builds its cache path from
  `$(pwd)` and is structurally immune. One dogfood job also covers one stack, whereas the three bugs
  landed in three different ones. The guard covers all five at `make unit` speed. `go-version-file`
  is deliberately excluded: `setup-go` reads it through `fs`, not glob, so it was never affected.

## [1.0.4] — 2026-08-21

### Fixed
- The `go` stack again caches Go modules when `working-directory` is left at its `.` default.
  `actions/setup-go` resolves `cache-dependency-path` through `@actions/glob`, which rejects a `.`
  path segment anywhere but the first, and the pipeline hands the stack action
  `source/<working-directory>` — so the default produced `source/./go.sum`. Unlike 1.0.3's `java`
  case, `setup-go` catches the rejection and downgrades it to `##[warning]Restore cache failed`, so
  affected runs stayed green while silently re-downloading every module on every `build` and `test`
  job. The trailing `/.` is now stripped before the path is built. `go-version-file` takes the same
  stripped value for consistency; it resolves through `fs` rather than glob, so it was never broken
  and is unaffected in behaviour.
- The `python` stack's `uv` branch no longer builds an invalid `cache-dependency-glob` when
  `working-directory` is left at its `.` default, for the same reason — `astral-sh/setup-uv`
  received `source/./uv.lock`. Same one-line strip.
- Both paths are byte-identical for every non-root `working-directory`; only the `.` case changes.
  The `pip` and `poetry` branches were never affected — they build absolute paths from `$(pwd)` —
  and `node` and `dotnet` pass no such glob at all. Closes the bug class opened in 1.0.1 and
  continued in 1.0.3 (`#22`).

  Verification note, stated plainly: the `go` fix is confirmed by a real root-level consumer run
  (`slackerwx/virtualab-sample-go`), where the module cache now saves and restores instead of
  warning. The `uv` fix ships unexercised by any real run — no dogfood fixture and no sample repo
  uses `uv`, so it rests on being the identical mechanical change applied to structurally identical
  code. The dogfood matrix cannot cover either case: its fixtures all live under
  `tests/fixtures/<stack>`, never at the repository root, and the `go` fixture additionally ships no
  `go.sum`, so `setup-go` caching is switched off there entirely.

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
