# Codex Config

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
