---
name: pr-conflict-preserver
description: Preserve both sides while resolving safe GitHub PR conflicts. Use when Codex needs to analyze or resolve a PR vs base-branch conflict, a PR vs PR conflict, or a conflicted merge where no side may be dropped or silently rewritten. This skill only auto-resolves non-overlapping text conflicts, preserves base/ours/theirs artifacts for every unresolved hunk, writes machine-readable and human-readable reports, and stops instead of guessing when semantic overlap is detected.
---

# PR Conflict Preserver

## Overview

Use this skill to resolve Git conflicts conservatively when content loss is unacceptable. The goal is to keep both sides intact, auto-resolve only clearly non-overlapping text edits, validate the result, and stop with preserved artifacts whenever a semantic decision would otherwise be guessed.

## Workflow

1. Confirm the repository policy before touching branches or PR state.
2. Inspect local state with `git status --short --branch` and avoid staging unrelated changes.
3. Prefer running the bundled script from the repository root. It creates an isolated worktree and does not rewrite the caller's current branch.
4. Let the script fetch PR metadata with `gh`, create a conflict-resolution branch, attempt the merge, auto-resolve only safe hunks, and write reports plus preserved artifacts.
5. If unresolved hunks remain, stop and review the generated report instead of forcing a merge.
6. If all hunks are safely resolved and validation passes, allow the script to create the resolution commit.
7. If the user explicitly asks to update the actual PR, fast-forward the PR head branch to the validated resolution commit and push that PR head branch. Do not stop at leaving the fix only on the temporary resolution branch.

## Safety Contract

- Never drop `ours`, `theirs`, or `base` content silently.
- Never auto-resolve overlapping edits to the same base range.
- Never normalize, summarize, or restyle conflicting text as part of conflict resolution.
- Preserve every unresolved conflict in two places:
  - inside the working file as diff3 markers
  - inside the artifact directory as raw `base`, `ours`, and `theirs` snapshots plus hunk metadata
- Treat binary conflicts as unresolved unless the user gives a file-type-specific rule.
- Commit only when there are no unresolved conflicts and validation passes.
- Do not push, update the GitHub PR, or mutate the user's original branch unless the user explicitly asks.
- When the user does explicitly ask to update the PR, apply the final resolved commit onto the PR head branch itself and push that branch, so the open PR becomes clean.

## Supported Modes

### PR vs Base

Use when one PR conflicts with its target branch.

```bash
python3 ~/.codex/skills/pr-conflict-preserver/scripts/resolve_pr_conflicts.py \
  --pr 123
```

The script reads the PR's `baseRefName` from GitHub, fetches the PR head through `origin pull/<n>/head`, creates an isolated worktree from the fetched base branch, and attempts the merge there.

### PR vs PR

Use when two PRs collide and you want to see whether the second can be applied after the first without dropping content.

```bash
python3 ~/.codex/skills/pr-conflict-preserver/scripts/resolve_pr_conflicts.py \
  --pr 123 \
  --against-pr 456
```

This simulates:

1. start from the shared or declared base branch
2. merge PR `123`
3. merge PR `456`

If PR `123` itself cannot be merged safely onto the base, the script stops before attempting PR `456`.

### Branch vs Branch

Use when the GitHub PR numbers are not the best selector but the same safety rules still apply.

```bash
python3 ~/.codex/skills/pr-conflict-preserver/scripts/resolve_pr_conflicts.py \
  --base-branch main \
  --head-branch feature/example
```

## Validation

The script always runs:

- `git diff --check`
- syntax or structure checks for recognized file types:
  - Python: `ast.parse`
  - JSON: `json.loads`
  - TOML: `tomllib.loads`
  - YAML: `yaml.safe_load` if PyYAML is installed

If unresolved conflicts remain, validation does not attempt to bless the result. If validation fails after a supposedly safe auto-merge, the script stops and reports the failure without committing.

## Artifacts

Each run writes a timestamped directory under `.codex-conflict-preserver/` inside the isolated worktree:

- `summary.json`: machine-readable outcome
- `summary.md`: concise human report
- `files/<sanitized-path>/base`
- `files/<sanitized-path>/ours`
- `files/<sanitized-path>/theirs`
- `files/<sanitized-path>/hunks.json`

Read `references/report-format.md` when you need the exact artifact semantics.

## Rules For Manual Follow-Up

When the script stops with unresolved conflicts:

1. Read `summary.md` first.
2. Open only the unresolved files listed there.
3. Compare the inline diff3 markers with the preserved sidecar artifacts.
4. Decide manually only for the specific unresolved hunks.
5. Re-run repository tests after manual edits before committing.

Do not delete the artifact directory until the resolution branch is merged or intentionally abandoned.

## Applying Back To The PR Branch

If the user asked for the open PR itself to be fixed:

1. Verify the PR head branch worktree is clean.
2. Confirm the resolution commit descends from the PR head branch tip so a fast-forward is possible.
3. Fast-forward the PR head branch to the validated resolution commit.
4. Push the PR head branch, not just the temporary resolution branch.
5. Report the PR URL, pushed branch name, and final mergeability state.

If the resolution commit cannot be fast-forwarded onto the PR head branch, stop and explain the blocker instead of rewriting history.
