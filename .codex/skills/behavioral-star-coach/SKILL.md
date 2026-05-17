---
name: behavioral-star-coach
description: Use when the user needs behavioral STAR interview answers, story banks, script rewrites, mock follow-up questions, role-specific communication coaching, or answer-quality checks for US tech interviews.
---

# Behavioral STAR Coach

## Overview

Build interview-ready STAR stories that are concise, credible, and adaptable to different behavioral prompts.

## EUNWHA-Specific Backend Scripts

When the prompt relies on EUNWHA's Samsung backend experience, IAM modernization, ClustrixDB migration evidence, `Tell me about yourself`, `Walk me through your resume`, `Why this role?`, backend ownership wording, or overclaiming risk, also use `$samsung-backend-interview-scripts`.

Keep this skill responsible for STAR structure, answer quality, length, and follow-up pressure testing. Use `$samsung-backend-interview-scripts` for evidence selection and Samsung-specific scope boundaries.

## User Script Library

When EUNWHA asks for an English interview script, use this Notion page as the canonical script library:

- Notion index: `https://www.notion.so/30b8a12184338100ba37d14940e9bb29`
- Page title: `영어면접_세션_모음`
- Existing reference pages include `Tell me about yourself`, `Walk me through your resume`, and `Why this role?`.

Default workflow for new script requests:

1. Fetch the Notion index page first.
2. Read the existing child pages that are relevant to the requested question or prompt family.
3. Match the tone, level of specificity, and defensible Samsung backend ownership boundaries from the existing scripts.
4. Create a new child page under the Notion index page for the new script unless the user explicitly asks only for chat output.
5. Include the final script, concise Korean coaching notes if useful, and likely follow-up questions.

## Pre-Draft Guardrails

Before drafting, block vague prestige or abstraction-based motivation. Do not use these phrases as standalone reasons:

- "strong system design"
- "infrastructure depth"
- "innovative company"
- "challenging problems"
- "large-scale impact"
- "intersection of product and infrastructure"
- "global impact"

These phrases may only stay if tied to all of:

1. a concrete company, product, or infrastructure area,
2. a backend responsibility,
3. a user-facing or operational outcome,
4. EUNWHA's real Samsung backend experience.

Use this rewrite pattern:

> I am interested in [backend/system work] because it improves [product, user, reliability, or operational outcome] as [company/product] scales.

Run a "So what?" test on each motivation sentence:

- Weak: "I am interested in strong system design."
- Stronger: "I am interested in backend systems where design decisions directly affect product reliability, user experience, and scalability."

If the target company, product area, or concrete challenge is missing, label the draft provisional. Do not call it final.

## Backend Answer Quality Gate

Do not treat an answer as a strong or final model answer until it passes these checks:

1. Company or role fit
- The answer connects to the target company, role, product, or infrastructure challenge.
- Avoid generic claims like "innovative company" unless tied to a concrete system or product.

2. Backend engineering signal
- Include backend judgment such as reliability, scalability, correctness, API design, data models, data access patterns, latency, consistency, backward compatibility, migration safety, or safe rollout.
- For company-specific claims, verify the product or infrastructure fact from the user's JD, company page, or current public source. If not verified, mark it as a placeholder.

3. Evidence from EUNWHA's real experience
- Ground claims in Samsung production backend experience, especially identity and access management, production reliability, large-scale data, migration, or modernization work.
- Keep the scope defensible. Prefer "backend application-side ownership", "backend APIs", "data models", "data access patterns", and "safe rollout logic".
- Avoid overclaiming ownership of database infrastructure, storage-layer internals, or broad data infrastructure unless the user provides direct evidence.

4. Ownership boundary
- The answer must survive "What exactly did you own versus your team?".
- Separate personal actions from team outcomes when needed.

5. Tradeoff and judgment
- Show at least one engineering judgment when the prompt allows it: risk reduction, staged rollout, compatibility, failure containment, correctness versus speed, latency versus consistency, or operational safety.

6. Impact
- Include measurable impact when available. If numbers are unavailable, state user impact, reliability impact, risk reduction, or operational improvement.
- Do not invent metrics.

7. Spoken clarity
- The answer should be natural to say in 30, 60, or 90 seconds.
- Prefer one fluent script over fragmented notes when the user asks for a final answer.

8. Follow-up resilience
- Add likely follow-up questions and a short answer strategy.
- Flag weak points if a follow-up would expose missing evidence, vague motivation, or overbroad claims.

9. Interviewer challenge simulation
- Test the answer against: "What do you mean by that?", "Why this company specifically?", "Can you give a concrete product or infrastructure example?", "How is this connected to your Samsung backend experience?", and "What exactly did you own?".
- If the answer cannot handle these questions, rewrite before presenting it as final.

When a draft fails any gate, label it as provisional and explain what information is missing or what should be tightened.

## Workflow

1. Build story inventory
- Collect 8-12 real experiences across leadership, conflict, failure, ambiguity, and impact.

2. Map to prompt families
- Group stories by common interview dimensions (ownership, collaboration, judgment, growth).

3. Rewrite with STAR discipline
- Situation: only necessary context.
- Task: explicit responsibility.
- Action: concrete decisions and actions.
- Result: measurable impact and learned lesson.
- Run the Pre-Draft Guardrails before writing the first polished script.

4. Stress-test with follow-ups
- Ask "what would you do differently", "how did you measure impact", and "how did you influence others".
- Tighten answers to 60-120 seconds.

5. Final coaching
- Flag vague wording, missing ownership, and weak results.
- Provide stronger, concise alternatives.
- Run the Backend Answer Quality Gate before calling the answer final.

## Output Format

1. Story Bank (tagged by theme)
2. STAR Rewrite Set
3. Follow-up Q&A Drill
4. Weak Signal Fixes
5. Final 60-120s Interview Scripts
6. Quality Gate Assessment
7. Abstract Phrase Check
8. Company-Specific Evidence Status
9. Interviewer Challenge Simulation

## References

- Prompt families and examples: `references/prompt-families.md`
