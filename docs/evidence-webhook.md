# Evidence webhook

Optional. Enabled when the caller passes `EVIDENCE_WEBHOOK_URL` (base URL) and
`EVIDENCE_WEBHOOK_TOKEN`. Every request: `POST`, `Authorization: Bearer <token>`,
`Content-Type: application/json`, 30 s timeout, two retries on 5xx/network errors, no retry on 4xx.
Failures are logged as warnings and never fail a job.

| Endpoint | When | Body |
|---|---|---|
| `POST <base>/sarif` | after each scanner (secrets, sast, sca, iac ×2, container, dast) | the SARIF 2.1.0 document |
| `POST <base>/event` | image pushed | `{"type":"image.pushed","payload":{"image":"<repo>:sha-<sha>","digest":"sha256:…"}}` |
| `POST <base>/event` | SBOM created | `{"type":"sbom.created","payload":{"packages":123,"format":"spdx-json"}}` |
| `POST <base>/event` | image signed | `{"type":"image.signed","payload":{"digest":"sha256:…","issuer":"https://token.actions.githubusercontent.com"}}` |
| `POST <base>/event` | pipeline finished | `{"type":"pipeline.completed","payload":{"verdict":"pass|fail","mode":"enforce|audit","failedCategories":["sca"]}}` |

Reference consumer: VirtuaLab (`/api/ingest/sarif`, `/api/ingest/event`); an unknown event type
answered with 400 is tolerated.
