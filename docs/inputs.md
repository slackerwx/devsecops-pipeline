# Inputs, secrets and outputs

_Generated from `.github/workflows/pipeline.yml` by `scripts/gen_inputs_doc.py` (`make inputs-doc`); do not edit by hand._

## Inputs

| Input | Type | Default | Description |
|---|---|---|---|
| `stack` | string | `auto` | auto | node | python | go | java | dotnet |
| `working-directory` | string | `.` | App root inside the repository |
| `mode` | string | `enforce` | enforce | audit |
| `runner` | string | `ubuntu-latest` | runs-on label |
| `toolchain-version` | string | — | Overrides the detected toolchain version |
| `build-command` | string | — |  |
| `test-command` | string | — |  |
| `skip-stages` | string | — | Comma list of build,test,secrets,sast,sca,iac,image,dast,sign |
| `dockerfile` | string | `Dockerfile` |  |
| `image-name` | string | — | Defaults to <registry>/<owner>/<repo>[/<slug>] |
| `registry` | string | `ghcr.io` |  |
| `platforms` | string | `linux/amd64` |  |
| `push` | string | `auto` | auto | always | never |
| `build-args` | string | — | Multiline KEY=VALUE |
| `app-port` | string | — | Enables ephemeral DAST against the candidate image |
| `app-health-path` | string | `/` |  |
| `app-env` | string | — | Multiline KEY=VALUE for the ephemeral container (non-secret) |
| `dast-target-url` | string | — |  |
| `fail-on` | string | `secrets=any,sast=high,sca=high,container=critical,iac=high,dast=high,license=none` | Per-category thresholds |
| `ignore-unfixed` | boolean | `True` |  |
| `gitleaks-config` | string | — | Gitleaks config for the secrets stage, relative to the repository root; empty = Gitleaks defaults |
| `semgrep-rulesets` | string | — | Comma list of p/ packs or paths; empty = pipeline defaults + stack pack |
| `sign` | string | `keyless` | keyless | key | none |
| `cosign-signature-format` | string | `legacy` | legacy | bundle |
| `pr-comment` | boolean | `True` |  |
| `upload-sarif` | boolean | `False` |  |
| `evidence-retention-days` | number | `30` |  |

## Secrets (all optional)

| Secret | Description |
|---|---|
| `REGISTRY_USERNAME` | Registry user when not GHCR with GITHUB_TOKEN (Zot, Harbor, Docker Hub) |
| `REGISTRY_PASSWORD` | Registry password/token paired with REGISTRY_USERNAME |
| `COSIGN_PRIVATE_KEY` | PEM private key for sign=key |
| `COSIGN_PASSWORD` | Password of COSIGN_PRIVATE_KEY |
| `EVIDENCE_WEBHOOK_URL` | Base URL of the evidence webhook; presence enables it (see docs/evidence-webhook.md) |
| `EVIDENCE_WEBHOOK_TOKEN` | Bearer token for the evidence webhook |

## Outputs

| Output | Description |
|---|---|
| `image` | Image repository (no tag) |
| `digest` |  |
| `tags` | Newline-separated tags |
| `pushed` |  |
| `signed` |  |
| `verdict` | pass | fail |
| `failed-categories` |  |
| `evidence-artifact` |  |
| `sbom-artifact` |  |
