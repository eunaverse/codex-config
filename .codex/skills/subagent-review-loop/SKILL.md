---
name: subagent-review-loop
description: Require a fresh subagent review loop before final handoff. Use when Codex has completed a code, configuration, documentation, or skill change and needs independent review; when the user asks for subagent review; or when local instructions require review cycles until no actionable findings remain.
---

# Subagent Review Loop

## Overview

Use this skill to gate completed work on independent review. Each review pass
must use a newly spawned subagent, and the loop continues until the newest
reviewer reports no actionable findings.

## Workflow

1. Finish the local change and run relevant verification first.
2. Spawn a new subagent for review. Never reuse an existing or previous reviewer
   session.
3. Give the reviewer only the task-local context needed to inspect the work:
   changed files, requirements, relevant commands, and any test output.
4. Ask for findings first, ordered by severity, with concrete file and line
   references where possible.
5. If the reviewer reports actionable findings, fix them locally.
6. Rerun the relevant verification for the affected area.
7. Spawn another new subagent for the next review pass.
8. Repeat until the newest reviewer reports no actionable findings.
9. In the final handoff, state the verification command and that the final fresh
   subagent review had no actionable findings.

## Reviewer Prompt Template

Use a prompt like this for each pass:

```text
Review the completed change for actionable issues.

Requirements:
- <summarize the user request>
- <summarize important local instructions>

Changed files:
- <path>

Verification:
- <commands run and results>

Please inspect the current files or diff and report findings first, ordered by
severity. Include file and line references for each actionable issue. If there
are no actionable findings, say that clearly. Do not edit files.
```

## Handling Findings

- Fix every actionable finding before final handoff, regardless of severity.
- Treat severity labels as ordering signals only; they do not change the stop
  condition.
- If a reviewer is wrong, explain the technical reason and cite the file,
  command output, or requirement that proves it.
- After any local fix, do not ask the same reviewer to re-check. Spawn a new
  subagent for the next pass.

## Stop Condition

Stop only when the newest fresh subagent review reports no actionable findings.
