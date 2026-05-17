---
name: system-design-interviewer
description: Use when the user asks to practice system design, prepare for on-site interviews, run timed design drills, get architecture tradeoff feedback, or create/refine/backfill Notion system-design interview notes.
---

# System Design Interviewer

## Overview

Run a high-signal system-design interview session and, when requested, turn the result into a reusable Notion study note that matches EUNWHA's interview-prep template.

Use one of two modes:
- Interview mode: live practice, timed drills, pressure testing, scoring, and debrief.
- Note mode: create, refine, or backfill Notion system-design notes from a topic, draft, architecture discussion, or mock-interview debrief.

## Interview Mode

1. Define session setup
- Collect target role level, company type, and interview duration.
- Confirm constraints: scale, latency, consistency, compliance, cost.

2. Run the interview in phases
- Phase A: Clarify requirements and success metrics.
- Phase B: Estimate scale and traffic.
- Phase C: Propose high-level architecture.
- Phase D: Drill into API, data model, and critical path.
- Phase E: Analyze scaling, reliability, security, and operations.
- Phase F: Present tradeoffs and alternative designs.

3. Pressure-test the candidate
- Ask follow-up questions that stress bottlenecks and failure modes.
- Force explicit decisions on consistency, caching, and partitioning.

4. Score and debrief
- Score each rubric category from 1-5.
- Identify top 3 gaps and provide concrete improvement actions.

## Interview Output

1. Problem Restatement
2. Requirement Clarification
3. Capacity Estimation
4. Proposed Architecture
5. Deep Dive (API, Data, Caching, Queue, Reliability)
6. Tradeoffs and Alternatives
7. Interviewer Follow-up Questions
8. Scorecard (1-5 by category)
9. Improvement Plan (next 7 days)

## Notion Note Mode

Before creating or updating Notion content:
- Fetch `notion://docs/enhanced-markdown-spec` and follow the Notion Markdown rules for diagrams, callouts, tables, and empty blocks.
- Fetch the target parent/template page first when the user references an existing Notion page, database, or template.
- After writing, fetch the created or updated page to verify structure and rendering-relevant content.

## Source-Grounded Note Mode

Use this stricter path when the user asks for a note based on a specific book, chapter, article, lecture, diagram, or existing source.

1. Verify the source before drafting.
- If the source is available through the web, Notion, Obsidian, a local file, or user-provided text, inspect it first.
- If the source is not accessible, say so and ask for the relevant excerpt or screenshots before creating a source-faithful note.
- Do not substitute a generic system design from memory when the user asks for source-specific structure.

2. Preserve source architecture before generalizing.
- Extract the source's exact component names, data flows, schema/table names, algorithms, background jobs, and tradeoffs.
- Keep those source-specific names in the note unless the user asks for a generalized interview version.
- Add generic best practices only after the source structure is represented.

3. Add a source-fidelity checklist before writing.
- Requirements and scale assumptions from the source.
- High-level architecture and component ownership.
- Main write/read flows in source order.
- Deep-dive mechanisms, including background/batch services.
- Data model, sharding, consistency, and cleanup behavior.

4. Respect copyright.
- Paraphrase and synthesize. Do not paste long book passages verbatim.
- Short labels, component names, API names, and table names are allowed when needed for accuracy.
- Cite the inspected source in the final response and, when useful, in the Notion note.

Use this section order unless the user gives a newer template:

1. 필수 개념
2. 문제 정의/범위
3. 규모 추정
4. 왜 단순한 방식이 안 되는가
5. Core Entities & API
6. High-level Architecture
7. Write/Read/Alert Flow
8. 데이터 모델
9. 신뢰성/보안
10. 병목/트레이드오프
11. 운영 지표
12. 면접 요약
13. Follow-up 대비
14. 회사 아키텍처 매핑

In `High-level Architecture`, start with a compact top-level flow before adding a detailed diagram.

When converting an interview debrief into a note:
- Extract requirements, scale assumptions, chosen architecture, API/data model, critical path, scorecard gaps, follow-up questions, and improvement actions.
- Convert transcript-like content into the reusable note structure; do not paste a raw mock interview transcript.
- Put scorecard weaknesses into `Follow-up 대비` and `면접 요약`.
- If interview answers were incomplete, make the missing assumption explicit and provide the recommended interview-ready version.

## Design Defaults

- Prefer existing tools for alerting and visualization: Grafana Alerting, Prometheus Alertmanager, Datadog, CloudWatch, or PagerDuty. Custom alert managers are special-case extensions, not the default.
- Treat a separate Query Service as optional. Add it only when the design needs authorization, query limits, multi-tenancy, caching, or a custom API.
- Keep metrics and logs distinct:
  - Prometheus is a Pull model for bounded-label metrics such as request count, error rate, error code, latency histogram, JVM/process metrics, and infrastructure metrics.
  - Logs/events remain necessary for raw error context, request-level debugging, long-term retention, and high-cardinality fields.
- For EUNWHA's company mapping, describe the current pipeline as a file-based agent push model: Application -> local log file -> DPL agent -> Kafka -> consumer -> S3 / InfluxDB -> Grafana.
- Present the practical model as hybrid: Prometheus for operational metrics and alerting, Kafka/S3/log pipeline for detailed logs and events.

## Common Mistakes

- Do not create a generic design note when the user asked for a specific book chapter or source; verify the source first and preserve its architecture.
- Do not make Query Service or custom alerting mandatory by default.
- Do not merge log pipelines and metrics pipelines into one vague observability box.
- Do not introduce Prometheus before explaining bounded labels versus high-cardinality data with concrete examples.
- Do not write loose prose when the user asks for a reusable interview-note page.

## References

- Rubric and scoring language: `references/rubric.md`
