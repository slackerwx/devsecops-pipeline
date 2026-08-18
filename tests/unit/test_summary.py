import json
import tempfile
import unittest
from pathlib import Path

from scripts import gate, normalize, summary

SAMPLES = Path("tests/samples")


def full_doc(tmp: Path) -> dict:
    d = tmp / "ev"
    d.mkdir()
    sca = normalize.build(
        "sca",
        "trivy-vuln",
        "0.60.0",
        "ok",
        "",
        normalize.PARSERS["trivy-vuln"](
            json.loads((SAMPLES / "trivy-fs.json").read_text())
        ),
    )
    (d / "findings-sca.json").write_text(json.dumps(sca))
    out = tmp / "findings.json"
    gate.main(
        [
            "all",
            "--dir",
            str(d),
            "--out",
            str(out),
            "--mode",
            "enforce",
            "--stack",
            "node",
        ]
    )
    return json.loads(out.read_text())


class SummaryTest(unittest.TestCase):
    def test_render_summary_and_comment(self):
        with tempfile.TemporaryDirectory() as tmp:
            doc = full_doc(Path(tmp))
            extra = {
                "image": {
                    "image": "ghcr.io/acme/app",
                    "digest": "sha256:abc",
                    "pushed": True,
                    "tags": ["ghcr.io/acme/app:sha-1"],
                },
                "sign": {"signed": True, "mode": "keyless", "format": "legacy"},
            }
            text = summary.render(doc, extra, "summary", 15)
            self.assertIn("**FAIL**", text)
            self.assertIn("| sca |", text)
            self.assertIn("CVE-2019-10744", text)
            self.assertIn("ghcr.io/acme/app", text)
            self.assertIn("signed (keyless, legacy)", text)
            comment = summary.render(
                doc, {}, "comment", 1, marker="<!-- devsecops-pipeline:root -->"
            )
            self.assertTrue(comment.startswith("<!-- devsecops-pipeline:root -->"))
            self.assertIn("showing 1", comment)
            self.assertNotIn("CVE-2020-8203", comment)

    def test_truncation(self):
        with tempfile.TemporaryDirectory() as tmp:
            doc = full_doc(Path(tmp))
            doc["categories"]["sca"]["findings"] = [
                dict(
                    doc["categories"]["sca"]["findings"][0],
                    title="x" * 300,
                    id=f"CVE-{i}",
                )
                for i in range(3000)
            ]
            text = summary.render(doc, {}, "comment", 3000)
            self.assertLess(len(text), 61_000)
            self.assertIn("(truncated)", text)


if __name__ == "__main__":
    unittest.main()
