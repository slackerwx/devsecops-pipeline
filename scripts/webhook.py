#!/usr/bin/env python3
"""Evidence webhook client: POST SARIF documents and events. Never fails the job."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request


def post(
    url: str, token: str, body: bytes, retries: int = 2, timeout: int = 30
) -> tuple[bool, str]:
    headers = {
        "content-type": "application/json",
        "authorization": f"Bearer {token}",
        "user-agent": "devsecops-pipeline",
    }
    last = ""
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, data=body, method="POST", headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as res:
                return True, f"HTTP {res.status}"
        except urllib.error.HTTPError as exc:
            last = f"HTTP {exc.code}"
            if 400 <= exc.code < 500:
                return False, last
        except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
            last = str(exc)
        if attempt < retries:
            time.sleep(2 * (attempt + 1))
    return False, last


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sarif")
    s.add_argument("--file", required=True)
    e = sub.add_parser("event")
    e.add_argument("--type", required=True)
    e.add_argument("--payload", default="{}")
    a = p.parse_args(argv)

    base = os.environ.get("EVIDENCE_WEBHOOK_URL", "").strip().rstrip("/")
    token = os.environ.get("EVIDENCE_WEBHOOK_TOKEN", "")
    if not base:
        print("webhook: disabled (EVIDENCE_WEBHOOK_URL is empty)")
        return 0
    if a.cmd == "sarif":
        try:
            with open(a.file, "rb") as fh:
                body = fh.read()
        except OSError as exc:
            print(f"::warning::webhook: cannot read {a.file}: {exc}")
            return 0
        what, ok, info = (
            f"sarif {os.path.basename(a.file)}",
            *post(f"{base}/sarif", token, body),
        )
    else:
        try:
            payload = json.loads(a.payload)
        except json.JSONDecodeError as exc:
            print(f"::warning::webhook: bad payload JSON: {exc}")
            return 0
        body = json.dumps({"type": a.type, "payload": payload}).encode()
        what, ok, info = f"event {a.type}", *post(f"{base}/event", token, body)
    print(
        f"webhook: {what} -> ok ({info})"
        if ok
        else f"::warning::webhook: {what} failed ({info})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
