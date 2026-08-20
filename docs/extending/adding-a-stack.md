# Adding a stack

1. `actions/stacks/<stack>/action.yml` with the shared contract: inputs `working-directory`,
   `version`, `package-manager`, `phase` (`setup|build|test`), `command`; setup uses the official
   `actions/setup-*` action pinned by SHA; `phase: build` and `phase: test` steps honour `command`.
2. `scripts/detect.py`: detection rule in `detect_stack`, package manager in `package_manager`,
   version sources in `toolchain_version`, default in `DEFAULT_VERSION`; unit tests in
   `tests/unit/test_detect.py`.
3. `tests/fixtures/<stack>/`: an HTTP app answering `/health`, one unit test, a clean Dockerfile
   (non-root `USER`, pinned base tag), `.dockerignore`.
4. `.github/workflows/pipeline.yml`: one conditional step in `build` and one in `test`
   (`if: needs.plan.outputs.stack == '<stack>'`).
5. Semgrep pack: add the language pack to the `case` in `actions/security/sast/semgrep/action.yml`.
6. `.github/workflows/ci.yml`: add the fixture to the dogfood matrix with its port.
7. `docs/usage.md` and `README.md`: mention the stack. `make lint unit` green, PR.
