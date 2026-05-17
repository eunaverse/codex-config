---
name: slack-notification-workspace-harness
description: Use when working in `/Users/eunhwa/projects` on private Slack notification apps, including prep-alerts, job-alerts, ai-news-alerts, uiuc-funding-alerts, GitHub Actions, dry-runs, seen-state files, or workspace agent instructions.
---

# Slack Notification Workspace Harness

## Workflow

1. Read `/Users/eunhwa/projects/Agents.md`.
2. Read `/Users/eunhwa/projects/docs/agent-workflow/projects.md` for the
   touched subproject's current runtime facts and commands.
3. For implementation, workflow, scheduler, collector, state, or docs changes,
   follow `/Users/eunhwa/projects/docs/agent-workflow/harness-engineering.md`.
4. For commits, pushes, PRs, CI monitoring, or GitHub review comments, read
   `/Users/eunhwa/projects/docs/agent-workflow/github-workflow.md`.
5. Before final handoff, use the fresh subagent review loop and the lenses in
   `/Users/eunhwa/projects/docs/agent-workflow/review-lenses.md`.

## Guardrails

- Default to Korean unless the user asks otherwise.
- Start from current files in the relevant subproject.
- Keep manual runs harmless: dry-runs and previews must not mutate production
  state or post unexpectedly.
- Never print or commit Slack webhooks, OAuth credentials, API tokens, refresh
  tokens, `.env` values, or private user data.
- Do not change alert cadence, schedule dates, target roles, or source strategy
  unless explicitly requested.
- Use Slack `mrkdwn` links: `<url|label>`.
- Check each subproject separately with `git -C <project> status --short`.
- Treat `job-alerts-local-copy` and similar scratch directories as
  non-authoritative unless explicitly named.

## Completion Gate

Run the relevant verification first, then spawn a fresh reviewer. Fix every
actionable finding, rerun verification, and use a new reviewer until the newest
review reports no actionable findings.
