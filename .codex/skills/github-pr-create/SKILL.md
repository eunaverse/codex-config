---
name: github-pr-create
description: Create GitHub pull requests from the current git branch. Use when the user asks to open, create, draft, or prepare a PR; push a branch and make a PR; follow repository PR policy; set base/head branches; or recover when `gh` is unavailable by using GitHub API credentials from git credential helper.
---

# GitHub PR Create

## Workflow

1. Inspect repository policy before acting:
   - Read `AGENTS.md` if present.
   - Respect branch/base rules in the repo. If no policy exists, infer the base from the upstream default branch or ask only when ambiguous.
   - For repositories that state feature PRs target `develop`, always use `develop` as `--base`.

2. Check local state:
   - Run `git status --short --branch`.
   - Do not stage unrelated user changes.
   - If commits are needed, stage only files relevant to the user's request and use Conventional Commit style when the repo uses it.
   - Run required validation from repo policy before committing when feasible.

3. Push the branch:
   - Ensure the current branch is not `main`, `master`, or the PR base branch.
   - Use `git push -u origin <branch>` unless upstream already exists.
   - If network or `.git` writes are sandbox-blocked, rerun with escalation and a concise justification.

4. Create the PR:
   - Prefer `gh pr create` when `gh` is installed and authenticated.
   - If `gh` is unavailable, use `scripts/create_pr.py` from this skill.
   - Do not print access tokens or credential-helper output.

5. Report the result:
   - Provide the PR URL, base branch, head branch, commit list, and any uncommitted files left intentionally outside the PR.

## Script

Use the bundled script when `gh` is missing or when deterministic fallback behavior is useful:

```bash
python3 /Users/eunhwa/.codex/skills/github-pr-create/scripts/create_pr.py \
  --base develop \
  --head "$(git branch --show-current)" \
  --title "feat(scope): concise title" \
  --body-file /tmp/pr-body.md
```

The script:
- Detects `owner/repo` from `origin`.
- Uses `gh pr create` if available.
- Falls back to GitHub REST API using `GH_TOKEN`, `GITHUB_TOKEN`, or `git credential fill`.
- Prints only the created PR URL or a concise error.

## PR Body

Follow the repository PR template when present. If the task is tied to a real
issue, include an issue-closing line in the PR body by default, such as
`closes #59`, unless the repo explicitly uses a different linking convention.
If no issue is provided, avoid fake closing keywords such as `close #번호`; use
`관련 이슈 없음` or the repo's preferred placeholder.

Include:
- summary of user-visible or API behavior changes
- important review notes
- validation commands actually run

For Korean repo templates, keep the PR body in Korean unless the user asks otherwise.
