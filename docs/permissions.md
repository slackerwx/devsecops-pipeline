# Permissions the caller must grant

A reusable workflow can only narrow what the caller grants. `pipeline.yml` declares `permissions: {}`
at the top and the minimum per job.

| Feature | Permission on the caller job |
|---|---|
| everything | `contents: read` |
| pushing images (`push` resolves to true) | `packages: write` |
| keyless signing (`sign: keyless`) | `id-token: write` |
| sticky PR comment (`pr-comment: true`) | `pull-requests: write` (skipped silently without it, e.g. fork PRs) |
| `upload-sarif: true` (Code Scanning; public repos or GHAS) | `security-events: write` |

Per job inside the pipeline: `plan/build/test/secrets/sast/sca/iac` → `contents: read`; `image` →
`+ packages: write`; `dast` → `+ packages: read`; `sign` → `+ packages: write, id-token: write`;
`evidence` → `+ pull-requests: write, security-events: write`.
