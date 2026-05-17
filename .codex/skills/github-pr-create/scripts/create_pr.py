#!/usr/bin/env python3
"""Create a GitHub pull request with gh fallback to GitHub REST API."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path


def run(cmd: list[str], *, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def require_success(result: subprocess.CompletedProcess[str], action: str) -> str:
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"{action} failed: {detail}")
    return result.stdout.strip()


def git_output(args: list[str]) -> str:
    return require_success(run(["git", *args]), f"git {' '.join(args)}")


def detect_repo() -> tuple[str, str]:
    remote = git_output(["remote", "get-url", "origin"])

    patterns = [
        r"github\.com[:/](?P<owner>[^/]+)/(?P<repo>[^/.]+)(?:\.git)?$",
        r"github\.com/(?P<owner>[^/]+)/(?P<repo>[^/.]+)(?:\.git)?$",
    ]
    for pattern in patterns:
        match = re.search(pattern, remote)
        if match:
            return match.group("owner"), match.group("repo")

    raise RuntimeError(f"Could not detect GitHub owner/repo from origin remote: {remote}")


def read_body(args: argparse.Namespace) -> str:
    if args.body_file:
        return Path(args.body_file).read_text()
    return args.body or ""


def create_with_gh(args: argparse.Namespace, body: str) -> str | None:
    if shutil.which("gh") is None:
        return None

    cmd = [
        "gh",
        "pr",
        "create",
        "--base",
        args.base,
        "--head",
        args.head,
        "--title",
        args.title,
        "--body",
        body,
    ]
    if args.draft:
        cmd.append("--draft")

    result = run(cmd)
    if result.returncode == 0:
        return result.stdout.strip().splitlines()[-1]

    if "not logged into" in result.stderr.lower() or "authentication" in result.stderr.lower():
        return None

    raise RuntimeError(result.stderr.strip() or result.stdout.strip())


def token_from_git_credential() -> tuple[str, str] | None:
    result = run(["git", "credential", "fill"], input_text="protocol=https\nhost=github.com\n\n")
    if result.returncode != 0:
        return None

    values: dict[str, str] = {}
    for line in result.stdout.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key] = value

    username = values.get("username")
    password = values.get("password")
    if username and password:
        return username, password
    return None


def create_with_api(owner: str, repo: str, args: argparse.Namespace, body: str) -> str:
    payload = {
        "title": args.title,
        "body": body,
        "head": args.head,
        "base": args.base,
        "draft": args.draft,
    }

    request = urllib.request.Request(
        f"https://api.github.com/repos/{owner}/{repo}/pulls",
        data=json.dumps(payload).encode(),
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    else:
        credential = token_from_git_credential()
        if credential is None:
            raise RuntimeError("No gh auth, GH_TOKEN/GITHUB_TOKEN, or git credential available")
        username, password = credential
        import base64

        auth = base64.b64encode(f"{username}:{password}".encode()).decode()
        request.add_header("Authorization", f"Basic {auth}")

    try:
        with urllib.request.urlopen(request) as response:
            data = json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        message = exc.read().decode(errors="replace")
        try:
            data = json.loads(message)
            message = data.get("message", message)
        except json.JSONDecodeError:
            pass
        raise RuntimeError(f"GitHub API request failed ({exc.code}): {message}") from exc

    url = data.get("html_url")
    if not url:
        raise RuntimeError("GitHub API response did not include html_url")
    return url


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", default=None)
    parser.add_argument("--title", required=True)
    parser.add_argument("--body", default=None)
    parser.add_argument("--body-file", default=None)
    parser.add_argument("--draft", action="store_true")
    args = parser.parse_args()

    if args.head is None:
        args.head = git_output(["branch", "--show-current"])
    if args.body and args.body_file:
        raise RuntimeError("Use either --body or --body-file, not both")

    body = read_body(args)
    owner, repo = detect_repo()

    url = create_with_gh(args, body)
    if url is None:
        url = create_with_api(owner, repo, args, body)

    print(url)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
