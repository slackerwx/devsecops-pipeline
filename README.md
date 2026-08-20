# devsecops-pipeline

[![ci](https://github.com/slackerwx/devsecops-pipeline/actions/workflows/ci.yml/badge.svg)](https://github.com/slackerwx/devsecops-pipeline/actions/workflows/ci.yml)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/slackerwx/devsecops-pipeline/badge)](https://scorecard.dev/viewer/?uri=github.com/slackerwx/devsecops-pipeline)
[![release](https://img.shields.io/github/v/release/slackerwx/devsecops-pipeline?sort=semver)](https://github.com/slackerwx/devsecops-pipeline/releases)

A reusable DevSecOps pipeline for GitHub Actions. One `uses:` line gives a repository — Node,
Python, Go, Java or .NET — build, tests, secret scanning, SAST, dependency and licence scanning,
IaC scanning, a container image that is scanned **before** it is pushed, an SBOM, a Cosign
signature that only exists when every gate passed, DAST against the running candidate, and an
evidence bundle. Private repositories on the free plan get the whole thing: results go to the job
summary, a PR comment, artifacts and (optionally) a webhook — nothing depends on paid GitHub features.

## 60-second start

```yaml
# .github/workflows/pipeline.yml in your repository
name: pipeline
on:
  push:
    branches: [main]
    tags: ["v*"]
  pull_request:
permissions:
  contents: read
  packages: write
  id-token: write
  pull-requests: write
jobs:
  devsecops:
    uses: slackerwx/devsecops-pipeline/.github/workflows/pipeline.yml@<sha>  # vX.Y.Z
    with:
      app-port: "3000"   # enables DAST against your image; drop it if the app is not an HTTP service
```

Pin the workflow to a commit SHA (Renovate keeps it fresh: extend
`github>slackerwx/devsecops-pipeline//renovate/consumer`). `@main` is unsupported.

## What runs

```
plan ─┬─ build ── test ──────────────────────┐
      ├─ secrets  (gitleaks)                 │
      ├─ sast     (semgrep)                  ├─► image (build → trivy → push) ─► dast (zap) ─► sign (cosign + sbom attest)
      ├─ sca      (trivy fs: vulns + licences)│                                                     │
      └─ iac      (trivy config + hadolint) ──┘                                        evidence (always) ◄┘
```

- **enforce** (default): a category above its threshold fails its job; no image is pushed, nothing is signed.
- **audit**: every job stays green, the verdict is advisory — the onboarding mode.
- Thresholds: `fail-on: secrets=any,sast=high,sca=high,container=critical,iac=high,dast=high,license=none`.
- Publish policy: `push: auto` pushes on the default branch and `v*` tags, never on PRs.

Full contract: [docs/inputs.md](docs/inputs.md) · scenarios: [docs/usage.md](docs/usage.md) ·
permissions per feature: [docs/permissions.md](docs/permissions.md).

## Building blocks

Every stage is a composite action you can use on its own, e.g.
`uses: slackerwx/devsecops-pipeline/actions/security/sast/semgrep@<sha>`. See `actions/`.

## Trust

Every action pinned to a commit SHA, every scanner image pinned to a digest, no secrets in this
repository, PR runs never publish, rulesets + immutable releases, OpenSSF Scorecard. Details and
threat model: [docs/security-model.md](docs/security-model.md).

## Extending

[Adding a stack](docs/extending/adding-a-stack.md) · [Adding a scanner](docs/extending/adding-a-scanner.md) · [ADRs](docs/adr/).

## Roadmap

SonarQube stage, DefectDojo import, Nuclei, TruffleHog verification, CodeQL (opt-in), Helm chart
stage, SLSA provenance, harden-runner, golden toolbox image, VEX.

Licence: Apache-2.0.
