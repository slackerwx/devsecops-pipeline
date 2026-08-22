import re
import unittest
from pathlib import Path

import yaml

# Inputs whose value the setup-* actions resolve through @actions/glob. Its Pattern
# constructor rejects a "." path segment anywhere but the first, and the pipeline hands
# every stack action "source/<working-directory>" — so gluing a filename onto that input
# produces "source/./go.sum" whenever working-directory is left at its "." default.
GLOB_INPUTS = ("cache-dependency-path", "cache-dependency-glob")

# The two shapes proven to survive that default: strip the trailing "/." off the working
# directory, or let the shell resolve it by building an absolute path from $(pwd) after
# `working-directory:` has already cd'd there.
SAFE_MARKERS = ("%/.", "$(pwd)")

_STEP_OUTPUT = re.compile(r"steps\.([A-Za-z0-9_-]+)\.outputs\.[A-Za-z0-9_-]+")

# go-version-file is deliberately not listed in GLOB_INPUTS: setup-go reads it through
# fs rather than glob, so it resolved fine even as "source/./go.mod". It takes the
# stripped value today only to keep go's two path inputs on one expression.


def _offences(doc):
    """Yield a message for every glob-resolved input that can still carry a "." segment."""
    steps = (doc.get("runs") or {}).get("steps") or []
    bodies = {s["id"]: s.get("run") or "" for s in steps if s.get("id")}
    for i, step in enumerate(steps):
        for key, value in (step.get("with") or {}).items():
            if key not in GLOB_INPUTS:
                continue
            where = f"step[{i}] `{key}`"
            value = str(value)
            if "inputs.working-directory" in value:
                yield f"{where} interpolates inputs.working-directory directly"
                continue
            for ref in _STEP_OUTPUT.findall(value):
                if ref not in bodies:
                    yield f"{where} reads step `{ref}`, which has no run body to verify"
                elif not any(marker in bodies[ref] for marker in SAFE_MARKERS):
                    yield (
                        f"{where} takes its value from step `{ref}`, whose script neither "
                        'strips the trailing "/." nor builds an absolute path from $(pwd)'
                    )


class StackGlobPathTest(unittest.TestCase):
    """Guards the bug class opened in 1.0.1 and continued in 1.0.3 and 1.0.4, where a
    consumer whose app sits at the repository root — working-directory at its "."
    default — got a glob the setup action could not resolve. The dogfood matrix cannot
    catch this: every fixture lives under tests/fixtures/<stack>, never at the root
    (#24). setup-java hard-failed the job, setup-go downgraded it to a warning and ran
    green with the module cache silently off, so a passing pipeline is not evidence
    either."""

    def test_glob_resolved_inputs_survive_a_root_working_directory(self):
        checked = 0
        for action in sorted(Path("actions").rglob("action.yml")):
            doc = yaml.safe_load(action.read_text(encoding="utf-8")) or {}
            checked += sum(
                1
                for step in (doc.get("runs") or {}).get("steps") or []
                for key in (step.get("with") or {})
                if key in GLOB_INPUTS
            )
            for offence in _offences(doc):
                self.fail(f"{action}: {offence}")
        # node, python (pip and uv), go and java each pass one; dotnet passes none. A
        # rename upstream would otherwise leave this test quietly asserting nothing.
        self.assertGreaterEqual(checked, 5, "no glob-resolved inputs found to check")

    def test_the_guard_rejects_a_working_directory_interpolated_raw(self):
        """The shape go and python/uv shipped before 1.0.4."""
        doc = yaml.safe_load(
            """
            runs:
              using: composite
              steps:
                - uses: actions/setup-go@v6
                  with:
                    cache-dependency-path: ${{ inputs.working-directory }}/go.sum
            """
        )
        self.assertTrue(list(_offences(doc)))

    def test_the_guard_rejects_an_unstripped_step_output(self):
        """The shape java shipped before 1.0.3: the glob is built in a prior step, so
        the value looks indirect, but nothing strips the trailing "/." on the way."""
        doc = yaml.safe_load(
            """
            runs:
              using: composite
              steps:
                - id: cfg
                  run: echo "deps=$WD/**/pom.xml" >> "$GITHUB_OUTPUT"
                - uses: actions/setup-java@v5
                  with:
                    cache-dependency-path: ${{ steps.cfg.outputs.deps }}
            """
        )
        self.assertTrue(list(_offences(doc)))

    def test_the_guard_accepts_both_safe_shapes(self):
        for script in ('echo "wd=${WD%/.}" >> "$GITHUB_OUTPUT"', 'dep="$(pwd)/go.sum"'):
            doc = yaml.safe_load(
                """
                runs:
                  using: composite
                  steps:
                    - id: cfg
                      run: PLACEHOLDER
                    - uses: actions/setup-go@v6
                      with:
                        cache-dependency-path: ${{ steps.cfg.outputs.wd }}
                """.replace("PLACEHOLDER", script)
            )
            self.assertEqual(list(_offences(doc)), [], script)


if __name__ == "__main__":
    unittest.main()
