import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import detect


def touch(root: Path, rel: str, text: str = "") -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


class DetectStackTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_node_with_pnpm_lock(self):
        touch(self.root, "package.json", '{"name":"x","packageManager":"pnpm@10.4.1"}')
        touch(self.root, "pnpm-lock.yaml")
        self.assertEqual(detect.detect_stack(self.root), "node")
        self.assertEqual(detect.package_manager("node", self.root), "pnpm")

    def test_python_uv(self):
        touch(
            self.root,
            "pyproject.toml",
            '[project]\nname="x"\nrequires-python=">=3.11"\n',
        )
        touch(self.root, "uv.lock")
        self.assertEqual(detect.detect_stack(self.root), "python")
        self.assertEqual(detect.package_manager("python", self.root), "uv")
        self.assertEqual(detect.toolchain_version("python", self.root, ""), "3.11")

    def test_go_uses_go_mod(self):
        touch(self.root, "go.mod", "module x\n\ngo 1.24\n")
        self.assertEqual(detect.detect_stack(self.root), "go")
        self.assertEqual(detect.toolchain_version("go", self.root, ""), "")

    def test_java_gradle_and_dotnet_tfm(self):
        touch(
            self.root,
            "build.gradle.kts",
            "java { toolchain { languageVersion.set(JavaLanguageVersion.of(17)) } }",
        )
        self.assertEqual(detect.detect_stack(self.root), "java")
        self.assertEqual(detect.package_manager("java", self.root), "gradle")
        self.assertEqual(detect.toolchain_version("java", self.root, ""), "17")
        other = self.root / "dn"
        touch(
            other,
            "Api.csproj",
            "<Project><PropertyGroup><TargetFramework>net8.0</TargetFramework></PropertyGroup></Project>",
        )
        self.assertEqual(detect.detect_stack(other), "dotnet")
        self.assertEqual(detect.toolchain_version("dotnet", other, ""), "8.0.x")

    def test_ambiguous_and_missing(self):
        touch(self.root, "package.json", "{}")
        touch(self.root, "go.mod", "module x\n")
        with self.assertRaises(SystemExit):
            detect.detect_stack(self.root)
        with self.assertRaises(SystemExit):
            detect.detect_stack(self.root / "empty")

    def test_override_wins(self):
        touch(self.root, ".nvmrc", "v20.11.0\n")
        touch(self.root, "package.json", "{}")
        self.assertEqual(detect.toolchain_version("node", self.root, ""), "20.11.0")
        self.assertEqual(detect.toolchain_version("node", self.root, "22"), "22")

    def test_python_fixture(self):
        root = Path("tests/fixtures/python")
        self.assertEqual(detect.detect_stack(root), "python")
        self.assertEqual(detect.package_manager("python", root), "pip")
        self.assertEqual(detect.toolchain_version("python", root, ""), "3.12")

    def test_go_fixture(self):
        root = Path("tests/fixtures/go")
        self.assertEqual(detect.detect_stack(root), "go")
        self.assertEqual(detect.package_manager("go", root), "gomod")

    def test_java_fixture(self):
        root = Path("tests/fixtures/java")
        self.assertEqual(detect.detect_stack(root), "java")
        self.assertEqual(detect.package_manager("java", root), "maven")
        self.assertEqual(detect.toolchain_version("java", root, ""), "21")


class PlanTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        touch(self.root, "package.json", '{"name":"x"}')
        touch(self.root, "package-lock.json", "{}")
        touch(self.root, "Dockerfile", "FROM scratch\n")

    def tearDown(self):
        self.tmp.cleanup()

    def plan(self, **kw):
        env = {
            "GITHUB_REPOSITORY": "Acme/My-App",
            "GITHUB_EVENT_NAME": "push",
            "GITHUB_REF": "refs/heads/main",
            "DEFAULT_BRANCH": "main",
        }
        with mock.patch.dict(os.environ, env):
            args = detect.parse_args(
                ["--dir", str(self.root)]
                + [f"--{k.replace('_', '-')}={v}" for k, v in kw.items()]
            )
            return detect.plan(args)

    def test_defaults_on_default_branch_push(self):
        p = self.plan()
        self.assertEqual(p["stack"], "node")
        self.assertEqual(p["image-name"], "ghcr.io/acme/my-app")
        self.assertEqual(p["push"], "true")
        self.assertEqual(p["slug"], "root")
        self.assertEqual(p["dast-mode"], "skip")
        self.assertTrue(json.loads(p["stages"])["image"])

    def test_pr_auto_does_not_push_and_dast_skips(self):
        env = {
            "GITHUB_REPOSITORY": "Acme/My-App",
            "GITHUB_EVENT_NAME": "pull_request",
            "GITHUB_REF": "refs/pull/7/merge",
            "DEFAULT_BRANCH": "main",
        }
        with mock.patch.dict(os.environ, env):
            args = detect.parse_args(["--dir", str(self.root), "--app-port=3000"])
            p = detect.plan(args)
        self.assertEqual(p["push"], "false")
        self.assertEqual(p["dast-mode"], "skip")
        self.assertIn("not pushed", p["dast-skip-reason"])

    def test_ephemeral_dast_and_subdir_slug(self):
        sub = self.root / "services" / "api"
        touch(sub, "package.json", "{}")
        touch(sub, "Dockerfile", "FROM scratch\n")
        env = {
            "GITHUB_REPOSITORY": "acme/app",
            "GITHUB_EVENT_NAME": "push",
            "GITHUB_REF": "refs/tags/v1.2.3",
            "DEFAULT_BRANCH": "main",
        }
        with mock.patch.dict(os.environ, env):
            args = detect.parse_args(
                [
                    "--dir",
                    str(sub),
                    "--working-directory",
                    "services/api",
                    "--app-port",
                    "8080",
                ]
            )
            p = detect.plan(args)
        self.assertEqual(p["slug"], "services-api")
        self.assertEqual(p["image-name"], "ghcr.io/acme/app/services-api")
        self.assertEqual(p["dast-mode"], "ephemeral")

    def test_skip_stages_and_external_dast(self):
        p = self.plan(
            skip_stages="sast,image", dast_target_url="https://staging.example.com"
        )
        stages = json.loads(p["stages"])
        self.assertFalse(stages["sast"])
        self.assertFalse(stages["image"])
        self.assertFalse(stages["sign"])
        self.assertTrue(stages["dast"])
        self.assertEqual(p["dast-mode"], "external")

    def test_unknown_stage_fails(self):
        with self.assertRaises(SystemExit):
            self.plan(skip_stages="lint")


if __name__ == "__main__":
    unittest.main()
