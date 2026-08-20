# Usage

All examples live in [`examples/`](../examples/) and are pinned by SHA (Renovate keeps them current).
Replace `<sha>` with the commit of the release you want; the comment shows the version.

## Minimal (`examples/minimal.yml`)
Push on `main`/tags publishes `ghcr.io/<owner>/<repo>` (`sha-<sha>`, `main`, `latest`, semver on `v*`), signed keyless.
PRs build, test and scan without publishing.

## Monorepo (`examples/monorepo.yml`)
One `uses:` job per app with `working-directory`. Images default to `ghcr.io/<owner>/<repo>/<slug>`;
artifacts and PR comments are prefixed with the slug so the two calls never collide.

## Release tags, multi-arch, build args (`examples/release-tags.yml`)
`platforms: linux/amd64,linux/arm64`, `build-args: VERSION=${{ github.ref_name }}`. The scan and
DAST run on the runner arch; the multi-arch manifest is pushed after the gate.

## Custom tests (`examples/custom-tests.yml`)
Tests need Postgres/Supabase/etc.? Keep your own `test` job in the caller and pass
`skip-stages: test`; or set `test-command`/`build-command` when the default is almost right.

## External DAST (`examples/external-dast.yml`)
`dast-target-url: https://staging.example.com` scans an already deployed environment instead of an
ephemeral container. Do not point it at systems you are not allowed to scan.

## Self-hosted runners (`examples/self-hosted.yml`)
`runner: my-label`. Linux only; Docker must be available on the runner.

## Key-based signing (`examples/key-signing.yml`)
`sign: key` with `COSIGN_PRIVATE_KEY`/`COSIGN_PASSWORD` — keeps the caller's identity out of the
public Rekor log (keyless publishes the workflow identity there).

## Onboarding a noisy repo (`examples/audit-onboarding.yml`)
`mode: audit` reports everything, blocks nothing; move to `enforce` category by category via `fail-on`.

## Tool-native configuration honoured from the caller repo

| File | Tool | Purpose |
|---|---|---|
| `.gitleaks.toml`, `.gitleaksignore` | Gitleaks | rules, allowlists, per-finding ignores |
| `.semgrepignore` | Semgrep | paths to skip (input `semgrep-rulesets` overrides packs) |
| `.trivyignore`, `.trivyignore.yaml`, `trivy.yaml` | Trivy (sca, container, iac) | ignored CVEs/misconfigs — use `exp:`/`expired_at` for time-boxed acceptance |
| `.hadolint.yaml` | Hadolint | ignored rules, trusted registries |
| `.zap/rules.tsv` | ZAP baseline | per-rule WARN/IGNORE/FAIL |

## Verifying a signature

```bash
cosign verify ghcr.io/<owner>/<repo>@<digest> \
  --certificate-identity-regexp '^https://github.com/<owner>/<repo>/' \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com
cosign verify-attestation --type spdxjson ghcr.io/<owner>/<repo>@<digest> \
  --certificate-identity-regexp '^https://github.com/<owner>/<repo>/' \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com
```

`cosign-signature-format: legacy` (default) writes `.sig`/`.att` tags that Kyverno 3.8 reads;
`bundle` uses cosign's referrers format.

## Outputs for CD

`image`, `digest`, `tags`, `pushed`, `signed`, `verdict`, `failed-categories`, `evidence-artifact`,
`sbom-artifact` — chain a GitOps promotion job on `needs.devsecops.outputs.digest`.
