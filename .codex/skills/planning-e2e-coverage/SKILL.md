---
name: planning-e2e-coverage
description: Use when planning or tightening end-to-end coverage for a product, feature, or web flow; when Playwright or browser-level tests are too shallow; or when Codex should generate a project-specific E2E checklist, propose test buckets, and strengthen plans with interaction, failure-state, responsive, and visual-stability coverage.
---

# Planning E2E Coverage

## Overview

Produce project-aware E2E coverage that checks how the product actually behaves, not just whether routes load. Generate a reusable checklist document, propose a maintainable `tests/e2e` structure, and strengthen any implementation plan with button-level, state-level, responsive, and visual-stability expectations.

## Workflow

1. Inspect project context before writing anything.
2. Identify the main user journeys and key screens.
3. Break each critical screen into interactions, states, and layout risks.
4. Choose responsive checkpoints that match the product.
5. Write the checklist document and propose test buckets.
6. If a plan document exists, strengthen its E2E coverage.

## Project Context Pass

Read only the artifacts needed to ground the checklist:

- product spec or feature notes
- implementation plan if one exists
- app routes, major screens, or page components
- existing `tests/e2e` structure
- package scripts or current E2E runner setup

Do not write a generic checklist before inspecting the project.

## Coverage Rules

Always enforce these rules:

- Do not treat route-load checks as sufficient E2E coverage.
- Identify the primary CTA on each critical screen and the important secondary actions.
- Cover state changes, not just clicks. At minimum consider `success`, `error`, `loading`, `empty`, and `populated` when relevant.
- Include responsive checks for small, medium, and large viewports chosen from project context.
- Include visual-stability checks such as overflow, clipping, overlap, hidden CTAs, awkward wrapping, and broken scroll behavior.
- Keep the checklist product-facing and the test bucket proposal engineering-facing.

If the project is not a browser UI, do not force Playwright-specific structure. Adapt the output to the actual browser-level test stack in use.

## Outputs

Generate these outputs by default:

1. A checklist document under the project's docs area such as:
   `docs/.../<date>-<feature>-e2e-checklist.md`
2. A proposed `tests/e2e` bucket structure based on user journeys and risk areas
3. E2E coverage additions for any existing implementation plan that is missing interaction, state, responsive, or visual-review expectations

Only generate actual spec files when the user asks for them or when a local workflow explicitly benefits from immediate scaffolding.

## Responsive Guidance

Pick viewports from product context instead of hard-coding a single trio for every app.

Good defaults for a web product:

- small mobile
- tablet or narrow laptop
- desktop

Prefer product-relevant sizes when the app clearly targets a narrower set of devices.

## Manual Review Expectations

Automated assertions are not enough for UI-heavy work. For milestone or release-level checks, recommend screenshot capture and manual review of the most important screens for:

- text clipping
- overlapping cards or panels
- hidden or off-screen CTAs
- unstable spacing at smaller widths
- decorative layers obscuring content

## Reference File

For checklist section prompts, test-bucket patterns, and adaptable viewport guidance, read:

- `references/e2e-checklist-template.md`
