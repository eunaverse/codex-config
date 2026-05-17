---
name: job-hunt-orchestrator
description: Orchestrate US software job preparation across resume tailoring, coding interview prep, system design mocks, and behavioral STAR coaching. Use when the user wants one integrated plan instead of running those skills separately, especially for weekly execution and interview readiness tracking.
---

# Job Hunt Orchestrator

## Overview

Run a single operating workflow that coordinates four skills for US hiring outcomes:
- `$jd-resume-tailor`
- `$leetcode-coach-us`
- `$system-design-interviewer`
- `$behavioral-star-coach`

## Workflow

1. Intake and constraints
- Capture target timeline, role level, visa constraints (if shared), location preference, and weekly hours.
- Capture current baseline: resume quality, coding speed, design confidence, behavioral readiness.

2. Weekly operating loop
- Resume lane: Use `$jd-resume-tailor` for 2-5 target JDs.
- Coding lane: Use `$leetcode-coach-us` for daily plan + postmortem loop.
- System design lane: Use `$system-design-interviewer` for 2 mock sessions per week.
- Behavioral lane: Use `$behavioral-star-coach` to maintain 8-12 strong STAR stories.

3. Priority policy
- If interviews are within 14 days: prioritize mock interviews and STAR polishing.
- If interview pipeline is weak: prioritize JD-tailored applications and resume iteration.
- If OA/technical screens are failing: prioritize coding and design remediation first.

4. Tracking and adaptation
- Track weekly KPIs:
  - Applications submitted
  - Resume-to-screen conversion
  - OA pass rate
  - System design mock score
  - Behavioral answer score
- Reallocate weekly effort to the weakest KPI.

5. Output a single execution plan
- Produce one consolidated plan with owners (you), deadlines, and measurable targets.

## Output Format

1. Candidate Snapshot
2. This Week Priorities (Top 3)
3. Integrated Plan by Lane (Resume / Coding / Design / Behavioral)
4. Daily Schedule (Mon-Sun)
5. KPI Targets and Checkpoints
6. Risks and Mitigations
7. Next Review Date (`YYYY-MM-DD`)

## References

- Weekly template and KPI definitions: `references/weekly-template.md`
