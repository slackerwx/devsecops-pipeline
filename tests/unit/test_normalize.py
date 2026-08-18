import json
import tempfile
import unittest
from pathlib import Path

from scripts import normalize

SAMPLES = Path("tests/samples")


def load(name):
    return json.loads((SAMPLES / name).read_text())


class ParserTest(unittest.TestCase):
    def test_gitleaks_every_leak_is_critical_and_secret_is_dropped(self):
        out = normalize.PARSERS["gitleaks"](load("gitleaks.json"))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["severity"], "critical")
        self.assertEqual(out[0]["id"], "private-key")
        self.assertEqual(out[0]["location"], "secrets/id_rsa:1")
        self.assertNotIn("Secret", json.dumps(out))
        self.assertNotIn("REDACTED", json.dumps(out))

    def test_semgrep_severity_map(self):
        out = normalize.PARSERS["semgrep"](load("semgrep.json"))
        self.assertEqual([f["severity"] for f in out], ["medium", "high"])
        self.assertEqual(out[0]["location"], "server.js:12")
        self.assertTrue(out[0]["url"].startswith("https://semgrep.dev/r/"))

    def test_trivy_vuln_and_license(self):
        vulns = normalize.PARSERS["trivy-vuln"](load("trivy-fs.json"))
        self.assertEqual([f["severity"] for f in vulns], ["critical", "high", "info"])
        self.assertEqual(vulns[0]["package"], "lodash")
        self.assertEqual(vulns[0]["fixed"], "4.17.12")
        lics = normalize.PARSERS["trivy-license"](load("trivy-fs.json"))
        self.assertEqual(lics[0]["severity"], "high")
        self.assertEqual(lics[0]["id"], "GPL-3.0")

    def test_trivy_misconfig_and_hadolint(self):
        mis = normalize.PARSERS["trivy-misconfig"](load("trivy-config.json"))
        self.assertEqual(mis[0]["id"], "DS002")
        self.assertEqual(mis[0]["location"], "Dockerfile:1")
        had = normalize.PARSERS["hadolint"](load("hadolint.json"))
        self.assertEqual([f["severity"] for f in had], ["medium", "high"])
        self.assertIn("hadolint/wiki/DL3007", had[0]["url"])

    def test_zap_riskcode_strings(self):
        out = normalize.PARSERS["zap"](load("zap.json"))
        self.assertEqual([f["severity"] for f in out], ["low", "medium"])
        self.assertEqual(out[0]["location"], "http://127.0.0.1:3000/")
        self.assertEqual(out[0]["url"], "https://owasp.org/www-project-secure-headers/")

    def test_empty_inputs(self):
        for tool in normalize.PARSERS:
            self.assertEqual(
                normalize.PARSERS[tool](
                    {} if tool not in ("gitleaks", "hadolint") else []
                ),
                [],
            )


class BuildTest(unittest.TestCase):
    def test_counts_and_append(self):
        doc = normalize.build(
            "iac",
            "trivy-misconfig",
            "0.60.0",
            "ok",
            "",
            normalize.PARSERS["trivy-misconfig"](load("trivy-config.json")),
        )
        self.assertEqual(doc["counts"]["high"], 1)
        self.assertEqual(doc["counts"]["low"], 1)
        doc = normalize.build(
            "iac",
            "hadolint",
            "2.12.0",
            "ok",
            "",
            normalize.PARSERS["hadolint"](load("hadolint.json")),
            existing=doc,
        )
        self.assertEqual([t["name"] for t in doc["tools"]], ["trivy", "hadolint"])
        self.assertEqual(doc["counts"]["high"], 2)
        self.assertEqual(len(doc["findings"]), 4)

    def test_error_status_wins(self):
        doc = normalize.build("sast", "semgrep", "1.0", "ok", "", [])
        doc = normalize.build(
            "sast", "semgrep", "1.0", "error", "semgrep exited 2", [], existing=doc
        )
        self.assertEqual(doc["status"], "error")
        self.assertIn("exited 2", doc["reason"])

    def test_cli_writes_partial(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "findings-sca.json"
            rc = normalize.main(
                [
                    "--tool",
                    "trivy-vuln",
                    "--input",
                    str(SAMPLES / "trivy-fs.json"),
                    "--category",
                    "sca",
                    "--tool-version",
                    "0.60.0",
                    "--out",
                    str(out),
                ]
            )
            self.assertEqual(rc, 0)
            doc = json.loads(out.read_text())
            self.assertEqual(doc["category"], "sca")
            self.assertEqual(doc["status"], "ok")
            self.assertEqual(doc["counts"]["critical"], 1)

    def test_cli_missing_input_is_error_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "findings-sast.json"
            normalize.main(
                [
                    "--tool",
                    "semgrep",
                    "--input",
                    str(Path(tmp) / "nope.json"),
                    "--category",
                    "sast",
                    "--out",
                    str(out),
                ]
            )
            doc = json.loads(out.read_text())
            self.assertEqual(doc["status"], "error")
            self.assertEqual(doc["findings"], [])


if __name__ == "__main__":
    unittest.main()
