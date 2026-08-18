import json
import unittest
from pathlib import Path

from scripts import normalize, sarif

SAMPLES = Path("tests/samples")


class SarifTest(unittest.TestCase):
    def test_gitleaks_to_sarif(self):
        partial = normalize.build(
            "secrets",
            "gitleaks",
            "8.30.1",
            "ok",
            "",
            normalize.PARSERS["gitleaks"](
                json.loads((SAMPLES / "gitleaks.json").read_text())
            ),
        )
        doc = sarif.to_sarif(partial)
        run = doc["runs"][0]
        self.assertEqual(doc["version"], "2.1.0")
        self.assertEqual(run["tool"]["driver"]["name"], "Gitleaks")
        self.assertEqual(run["tool"]["driver"]["version"], "8.30.1")
        self.assertEqual(run["results"][0]["level"], "error")
        self.assertEqual(
            run["results"][0]["locations"][0]["physicalLocation"]["artifactLocation"][
                "uri"
            ],
            "secrets/id_rsa",
        )
        self.assertEqual(
            run["results"][0]["locations"][0]["physicalLocation"]["region"][
                "startLine"
            ],
            1,
        )
        self.assertEqual(
            run["tool"]["driver"]["rules"][0]["properties"]["security-severity"], "9.5"
        )

    def test_zap_urls_have_no_region(self):
        partial = normalize.build(
            "dast",
            "zap",
            "2.16.1",
            "ok",
            "",
            normalize.PARSERS["zap"](json.loads((SAMPLES / "zap.json").read_text())),
        )
        run = sarif.to_sarif(partial)["runs"][0]
        self.assertEqual(run["tool"]["driver"]["name"], "ZAP")
        loc = run["results"][0]["locations"][0]["physicalLocation"]
        self.assertEqual(loc["artifactLocation"]["uri"], "http://127.0.0.1:3000/")
        self.assertNotIn("region", loc)
        self.assertEqual(len(run["tool"]["driver"]["rules"]), 2)


if __name__ == "__main__":
    unittest.main()
