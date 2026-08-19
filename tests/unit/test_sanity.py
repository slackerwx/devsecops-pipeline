import unittest
from pathlib import Path

import yaml


def _run_scripts(action: Path):
    """Yield (step name, run script) for every step of a composite action."""
    doc = yaml.safe_load(action.read_text(encoding="utf-8")) or {}
    for i, step in enumerate(doc.get("runs", {}).get("steps", []) or []):
        run = step.get("run")
        if run:
            yield step.get("id") or step.get("name") or f"step[{i}]", run


class SanityTest(unittest.TestCase):
    def test_versions_env_has_no_placeholders(self):
        text = Path("config/versions.env").read_text()
        self.assertNotIn("<tag>", text)
        self.assertNotIn("<version>", text)

    def test_steps_that_capture_an_exit_code_drop_errexit_first(self):
        """`shell: bash` runs with errexit, so a step that means to inspect a non-zero
        exit code has to `set +e` first or it dies before ever reading `rc`. Missing
        this in the gate action is what made audit mode fail the job like enforce."""
        for action in sorted(Path("actions").rglob("action.yml")):
            for name, script in _run_scripts(action):
                if "rc=$?" not in script:
                    continue
                before = script[: script.index("rc=$?")]
                self.assertIn(
                    "set +e",
                    before,
                    f"{action}: step `{name}` captures rc=$? without dropping errexit first",
                )


if __name__ == "__main__":
    unittest.main()
