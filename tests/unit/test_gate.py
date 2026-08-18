import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import gate, normalize

SAMPLES = Path("tests/samples")


def partial(category, tool, sample):
    return normalize.build(
        category,
        tool,
        "x",
        "ok",
        "",
        normalize.PARSERS[tool](json.loads((SAMPLES / sample).read_text())),
    )


class ThresholdTest(unittest.TestCase):
    def test_defaults_and_overrides(self):
        t = gate.parse_fail_on("")
        self.assertEqual(t["sca"], "high")
        self.assertEqual(t["license"], "none")
        t = gate.parse_fail_on("sca=critical, dast=none")
        self.assertEqual(t["sca"], "critical")
        self.assertEqual(t["dast"], "none")
        self.assertEqual(t["sast"], "high")

    def test_bad_specs(self):
        for bad in ("sca", "nope=high", "sca=huge"):
            with self.assertRaises(SystemExit):
                gate.parse_fail_on(bad)

    def test_evaluate(self):
        sca = partial("sca", "trivy-vuln", "trivy-fs.json")
        self.assertEqual(gate.evaluate(sca, "critical"), ("fail", 1))
        self.assertEqual(gate.evaluate(sca, "high"), ("fail", 2))
        self.assertEqual(gate.evaluate(sca, "none"), ("pass", 0))
        self.assertEqual(gate.evaluate(sca, "any"), ("fail", 3))
        clean = normalize.build("sast", "semgrep", "x", "ok", "", [])
        self.assertEqual(gate.evaluate(clean, "any"), ("pass", 0))
        self.assertEqual(
            gate.evaluate({"status": "skipped", "findings": []}, "any"), ("skipped", 0)
        )
        self.assertEqual(
            gate.evaluate({"status": "error", "findings": []}, "none"), ("fail", 0)
        )


class CliTest(unittest.TestCase):
    def test_category_exit_codes(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "findings-sca.json"
            p.write_text(json.dumps(partial("sca", "trivy-vuln", "trivy-fs.json")))
            self.assertEqual(
                gate.main(
                    ["category", "--findings", str(p), "--fail-on", "sca=critical"]
                ),
                1,
            )
            self.assertEqual(
                gate.main(["category", "--findings", str(p), "--fail-on", "sca=none"]),
                0,
            )
            self.assertEqual(json.loads(p.read_text())["gate"], "pass")

    def test_all_merges_and_fills_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "evidence"
            (d / "a").mkdir(parents=True)
            (d / "a" / "findings-sca.json").write_text(
                json.dumps(partial("sca", "trivy-vuln", "trivy-fs.json"))
            )
            (d / "b").mkdir()
            (d / "b" / "findings-secrets.json").write_text(
                json.dumps(normalize.build("secrets", "gitleaks", "x", "ok", "", []))
            )
            out = Path(tmp) / "findings.json"
            env = {
                "GITHUB_REPOSITORY": "acme/app",
                "GITHUB_SHA": "abc",
                "GITHUB_REF": "refs/heads/main",
                "GITHUB_RUN_ID": "42",
            }
            with mock.patch.dict(os.environ, env):
                rc = gate.main(
                    [
                        "all",
                        "--dir",
                        str(d),
                        "--out",
                        str(out),
                        "--mode",
                        "audit",
                        "--stack",
                        "node",
                        "--stages",
                        json.dumps({"iac": False, "dast": False, "image": True}),
                    ]
                )
            self.assertEqual(rc, 0)
            doc = json.loads(out.read_text())
            self.assertEqual(doc["schema"], "devsecops-pipeline/findings/v1")
            self.assertEqual(doc["verdict"], "fail")
            self.assertEqual(doc["failed_categories"], ["sca"])
            self.assertEqual(doc["categories"]["secrets"]["gate"], "pass")
            self.assertEqual(doc["categories"]["iac"]["status"], "skipped")
            self.assertEqual(doc["categories"]["iac"]["reason"], "stage disabled")
            self.assertEqual(
                doc["categories"]["container"]["reason"],
                "no results produced (stage did not run)",
            )
            self.assertEqual(doc["run"]["run_id"], 42)
            self.assertEqual(doc["run"]["mode"], "audit")


class SchemaTest(unittest.TestCase):
    def test_full_document_matches_schema(self):
        try:
            import jsonschema
        except ImportError:
            self.skipTest("jsonschema not installed")
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "ev"
            d.mkdir()
            (d / "findings-sca.json").write_text(
                json.dumps(partial("sca", "trivy-vuln", "trivy-fs.json"))
            )
            out = Path(tmp) / "findings.json"
            gate.main(["all", "--dir", str(d), "--out", str(out), "--stack", "node"])
            schema = json.loads(Path("scripts/schema/findings.v1.json").read_text())
            jsonschema.validate(json.loads(out.read_text()), schema)


if __name__ == "__main__":
    unittest.main()
