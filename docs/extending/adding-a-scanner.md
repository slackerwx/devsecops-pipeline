# Adding a scanner

1. Pin it: image `NAME_IMAGE=registry/image:tag` in `config/versions.env`, then `make resolve-pins`
   (or a `*_VERSION` line with a `# renovate:` comment for non-image tools).
2. `actions/security/<category>/<tool>/action.yml`: run the tool from the pinned image, write
   `<tool>.json` (+ native SARIF when it exists) under `$RUNNER_TEMP/devsecops/<category>/`, honour
   the tool's config file from the caller repo, call `scripts/normalize.py --tool <tool>` and, if
   there is no native SARIF, `scripts/sarif.py`. Outputs: `findings`, `sarif`, `output-dir`.
3. `scripts/normalize.py`: a parser + severity map; a sample output in `tests/samples/<tool>.json`;
   tests in `tests/unit/test_normalize.py`. New category? add it to `gate.CATEGORIES`,
   `gate.STAGE_OF`, `DEFAULT_FAIL_ON`, `summary.ORDER`, `sarif.DRIVER`, `docs/findings-schema.md`.
4. `.github/workflows/pipeline.yml`: a job (or a step in the category's job) following the pattern
   checkout → scan → upload `devsecops-<slug>-<category>` → webhook sarif → gate.
5. If it needs a new external action, add an ADR and the action to the allowed list in
   `docs/security-model.md`.
6. Docs (`README.md` diagram, `docs/usage.md` config-file table), `make lint unit`, PR.
