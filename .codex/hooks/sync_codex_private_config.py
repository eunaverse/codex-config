#!/usr/bin/env python3
"""Sync a safe allowlist of Codex configuration into the public config repo.

This script is intended to run from a Codex PostToolUse hook. It copies only
explicitly allowed files and directories, commits changed snapshots locally, and
pushes when the backup repo has a configured remote.
"""

from __future__ import annotations

import datetime as dt
import fcntl
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


HOME = Path.home()
CODEX_HOME = Path(os.environ.get("CODEX_HOME", HOME / ".codex")).expanduser()
BACKUP_REPO = Path(
    os.environ.get("CODEX_CONFIG_BACKUP_REPO", HOME / "codex-config")
).expanduser()
LOCK_FILE = Path(
    os.environ.get(
        "CODEX_CONFIG_SYNC_LOCK",
        "/private/tmp/eunhwa_codex_private_config_sync.lock",
    )
)
LOG_FILE = Path(
    os.environ.get(
        "CODEX_CONFIG_SYNC_LOG",
        BACKUP_REPO / ".sync" / "sync_codex_private_config.log",
    )
).expanduser()

ALLOWLIST = (
    (CODEX_HOME / "config.toml", BACKUP_REPO / ".codex" / "config.toml"),
    (CODEX_HOME / "hooks.json", BACKUP_REPO / ".codex" / "hooks.json"),
    (CODEX_HOME / "hooks", BACKUP_REPO / ".codex" / "hooks"),
    (CODEX_HOME / "skills", BACKUP_REPO / ".codex" / "skills"),
)

PUBLIC_EXCLUDED_PATHS = (
    BACKUP_REPO / "AGENTS.md",
    BACKUP_REPO / ".codex" / "skills" / "jd-resume-tailor",
    BACKUP_REPO / ".codex" / "skills" / "samsung-backend-interview-scripts",
)

EXCLUDED_NAMES = {
    ".DS_Store",
    ".git",
    ".pytest_cache",
    "__pycache__",
    "jd-resume-tailor",
    "samsung-backend-interview-scripts",
    "node_modules",
}

FORBIDDEN_BACKUP_PARTS = {
    ".tmp",
    "archived_sessions",
    "auth.json",
    "cache",
    "computer-use",
    "history.jsonl",
    "logs_2.sqlite",
    "logs_2.sqlite-shm",
    "logs_2.sqlite-wal",
    "plugins",
    "session_index.jsonl",
    "sessions",
    "shell_snapshots",
    "sqlite",
    "state_5.sqlite",
    "state_5.sqlite-shm",
    "state_5.sqlite-wal",
    "tmp",
    "transcription-history.jsonl",
}


README = """# Codex Config

Public backup for a safe allowlist of local Codex configuration: reusable
skills, hooks, and guardrails that make agent-assisted work more repeatable.

This repository is the executable companion to
[`agent-harness-playbook`](https://github.com/eunhwa99/agent-harness-playbook):
the playbook documents the delivery workflow, while this repo shows the local
Codex skills and hooks that help run that workflow in practice.

[`ai-news-alerts`](https://github.com/eunhwa99/ai-news-alerts) was built using
both pieces: the playbook for the delivery loop and this config for local
skills, safety checks, and sync automation.

Included:
- `.codex/config.toml`
- `.codex/hooks.json`
- `.codex/hooks/`
- `.codex/skills/`

Excluded by design:
- authentication files
- personal profile instructions (`AGENTS.md`)
- JD resume tailoring evidence and personal resume material
- Samsung backend interview scripts and personal experience material
- memory files and rollout summaries
- shell history and transcripts
- session logs
- sqlite databases
- plugin caches and runtime caches
- temporary files

The sync source of truth remains the local machine. This repo is a public
backup snapshot, not a full mirror of `~/.codex`.
"""


GITIGNORE = """# Never commit secrets, runtime state, or heavy local data.
.DS_Store
*.log
*.sqlite
*.sqlite-shm
*.sqlite-wal
*.db

.codex/auth.json
.codex/history.jsonl
.codex/transcription-history.jsonl
.codex/session_index.jsonl
.codex/sessions/
.codex/archived_sessions/
.codex/cache/
.codex/plugins/
.codex/.tmp/
.codex/tmp/
.codex/shell_snapshots/
.codex/sqlite/
.codex/computer-use/
.codex/memories/
.codex/state_*.sqlite*
.codex/logs_*.sqlite*
.sync/
"""


def main() -> int:
    try:
        consume_hook_payload()

        LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

        with LOCK_FILE.open("w") as lock:
            try:
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                log("sync skipped: another sync is already running")
                return 0

            try:
                ensure_repo()
                write_repo_metadata()
                sync_allowlist()
                remove_public_excluded_paths()
                assert_no_forbidden_files()
                changed = has_changes()
                if not changed:
                    log("sync complete: no changes")
                    return 0
                commit_changes()
                push_if_remote_exists()
                log("sync complete: committed changes")
            except Exception as exc:  # noqa: BLE001 - hook must fail open.
                log(f"sync failed open: {type(exc).__name__}: {exc}")
                return 0
    except Exception as exc:  # noqa: BLE001 - hook must fail open.
        safe_stderr(f"Codex config sync failed open: {type(exc).__name__}: {exc}\n")
        return 0

    return 0


def consume_hook_payload() -> None:
    if sys.stdin.isatty():
        return
    try:
        json.load(sys.stdin)
    except Exception:
        return


def ensure_repo() -> None:
    BACKUP_REPO.mkdir(parents=True, exist_ok=True)
    if not (BACKUP_REPO / ".git").exists():
        run(("git", "init", "-b", "main"), cwd=BACKUP_REPO)


def write_repo_metadata() -> None:
    write_text_if_changed(BACKUP_REPO / "README.md", README)
    write_text_if_changed(BACKUP_REPO / ".gitignore", GITIGNORE)


def sync_allowlist() -> None:
    for source, destination in ALLOWLIST:
        if not source.exists():
            remove_path(destination)
            continue
        if source.is_dir():
            copy_tree(source, destination)
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)


def remove_public_excluded_paths() -> None:
    for path in PUBLIC_EXCLUDED_PATHS:
        remove_path(path)


def copy_tree(source: Path, destination: Path) -> None:
    remove_path(destination)
    shutil.copytree(
        source,
        destination,
        ignore=ignore_names,
        symlinks=True,
    )


def ignore_names(_directory: str, names: list[str]) -> set[str]:
    ignored = set()
    for name in names:
        if name in EXCLUDED_NAMES:
            ignored.add(name)
    return ignored


def remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def assert_no_forbidden_files() -> None:
    for path in BACKUP_REPO.rglob("*"):
        if ".git" in path.parts:
            continue
        relative = path.relative_to(BACKUP_REPO)
        if any(part in FORBIDDEN_BACKUP_PARTS for part in relative.parts):
            raise RuntimeError(f"forbidden backup path detected: {relative}")


def has_changes() -> bool:
    result = run(("git", "status", "--porcelain"), cwd=BACKUP_REPO, capture=True)
    return bool(result.stdout.strip())


def commit_changes() -> None:
    run(("git", "add", "-A"), cwd=BACKUP_REPO)
    timestamp = dt.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    run(("git", "commit", "-m", f"chore: sync Codex config {timestamp}"), cwd=BACKUP_REPO)


def push_if_remote_exists() -> None:
    result = run(("git", "remote", "get-url", "origin"), cwd=BACKUP_REPO, capture=True, check=False)
    if result.returncode != 0:
        log("push skipped: origin remote is not configured")
        return

    upstream = run(
        ("git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"),
        cwd=BACKUP_REPO,
        capture=True,
        check=False,
    )
    if upstream.returncode == 0:
        push_result = run(("git", "push"), cwd=BACKUP_REPO, check=False, capture=True)
    else:
        push_result = run(
            ("git", "push", "-u", "origin", "main"),
            cwd=BACKUP_REPO,
            check=False,
            capture=True,
        )

    if push_result.returncode == 0:
        log("push complete")
    else:
        log(f"push failed open: {truncate(push_result.stdout)}")


def write_text_if_changed(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text() == content:
        return
    path.write_text(content)


def run(
    args: tuple[str, ...],
    *,
    cwd: Path,
    capture: bool = False,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.STDOUT if capture else None,
        check=check,
    )


def log(message: str) -> None:
    timestamp = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a") as file:
            file.write(f"{timestamp} {message}\n")
    except Exception:
        safe_stderr(f"{timestamp} {message}\n")


def truncate(output: str, max_chars: int = 1000) -> str:
    output = output.strip()
    if len(output) <= max_chars:
        return output
    return output[-max_chars:]


def safe_stderr(message: str) -> None:
    try:
        sys.stderr.write(message)
    except Exception:
        pass


if __name__ == "__main__":
    raise SystemExit(main())
