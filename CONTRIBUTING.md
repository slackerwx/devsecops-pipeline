# Contributing

- `make venv` once, then `make lint unit` before every commit.
- Every third-party action is pinned to a commit SHA (`make pinact` rewrites `uses:` lines);
  every image in `config/versions.env` is `tag@sha256`. Renovate opens the bump PRs.
- New scanner or stack: follow `docs/extending/`.
- Integration tests are the dogfood matrix in `.github/workflows/ci.yml`; they run on your PR.
