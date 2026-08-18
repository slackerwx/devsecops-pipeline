#!/usr/bin/env python3
"""Detect the stack of a project directory and resolve the pipeline plan.

Prints key=value lines (one per output) so a composite action can append them to $GITHUB_OUTPUT.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

STACKS = ("node", "python", "go", "java", "dotnet")
STAGES = ("build", "test", "secrets", "sast", "sca", "iac", "image", "dast", "sign")
DEFAULT_VERSION = {
    "node": "22",
    "python": "3.12",
    "go": "",
    "java": "21",
    "dotnet": "8.0.x",
}
TOOL_VERSIONS_KEY = {
    "node": "nodejs",
    "python": "python",
    "go": "golang",
    "java": "java",
    "dotnet": "dotnet",
}
IAC_GLOBS = (
    "Dockerfile*",
    "*.tf",
    "*.hcl",
    "Chart.yaml",
    "docker-compose*.yml",
    "docker-compose*.yaml",
    "compose*.yml",
    "compose*.yaml",
)
PRUNE = {
    ".git",
    "node_modules",
    "vendor",
    ".venv",
    "venv",
    "target",
    "bin",
    "obj",
    "dist",
    "build",
    ".pipeline",
}


def read(path: Path) -> str:
    try:
        return path.read_text(errors="ignore")
    except OSError:
        return ""


def detect_stack(d: Path) -> str:
    found = []
    if (d / "package.json").is_file():
        found.append("node")
    if any(
        (d / f).is_file() for f in ("pyproject.toml", "requirements.txt", "setup.py")
    ):
        found.append("python")
    if (d / "go.mod").is_file():
        found.append("go")
    if any((d / f).is_file() for f in ("pom.xml", "build.gradle", "build.gradle.kts")):
        found.append("java")
    if list(d.glob("*.sln")) or list(d.glob("*.csproj")) or list(d.glob("*.fsproj")):
        found.append("dotnet")
    if len(found) == 1:
        return found[0]
    if not found:
        raise SystemExit(
            f"detect: no supported stack found in {d}; set the `stack` input"
        )
    raise SystemExit(
        f"detect: ambiguous stack ({', '.join(found)}) in {d}; set the `stack` input"
    )


def package_manager(stack: str, d: Path) -> str:
    if stack == "node":
        if (d / "pnpm-lock.yaml").is_file():
            return "pnpm"
        if (d / "yarn.lock").is_file():
            return "yarn"
        try:
            pm = str(
                json.loads(read(d / "package.json") or "{}").get("packageManager", "")
            )
        except json.JSONDecodeError:
            pm = ""
        if pm.startswith("pnpm@"):
            return "pnpm"
        if pm.startswith("yarn@"):
            return "yarn"
        return "npm"
    if stack == "python":
        if (d / "uv.lock").is_file():
            return "uv"
        if (d / "poetry.lock").is_file():
            return "poetry"
        return "pip"
    if stack == "java":
        return "maven" if (d / "pom.xml").is_file() else "gradle"
    if stack == "go":
        return "gomod"
    return "dotnet"


def _tool_versions(d: Path, key: str) -> str:
    for line in read(d / ".tool-versions").splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0] == key:
            return parts[1]
    return ""


def _first_number(text: str) -> str:
    m = re.search(r"(\d+(?:\.\d+)*)", text)
    return m.group(1) if m else ""


def toolchain_version(stack: str, d: Path, override: str) -> str:
    if override:
        return override
    v = _tool_versions(d, TOOL_VERSIONS_KEY[stack])
    if v:
        return v
    if stack == "node":
        for f in (".nvmrc", ".node-version"):
            s = read(d / f).strip()
            if s:
                return s.lstrip("v")
        try:
            engines = (
                json.loads(read(d / "package.json") or "{}")
                .get("engines", {})
                .get("node", "")
            )
        except json.JSONDecodeError:
            engines = ""
        return _first_number(engines) or DEFAULT_VERSION["node"]
    if stack == "python":
        s = read(d / ".python-version").strip().splitlines()
        if s:
            return s[0].strip()
        m = re.search(
            r'requires-python\s*=\s*"[^\d]*(\d+\.\d+)', read(d / "pyproject.toml")
        )
        return m.group(1) if m else DEFAULT_VERSION["python"]
    if stack == "go":
        return ""
    if stack == "java":
        s = read(d / ".java-version").strip()
        if s:
            return _first_number(s)
        pom = read(d / "pom.xml")
        for tag in (
            "maven.compiler.release",
            "maven.compiler.source",
            "java.version",
            "release",
        ):
            m = re.search(rf"<{tag}>\s*(?:1\.)?(\d+)\s*</{tag}>", pom)
            if m:
                return m.group(1)
        gradle = read(d / "build.gradle") + read(d / "build.gradle.kts")
        m = re.search(
            r"JavaLanguageVersion\.of\((\d+)\)|sourceCompatibility\s*=\s*['\"]?(?:1\.)?(\d+)",
            gradle,
        )
        if m:
            return m.group(1) or m.group(2)
        return DEFAULT_VERSION["java"]
    if stack == "dotnet":
        try:
            sdk = (
                json.loads(read(d / "global.json") or "{}")
                .get("sdk", {})
                .get("version", "")
            )
        except json.JSONDecodeError:
            sdk = ""
        if sdk:
            return sdk
        for proj in list(d.rglob("*.csproj")) + list(d.rglob("*.fsproj")):
            m = re.search(r"<TargetFrameworks?>\s*net(\d+\.\d+)", read(proj))
            if m:
                return f"{m.group(1)}.x"
        return DEFAULT_VERSION["dotnet"]
    raise SystemExit(f"detect: unknown stack {stack}")


def has_iac(d: Path, dockerfile: str) -> bool:
    if (d / dockerfile).is_file():
        return True
    for base, dirs, files in os.walk(d):
        dirs[:] = [x for x in dirs if x not in PRUNE]
        p = Path(base)
        for pattern in IAC_GLOBS:
            if any(p.glob(pattern)):
                return True
        for f in files:
            if f.endswith((".yaml", ".yml")):
                text = read(p / f)
                if re.search(r"^apiVersion:", text, re.MULTILINE) and re.search(
                    r"^kind:", text, re.MULTILINE
                ):
                    return True
    return False


def slug_of(working_directory: str) -> str:
    wd = working_directory.strip().strip("/")
    if wd in ("", "."):
        return "root"
    return re.sub(r"[^a-z0-9]+", "-", wd.lower()).strip("-") or "root"


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dir", required=True)
    p.add_argument("--working-directory", default=".")
    p.add_argument("--stack", default="auto")
    p.add_argument("--toolchain-version", default="")
    p.add_argument("--dockerfile", default="Dockerfile")
    p.add_argument("--image-name", default="")
    p.add_argument("--registry", default="ghcr.io")
    p.add_argument("--push", default="auto", choices=("auto", "always", "never"))
    p.add_argument("--skip-stages", default="")
    p.add_argument("--app-port", default="")
    p.add_argument("--dast-target-url", default="")
    p.add_argument("--sign", default="keyless", choices=("keyless", "key", "none"))
    return p.parse_args(argv)


def plan(args: argparse.Namespace) -> dict[str, str]:
    d = Path(args.dir)
    stack = args.stack if args.stack != "auto" else detect_stack(d)
    if stack not in STACKS:
        raise SystemExit(
            f"detect: unsupported stack `{stack}` (one of {', '.join(STACKS)})"
        )
    skip = {s.strip() for s in args.skip_stages.split(",") if s.strip()}
    unknown = skip - set(STAGES)
    if unknown:
        raise SystemExit(
            f"detect: unknown stage(s) in skip-stages: {', '.join(sorted(unknown))}"
        )
    stages = {s: s not in skip for s in STAGES}

    dockerfile_present = (d / args.dockerfile).is_file()
    stages["image"] = stages["image"] and dockerfile_present
    stages["iac"] = stages["iac"] and has_iac(d, args.dockerfile)
    stages["sign"] = stages["sign"] and stages["image"] and args.sign != "none"

    repo = os.environ.get("GITHUB_REPOSITORY", "").lower()
    slug = slug_of(args.working_directory)
    image_name = args.image_name or f"{args.registry}/{repo}" + (
        f"/{slug}" if slug != "root" else ""
    )

    event = os.environ.get("GITHUB_EVENT_NAME", "")
    ref = os.environ.get("GITHUB_REF", "")
    default_branch = os.environ.get("DEFAULT_BRANCH", "main")
    if args.push == "always":
        push = True
    elif args.push == "never":
        push = False
    else:
        push = event == "push" and (
            ref == f"refs/heads/{default_branch}" or ref.startswith("refs/tags/v")
        )
    push = push and stages["image"]

    if not stages["dast"]:
        dast_mode, reason = "skip", "stage disabled by skip-stages"
    elif args.dast_target_url:
        dast_mode, reason = "external", ""
    elif not args.app_port:
        dast_mode, reason = "skip", "no app-port and no dast-target-url"
    elif not stages["image"]:
        dast_mode, reason = (
            "skip",
            "no image to run (Dockerfile missing or image stage skipped)",
        )
    elif not push:
        dast_mode, reason = (
            "skip",
            "candidate image not pushed on this event (push=auto)",
        )
    else:
        dast_mode, reason = "ephemeral", ""
    stages["dast"] = dast_mode != "skip"

    return {
        "stack": stack,
        "package-manager": package_manager(stack, d),
        "toolchain-version": toolchain_version(stack, d, args.toolchain_version),
        "has-dockerfile": str(dockerfile_present).lower(),
        "has-iac": str(stages["iac"]).lower(),
        "image-name": image_name,
        "push": str(push).lower(),
        "dast-mode": dast_mode,
        "dast-skip-reason": reason,
        "slug": slug,
        "stages": json.dumps(stages, separators=(",", ":")),
    }


def main(argv: list[str]) -> int:
    out = plan(parse_args(argv))
    for k, v in out.items():
        print(f"{k}={v}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
