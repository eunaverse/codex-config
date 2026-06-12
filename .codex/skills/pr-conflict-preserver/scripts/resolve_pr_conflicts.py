#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import List, Optional


@dataclass
class Diff3Chunk:
    kind: str
    text: str = ""
    base: str = ""
    ours: str = ""
    theirs: str = ""


def run(cmd: List[str], cwd: Optional[Path] = None, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, check=check, text=True, capture_output=True)


def run_bytes(cmd: List[str], cwd: Optional[Path] = None, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, check=check, capture_output=True)


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return run(["git", *args], cwd=repo, check=check)


def git_bytes(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return run_bytes(["git", *args], cwd=repo, check=check)


def sanitize(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-") or "item"


def decode_text(raw: bytes) -> str:
    return raw.decode("utf-8", errors="surrogateescape")


def is_binary(raw: bytes) -> bool:
    return b"\x00" in raw


def get_repo_root() -> Path:
    result = run(["git", "rev-parse", "--show-toplevel"])
    return Path(result.stdout.strip())


def require_tool(name: str) -> None:
    if shutil.which(name) is None:
        raise SystemExit(f"required tool not found: {name}")


def ensure_gh_auth(repo: Path) -> None:
    result = run(["gh", "auth", "status"], cwd=repo, check=False)
    if result.returncode != 0:
        raise SystemExit("gh auth is required for PR metadata lookups; run `gh auth login` first")


def gh_pr_view(repo: Path, pr_number: int) -> dict:
    fields = [
        "number",
        "title",
        "baseRefName",
        "headRefName",
        "headRefOid",
        "headRepositoryOwner",
        "isCrossRepository",
        "url",
    ]
    result = run(["gh", "pr", "view", str(pr_number), "--json", ",".join(fields)], cwd=repo)
    return json.loads(result.stdout)


def fetch_branch(repo: Path, remote: str, branch: str) -> str:
    git(repo, "fetch", remote, f"{branch}:refs/remotes/{remote}/{branch}")
    return f"refs/remotes/{remote}/{branch}"


def fetch_pr_head(repo: Path, remote: str, pr_number: int) -> str:
    ref = f"refs/remotes/{remote}/__codex_pr_{pr_number}"
    git(repo, "fetch", remote, f"pull/{pr_number}/head:{ref}")
    return ref


def create_worktree(repo: Path, base_ref: str, branch_name: str, requested_path: Optional[Path]) -> Path:
    if requested_path is None:
        requested_path = repo / ".codex-conflict-worktrees" / branch_name
    requested_path.parent.mkdir(parents=True, exist_ok=True)
    if requested_path.exists():
        raise SystemExit(f"worktree path already exists: {requested_path}")
    git(repo, "worktree", "add", "-b", branch_name, str(requested_path), base_ref)
    return requested_path


def get_stage_bytes(repo: Path, stage: int, path: str) -> bytes:
    result = git_bytes(repo, "show", f":{stage}:{path}", check=False)
    if result.returncode != 0:
        return b""
    return result.stdout


def build_diff3_text(base_raw: bytes, ours_raw: bytes, theirs_raw: bytes) -> str:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        ours_path = tmp / "ours"
        base_path = tmp / "base"
        theirs_path = tmp / "theirs"
        ours_path.write_bytes(ours_raw)
        base_path.write_bytes(base_raw)
        theirs_path.write_bytes(theirs_raw)
        result = run(
            [
                "git",
                "merge-file",
                "-p",
                "--diff3",
                "-L",
                "ours",
                "-L",
                "base",
                "-L",
                "theirs",
                str(ours_path),
                str(base_path),
                str(theirs_path),
            ],
            check=False,
        )
        return result.stdout


def parse_diff3(text: str) -> List[Diff3Chunk]:
    lines = text.splitlines(keepends=True)
    chunks: List[Diff3Chunk] = []
    buffer: List[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("<<<<<<< "):
            if buffer:
                chunks.append(Diff3Chunk(kind="text", text="".join(buffer)))
                buffer = []
            i += 1
            ours: List[str] = []
            while i < len(lines) and not lines[i].startswith("||||||| "):
                ours.append(lines[i])
                i += 1
            if i >= len(lines):
                raise ValueError("malformed diff3 conflict: missing base marker")
            i += 1
            base: List[str] = []
            while i < len(lines) and not lines[i].startswith("======="):
                base.append(lines[i])
                i += 1
            if i >= len(lines):
                raise ValueError("malformed diff3 conflict: missing separator")
            i += 1
            theirs: List[str] = []
            while i < len(lines) and not lines[i].startswith(">>>>>>> "):
                theirs.append(lines[i])
                i += 1
            if i >= len(lines):
                raise ValueError("malformed diff3 conflict: missing end marker")
            i += 1
            chunks.append(
                Diff3Chunk(
                    kind="conflict",
                    base="".join(base),
                    ours="".join(ours),
                    theirs="".join(theirs),
                )
            )
            continue
        buffer.append(line)
        i += 1
    if buffer:
        chunks.append(Diff3Chunk(kind="text", text="".join(buffer)))
    return chunks


def conflict_marker(base: str, ours: str, theirs: str) -> str:
    return "".join(
        [
            "<<<<<<< ours\n",
            ours,
            "||||||| base\n",
            base,
            "=======\n",
            theirs,
            ">>>>>>> theirs\n",
        ]
    )


def change_entries(base_lines: List[str], side_lines: List[str]) -> List[dict]:
    matcher = SequenceMatcher(a=base_lines, b=side_lines)
    entries = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        entries.append({"tag": tag, "i1": i1, "i2": i2, "j1": j1, "j2": j2, "side": side_lines[j1:j2]})
    return entries


def edits_overlap(left: dict, right: dict) -> bool:
    left_insert = left["tag"] == "insert"
    right_insert = right["tag"] == "insert"
    if left_insert and right_insert:
        return left["i1"] == right["i1"]
    if left_insert:
        point = left["i1"]
        return right["i1"] < point < right["i2"]
    if right_insert:
        point = right["i1"]
        return left["i1"] < point < left["i2"]
    return not (left["i2"] <= right["i1"] or right["i2"] <= left["i1"])


def merge_non_overlapping(base: str, ours: str, theirs: str) -> tuple[bool, str, str]:
    if ours == theirs:
        return True, ours, "identical"
    if ours == base:
        return True, theirs, "ours-matches-base"
    if theirs == base:
        return True, ours, "theirs-matches-base"

    base_lines = base.splitlines(keepends=True)
    ours_lines = ours.splitlines(keepends=True)
    theirs_lines = theirs.splitlines(keepends=True)
    our_changes = change_entries(base_lines, ours_lines)
    their_changes = change_entries(base_lines, theirs_lines)

    for left in our_changes:
        for right in their_changes:
            if edits_overlap(left, right):
                return False, conflict_marker(base, ours, theirs), "overlapping-base-range"

    merged_lines = list(base_lines)
    combined = [(entry, "ours") for entry in our_changes] + [(entry, "theirs") for entry in their_changes]
    combined.sort(key=lambda item: (item[0]["i1"], item[0]["i2"], 0 if item[0]["tag"] != "insert" else 1), reverse=True)
    for entry, _origin in combined:
        replacement = entry["side"]
        merged_lines[entry["i1"] : entry["i2"]] = replacement
    return True, "".join(merged_lines), "disjoint-edits"


def write_sidecar(base_dir: Path, path: str, base_raw: bytes, ours_raw: bytes, theirs_raw: bytes, hunk_records: List[dict]) -> None:
    file_dir = base_dir / "files" / sanitize(path)
    file_dir.mkdir(parents=True, exist_ok=True)
    (file_dir / "base").write_bytes(base_raw)
    (file_dir / "ours").write_bytes(ours_raw)
    (file_dir / "theirs").write_bytes(theirs_raw)
    (file_dir / "hunks.json").write_text(json.dumps(hunk_records, indent=2, ensure_ascii=False) + "\n")


def resolve_conflicted_file(repo: Path, rel_path: str, artifact_dir: Path) -> dict:
    base_raw = get_stage_bytes(repo, 1, rel_path)
    ours_raw = get_stage_bytes(repo, 2, rel_path)
    theirs_raw = get_stage_bytes(repo, 3, rel_path)
    current_path = repo / rel_path

    if not base_raw and not ours_raw and not theirs_raw:
        return {"path": rel_path, "status": "unresolved", "reason": "missing-index-stages"}

    if any(is_binary(raw) for raw in (base_raw, ours_raw, theirs_raw)):
        write_sidecar(artifact_dir, rel_path, base_raw, ours_raw, theirs_raw, [])
        return {"path": rel_path, "status": "unresolved", "reason": "binary-conflict"}

    diff3_text = build_diff3_text(base_raw, ours_raw, theirs_raw)
    chunks = parse_diff3(diff3_text)
    output_parts: List[str] = []
    hunk_records: List[dict] = []
    unresolved = False

    for index, chunk in enumerate(chunks):
        if chunk.kind == "text":
            output_parts.append(chunk.text)
            continue
        safe, merged_text, reason = merge_non_overlapping(chunk.base, chunk.ours, chunk.theirs)
        if not safe:
            unresolved = True
        output_parts.append(merged_text)
        hunk_records.append(
            {
                "index": index,
                "status": "resolved" if safe else "unresolved",
                "reason": reason,
                "base": chunk.base,
                "ours": chunk.ours,
                "theirs": chunk.theirs,
                "merged_preview": merged_text,
            }
        )

    current_path.parent.mkdir(parents=True, exist_ok=True)
    current_path.write_text("".join(output_parts), encoding="utf-8", errors="surrogateescape")
    write_sidecar(artifact_dir, rel_path, base_raw, ours_raw, theirs_raw, hunk_records)
    if not unresolved:
        git(repo, "add", "--", rel_path)
    return {
        "path": rel_path,
        "status": "unresolved" if unresolved else "resolved",
        "reason": "contains-unresolved-hunks" if unresolved else "all-safe-hunks-resolved",
        "hunks": hunk_records,
    }


def validate_file(path: Path) -> Optional[str]:
    suffix = path.suffix.lower()
    raw = path.read_text(encoding="utf-8", errors="surrogateescape")
    try:
        if suffix == ".py":
            ast.parse(raw)
        elif suffix == ".json":
            json.loads(raw)
        elif suffix == ".toml":
            import tomllib

            tomllib.loads(raw)
        elif suffix in {".yaml", ".yml"}:
            try:
                import yaml  # type: ignore
            except ImportError:
                return None
            yaml.safe_load(raw)
    except Exception as exc:  # noqa: BLE001
        return f"{path}: {exc}"
    return None


def validate_repo(repo: Path) -> List[str]:
    failures: List[str] = []
    diff_check = git(repo, "diff", "--check", check=False)
    if diff_check.returncode != 0:
        failures.append(diff_check.stdout.strip() or diff_check.stderr.strip() or "git diff --check failed")
    changed = git(repo, "diff", "--cached", "--name-only").stdout.splitlines()
    for rel in changed:
        path = repo / rel
        if not path.is_file():
            continue
        failure = validate_file(path)
        if failure:
            failures.append(failure)
    return failures


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_summary_md(path: Path, payload: dict) -> None:
    lines = [
        f"# Conflict Resolution Summary",
        "",
        f"- mode: `{payload['mode']}`",
        f"- final_status: `{payload['final_status']}`",
        f"- resolution_branch: `{payload['resolution_branch']}`",
        f"- worktree_path: `{payload['worktree_path']}`",
        f"- artifact_dir: `{payload['artifact_dir']}`",
        "",
    ]
    for step in payload["steps"]:
        lines.append(f"## {step['label']}")
        lines.append("")
        lines.append(f"- target: `{step['target']}`")
        lines.append(f"- status: `{step['status']}`")
        if step.get("resolved_files"):
            lines.append(f"- resolved_files: {', '.join(f'`{item}`' for item in step['resolved_files'])}")
        if step.get("unresolved_files"):
            lines.append(f"- unresolved_files: {', '.join(f'`{item}`' for item in step['unresolved_files'])}")
        if step.get("validation_failures"):
            lines.append("- validation_failures:")
            for failure in step["validation_failures"]:
                lines.append(f"  - `{failure}`")
        if step.get("commit"):
            lines.append(f"- commit: `{step['commit']}`")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def resolve_current_conflicts(repo: Path, artifact_dir: Path) -> dict:
    conflicted = git(repo, "diff", "--name-only", "--diff-filter=U").stdout.splitlines()
    results = [resolve_conflicted_file(repo, rel_path, artifact_dir) for rel_path in conflicted]
    return {
        "files": results,
        "resolved_files": [item["path"] for item in results if item["status"] == "resolved"],
        "unresolved_files": [item["path"] for item in results if item["status"] != "resolved"],
    }


def finalize_step(repo: Path, step_payload: dict, commit_message: str, allow_commit: bool) -> dict:
    if step_payload["unresolved_files"]:
        step_payload["status"] = "unresolved"
        return step_payload

    validation_failures = validate_repo(repo)
    if validation_failures:
        step_payload["status"] = "validation_failed"
        step_payload["validation_failures"] = validation_failures
        return step_payload

    if allow_commit:
        git(repo, "commit", "-m", commit_message)
        step_payload["commit"] = git(repo, "rev-parse", "HEAD").stdout.strip()
    step_payload["status"] = "resolved" if allow_commit else "clean"
    return step_payload


def merge_target(repo: Path, target_ref: str, label: str, artifact_dir: Path, commit_message: str, allow_commit: bool) -> dict:
    merge = git(repo, "merge", "--no-commit", "--no-ff", target_ref, check=False)
    step = {
        "label": label,
        "target": target_ref,
        "status": "clean",
        "stdout": merge.stdout.strip(),
        "stderr": merge.stderr.strip(),
        "resolved_files": [],
        "unresolved_files": [],
    }
    if merge.returncode == 0:
        return finalize_step(repo, step, commit_message, allow_commit)

    conflict_state = resolve_current_conflicts(repo, artifact_dir)
    step.update(conflict_state)
    step = finalize_step(repo, step, commit_message, allow_commit)
    return step


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Resolve safe PR conflicts without dropping either side")
    parser.add_argument("--pr", type=int, help="Primary GitHub PR number")
    parser.add_argument("--against-pr", type=int, help="Second GitHub PR number for PR-vs-PR simulation")
    parser.add_argument("--base-branch", help="Base branch name")
    parser.add_argument("--head-branch", help="Head branch name for branch-vs-branch mode")
    parser.add_argument("--remote", default="origin", help="Git remote to fetch from")
    parser.add_argument("--branch-name", help="Name for the generated resolution branch")
    parser.add_argument("--worktree-dir", help="Explicit path for the isolated worktree")
    parser.add_argument("--no-commit", action="store_true", help="Do not create commits even after safe resolution")
    return parser


def determine_mode(args: argparse.Namespace) -> str:
    if args.pr and args.against_pr:
        return "pr-vs-pr"
    if args.pr:
        return "pr-vs-base"
    if args.base_branch and args.head_branch:
        return "branch-vs-branch"
    raise SystemExit("provide either --pr, --pr with --against-pr, or --base-branch with --head-branch")


def main() -> int:
    args = build_parser().parse_args()
    require_tool("git")
    require_tool("gh")
    repo = get_repo_root()
    ensure_gh_auth(repo)
    mode = determine_mode(args)
    remote = args.remote
    now = datetime.now().strftime("%Y%m%d-%H%M%S")

    if mode == "pr-vs-base":
        pr_info = gh_pr_view(repo, args.pr)
        base_branch = args.base_branch or pr_info["baseRefName"]
        base_ref = fetch_branch(repo, remote, base_branch)
        target_ref = fetch_pr_head(repo, remote, args.pr)
        branch_name = args.branch_name or f"resolve-pr-{args.pr}-vs-{sanitize(base_branch)}-{now}"
        worktree_path = create_worktree(repo, base_ref, branch_name, Path(args.worktree_dir) if args.worktree_dir else None)
        artifact_dir = worktree_path / ".codex-conflict-preserver" / now
        artifact_dir.mkdir(parents=True, exist_ok=True)
        step = merge_target(
            worktree_path,
            target_ref,
            f"merge-pr-{args.pr}",
            artifact_dir,
            f"chore(conflict): resolve safe conflicts for pr #{args.pr}",
            allow_commit=not args.no_commit,
        )
        steps = [step]
    elif mode == "pr-vs-pr":
        primary = gh_pr_view(repo, args.pr)
        secondary = gh_pr_view(repo, args.against_pr)
        base_branch = args.base_branch or primary["baseRefName"]
        if secondary["baseRefName"] != base_branch and not args.base_branch:
            raise SystemExit(
                f"PR base mismatch: pr #{args.pr} targets {primary['baseRefName']} but pr #{args.against_pr} targets {secondary['baseRefName']}; pass --base-branch explicitly to override"
            )
        base_ref = fetch_branch(repo, remote, base_branch)
        first_ref = fetch_pr_head(repo, remote, args.pr)
        second_ref = fetch_pr_head(repo, remote, args.against_pr)
        branch_name = args.branch_name or f"resolve-pr-{args.pr}-pr-{args.against_pr}-{sanitize(base_branch)}-{now}"
        worktree_path = create_worktree(repo, base_ref, branch_name, Path(args.worktree_dir) if args.worktree_dir else None)
        artifact_dir = worktree_path / ".codex-conflict-preserver" / now
        artifact_dir.mkdir(parents=True, exist_ok=True)
        first_step = merge_target(
            worktree_path,
            first_ref,
            f"merge-pr-{args.pr}",
            artifact_dir,
            f"chore(conflict): apply pr #{args.pr} before conflict simulation",
            allow_commit=not args.no_commit,
        )
        steps = [first_step]
        if first_step["status"] in {"resolved", "clean"}:
            second_step = merge_target(
                worktree_path,
                second_ref,
                f"merge-pr-{args.against_pr}",
                artifact_dir,
                f"chore(conflict): resolve safe conflicts for pr #{args.against_pr} after pr #{args.pr}",
                allow_commit=not args.no_commit,
            )
            steps.append(second_step)
    else:
        base_ref = fetch_branch(repo, remote, args.base_branch)
        target_ref = fetch_branch(repo, remote, args.head_branch)
        branch_name = args.branch_name or f"resolve-{sanitize(args.head_branch)}-vs-{sanitize(args.base_branch)}-{now}"
        worktree_path = create_worktree(repo, base_ref, branch_name, Path(args.worktree_dir) if args.worktree_dir else None)
        artifact_dir = worktree_path / ".codex-conflict-preserver" / now
        artifact_dir.mkdir(parents=True, exist_ok=True)
        step = merge_target(
            worktree_path,
            target_ref,
            f"merge-{sanitize(args.head_branch)}",
            artifact_dir,
            f"chore(conflict): resolve safe conflicts for {args.head_branch}",
            allow_commit=not args.no_commit,
        )
        steps = [step]

    final_status = "committed"
    for step in steps:
        if step["status"] == "unresolved":
            final_status = "unresolved"
            break
        if step["status"] == "validation_failed":
            final_status = "validation_failed"
            break

    summary = {
        "mode": mode,
        "repo_root": str(repo),
        "worktree_path": str(worktree_path),
        "resolution_branch": branch_name,
        "artifact_dir": str(artifact_dir),
        "steps": steps,
        "final_status": final_status,
    }
    write_json(artifact_dir / "summary.json", summary)
    write_summary_md(artifact_dir / "summary.md", summary)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if final_status == "committed" else 1


if __name__ == "__main__":
    sys.exit(main())
